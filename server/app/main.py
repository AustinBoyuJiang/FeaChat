import re
import uuid
from pathlib import Path

from fastapi import Depends, FastAPI, File, Header, HTTPException, Query, UploadFile, WebSocket, WebSocketDisconnect, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from .config import settings
from .db import db
from .schemas import (
    AccountUpdate,
    FriendProfileUpdate,
    FriendRequestCreate,
    GroupAliasUpdate,
    GroupCreate,
    GroupInviteCreate,
    GroupUpdate,
    LoginRequest,
    MessageCreate,
    RegisterRequest,
)
from .services import (
    accept_friend_request,
    answer_group_invite,
    conversation_members,
    create_group,
    create_group_invites,
    create_friend_request,
    delete_friend,
    list_friend_request_history,
    list_friend_requests,
    list_friends,
    list_conversation_messages,
    list_conversations,
    list_group_invites,
    list_messages,
    login_user,
    register_user,
    reject_friend_request,
    require_conversation_member,
    require_user,
    save_attachment_message,
    save_conversation_attachment_message,
    save_conversation_message,
    save_message,
    search_users,
    sessions,
    remove_group_member,
    update_group,
    update_group_alias,
    update_friend_profile,
    update_account,
    update_account_avatar,
)
from .websocket_manager import manager


app = FastAPI(title="FeaChat API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.cors_origins),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def safe_filename(name: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._ -]+", "_", Path(name or "file").name).strip()
    return cleaned[:160] or "file"


async def persist_upload(file: UploadFile) -> tuple[str, str, str, int]:
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    original_name = safe_filename(file.filename or "file")
    suffix = Path(original_name).suffix[:16]
    stored_name = f"{uuid.uuid4().hex}{suffix}"
    target = settings.upload_dir / stored_name
    size = 0

    try:
        with target.open("wb") as output:
            while chunk := await file.read(1024 * 1024):
                size += len(chunk)
                if size > settings.max_upload_bytes:
                    raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, "File is too large")
                output.write(chunk)
    except Exception:
        target.unlink(missing_ok=True)
        raise
    finally:
        await file.close()

    if size == 0:
        target.unlink(missing_ok=True)
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "File is empty")

    return original_name, stored_name, file.content_type or "application/octet-stream", size


def current_user(authorization: str | None = Header(default=None)) -> str:
    token = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization.removeprefix("Bearer ").strip()
    number = sessions.resolve(token)
    if number is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not authenticated")
    return number


@app.get("/api/health")
def health():
    return {"ok": True}


@app.post("/api/auth/register")
def register(payload: RegisterRequest):
    user = register_user(db, payload.number, payload.password, payload.email, payload.nickname)
    return {"user": user}


@app.post("/api/auth/login")
def login(payload: LoginRequest):
    return login_user(db, payload.number, payload.password)


@app.get("/api/me")
def me(number: str = Depends(current_user)):
    from .services import public_user

    return {"user": public_user(require_user(db, number))}


@app.patch("/api/me")
def edit_me(payload: AccountUpdate, number: str = Depends(current_user)):
    return update_account(db, number, payload.nickname, payload.current_password, payload.new_password)


@app.post("/api/me/avatar")
async def edit_my_avatar(file: UploadFile = File(...), number: str = Depends(current_user)):
    if not (file.content_type or "").startswith("image/"):
        await file.close()
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Avatar must be an image")
    original_name, stored_name, mime_type, size = await persist_upload(file)
    try:
        return update_account_avatar(db, number, stored_name, mime_type)
    except Exception:
        (settings.upload_dir / stored_name).unlink(missing_ok=True)
        raise


@app.get("/api/users/search")
def users_search(q: str = Query(default=""), number: str = Depends(current_user)):
    return {"users": search_users(db, number, q)}


@app.get("/api/friends")
def friends(number: str = Depends(current_user)):
    return {"friends": list_friends(db, number)}


@app.post("/api/friends/requests")
def friend_request(payload: FriendRequestCreate, number: str = Depends(current_user)):
    return create_friend_request(db, number, payload.receiver)


@app.get("/api/friends/requests")
def friend_requests(number: str = Depends(current_user)):
    return {"requests": list_friend_requests(db, number)}


@app.get("/api/friends/requests/history")
def friend_request_history(number: str = Depends(current_user)):
    return {"requests": list_friend_request_history(db, number)}


@app.post("/api/friends/requests/{requester}/accept")
def accept_request(requester: str, number: str = Depends(current_user)):
    return accept_friend_request(db, number, requester)


@app.post("/api/friends/requests/{requester}/reject")
def reject_request(requester: str, number: str = Depends(current_user)):
    return reject_friend_request(db, number, requester)


@app.delete("/api/friends/{friend}")
def remove_friend(friend: str, number: str = Depends(current_user)):
    return delete_friend(db, number, friend)


@app.patch("/api/friends/{friend}")
def edit_friend_profile(friend: str, payload: FriendProfileUpdate, number: str = Depends(current_user)):
    return update_friend_profile(db, number, friend, payload.alias, payload.tags)


@app.get("/api/conversations")
def conversations(number: str = Depends(current_user)):
    return {"conversations": list_conversations(db, number)}


@app.post("/api/groups")
async def create_group_chat(payload: GroupCreate, number: str = Depends(current_user)):
    result = create_group(db, number, payload.title, payload.members)
    for message in result.get("messages", []):
        await manager.broadcast_message(message)
    return result


@app.get("/api/groups/invites")
def group_invites(number: str = Depends(current_user)):
    return {"invites": list_group_invites(db, number)}


@app.post("/api/groups/invites/{invite_id}/accept")
def accept_group_invite(invite_id: int, number: str = Depends(current_user)):
    return answer_group_invite(db, number, invite_id, True)


@app.post("/api/groups/invites/{invite_id}/reject")
def reject_group_invite(invite_id: int, number: str = Depends(current_user)):
    return answer_group_invite(db, number, invite_id, False)


@app.post("/api/conversations/{conversation_id}/invites")
async def invite_to_group(conversation_id: str, payload: GroupInviteCreate, number: str = Depends(current_user)):
    result = create_group_invites(db, number, conversation_id, payload.invitees)
    for message in result.get("messages", []):
        await manager.broadcast_message(message)
    return result


@app.patch("/api/conversations/{conversation_id}")
def edit_group(conversation_id: str, payload: GroupUpdate, number: str = Depends(current_user)):
    return update_group(db, number, conversation_id, payload.title)


@app.patch("/api/conversations/{conversation_id}/me")
def edit_group_alias(conversation_id: str, payload: GroupAliasUpdate, number: str = Depends(current_user)):
    return update_group_alias(db, number, conversation_id, payload.alias)


@app.delete("/api/conversations/{conversation_id}/members/{member}")
def kick_group_member(conversation_id: str, member: str, number: str = Depends(current_user)):
    return remove_group_member(db, number, conversation_id, member)


@app.get("/api/conversations/by-id/{conversation_id}/messages")
def conversation_messages_by_id(conversation_id: str, limit: int = Query(default=80), number: str = Depends(current_user)):
    return {"messages": list_conversation_messages(db, number, conversation_id, limit)}


@app.post("/api/conversations/by-id/{conversation_id}/messages")
async def create_conversation_message(conversation_id: str, payload: MessageCreate, number: str = Depends(current_user)):
    message = save_conversation_message(db, number, conversation_id, payload.message_type, payload.body)
    recipients = [member["number"] for member in conversation_members(db, conversation_id)]
    await manager.broadcast_message(message, recipients=recipients)
    return {"message": message}


@app.post("/api/conversations/by-id/{conversation_id}/attachments")
async def create_conversation_attachment(conversation_id: str, file: UploadFile = File(...), number: str = Depends(current_user)):
    original_name, stored_name, mime_type, size = await persist_upload(file)
    try:
        message = save_conversation_attachment_message(db, number, conversation_id, original_name, stored_name, mime_type, size)
    except Exception:
        (settings.upload_dir / stored_name).unlink(missing_ok=True)
        raise
    recipients = [member["number"] for member in conversation_members(db, conversation_id)]
    await manager.broadcast_message(message, recipients=recipients)
    return {"message": message}


@app.get("/api/conversations/{peer}/messages")
def conversation_messages(peer: str, limit: int = Query(default=80), number: str = Depends(current_user)):
    return {"messages": list_messages(db, number, peer, limit)}


@app.post("/api/conversations/{peer}/messages")
async def create_message(peer: str, payload: MessageCreate, number: str = Depends(current_user)):
    message = save_message(db, number, peer, payload.message_type, payload.body)
    await manager.broadcast_message(message)
    return {"message": message}


@app.post("/api/conversations/{peer}/attachments")
async def create_attachment(peer: str, file: UploadFile = File(...), number: str = Depends(current_user)):
    original_name, stored_name, mime_type, size = await persist_upload(file)
    try:
        message = save_attachment_message(db, number, peer, original_name, stored_name, mime_type, size)
    except Exception:
        (settings.upload_dir / stored_name).unlink(missing_ok=True)
        raise
    await manager.broadcast_message(message)
    return {"message": message}


@app.get("/api/files/{stored_name}")
def download_file(stored_name: str, download: bool = Query(default=False)):
    if "/" in stored_name or "\\" in stored_name:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "File not found")
    row = db.fetchone(
        "SELECT original_name, mime_type FROM attachments WHERE stored_name = ?",
        stored_name,
    )
    path = settings.upload_dir / stored_name
    if row is None or not path.exists():
        raise HTTPException(status.HTTP_404_NOT_FOUND, "File not found")
    if download:
        return FileResponse(path, media_type=row["mime_type"], filename=row["original_name"])
    return FileResponse(path, media_type=row["mime_type"])


@app.get("/api/avatars/{stored_name}")
def download_avatar(stored_name: str):
    if "/" in stored_name or "\\" in stored_name:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Avatar not found")
    row = db.fetchone(
        "SELECT avatar_mime_type FROM users WHERE avatar_file = ?",
        stored_name,
    )
    path = settings.upload_dir / stored_name
    if row is None or not path.exists():
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Avatar not found")
    return FileResponse(path, media_type=row["avatar_mime_type"] or "image/png")


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str | None = Query(default=None)):
    number = sessions.resolve(token)
    if number is None:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    await manager.connect(number, websocket)
    try:
        while True:
            payload = await websocket.receive_json()
            if payload.get("type") == "send_message":
                body = str(payload.get("body", "")).strip()
                receiver = str(payload.get("receiver", "")).strip()
                conversation_id = str(payload.get("conversation_id", "")).strip()
                if not body or not (receiver or conversation_id):
                    await websocket.send_json({"type": "error", "message": "Missing receiver/conversation or body"})
                    continue
                if conversation_id:
                    message = save_conversation_message(db, number, conversation_id, payload.get("message_type", "text"), body)
                    recipients = [member["number"] for member in conversation_members(db, conversation_id)]
                    await manager.broadcast_message(message, recipients=recipients)
                else:
                    message = save_message(db, number, receiver, payload.get("message_type", "text"), body)
                    await manager.broadcast_message(message)
            elif payload.get("type") == "call_signal":
                receiver = str(payload.get("receiver", "")).strip()
                conversation_id = str(payload.get("conversation_id", "")).strip()
                signal = payload.get("signal")
                if not (receiver or conversation_id) or not isinstance(signal, dict):
                    await websocket.send_json({"type": "error", "message": "Missing call receiver or signal"})
                    continue
                if conversation_id:
                    require_conversation_member(db, conversation_id, number)
                    recipients = [member["number"] for member in conversation_members(db, conversation_id) if member["number"] != number]
                    for recipient in recipients:
                        await manager.send_to_user(
                            recipient,
                            {
                                "type": "call_signal",
                                "sender": number,
                                "conversation_id": conversation_id,
                                "signal": signal,
                            },
                        )
                    continue
                await manager.send_to_user(
                    receiver,
                    {
                        "type": "call_signal",
                        "sender": number,
                        "signal": signal,
                    },
                )
            elif payload.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
            else:
                await websocket.send_json({"type": "error", "message": "Unknown websocket event"})
    except WebSocketDisconnect:
        manager.disconnect(number, websocket)
