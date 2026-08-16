import secrets
import sqlite3
import json
import uuid

from fastapi import HTTPException, status

from server.security import hash_password, verify_password

from .db import Database


class SessionStore:
    def __init__(self):
        self._token_to_number: dict[str, str] = {}

    def create(self, number: str) -> str:
        token = secrets.token_urlsafe(32)
        self._token_to_number[token] = number
        return token

    def resolve(self, token: str | None) -> str | None:
        if not token:
            return None
        return self._token_to_number.get(token)

    def clear(self):
        self._token_to_number.clear()


sessions = SessionStore()


def generate_avatar_color() -> str:
    return f"hsl({secrets.randbelow(360)} 72% 46%)"


def public_user(row) -> dict:
    return {
        "number": row["number"],
        "nickname": row["nickname"] or row["number"],
        "avatar": row["avatar"],
        "avatar_url": f"/api/avatars/{row['avatar_file']}" if row["avatar_file"] else None,
        "avatar_color": row["avatar_color"] or "#0076f6",
        "background": row["background"],
        "gender": row["gender"] or "unknown",
        "motto": row["motto"] or "",
    }


def friend_user(row) -> dict:
    user = public_user(row)
    alias = (row["alias"] or "").strip()
    try:
        tags = json.loads(row["tags"] or "[]")
    except json.JSONDecodeError:
        tags = []
    user["alias"] = alias
    user["tags"] = [str(tag) for tag in tags if str(tag).strip()]
    user["display_name"] = alias or user["nickname"]
    return user


def direct_conversation_id(user_a: str, user_b: str) -> str:
    first, second = sorted([user_a, user_b])
    return f"dm:{first}:{second}"


def ensure_direct_conversation(database: Database, user_a: str, user_b: str) -> str:
    conversation_id = direct_conversation_id(user_a, user_b)
    database.execute(
        """
        INSERT OR IGNORE INTO conversations(id, type, title, owner)
        VALUES (?, 'direct', '', NULL)
        """,
        conversation_id,
    )
    for number in (user_a, user_b):
        database.execute(
            """
            INSERT OR IGNORE INTO conversation_members(conversation_id, user_number, role, status)
            VALUES (?, ?, 'member', 'active')
            """,
            conversation_id,
            number,
        )
    return conversation_id


def normalize_tags(tags: list[str] | None) -> str:
    if not tags:
        return "[]"
    normalized: list[str] = []
    seen = set()
    for tag in tags:
        value = str(tag).strip()
        if not value:
            continue
        value = value[:24]
        key = value.lower()
        if key not in seen:
            seen.add(key)
            normalized.append(value)
        if len(normalized) >= 12:
            break
    return json.dumps(normalized, ensure_ascii=False)


def require_user(database: Database, number: str):
    row = database.fetchone(
        "SELECT number, nickname, avatar, avatar_file, avatar_mime_type, avatar_color, background, gender, motto FROM users WHERE number = ?",
        number,
    )
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    return row


def register_user(database: Database, number: str, password: str, email: str, nickname: str | None):
    try:
        database.execute(
            """
            INSERT INTO users(number, password_hash, email, nickname, avatar_color)
            VALUES (?, ?, ?, ?, ?)
            """,
            number,
            hash_password(password),
            email,
            nickname or number,
            generate_avatar_color(),
        )
    except sqlite3.IntegrityError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, "Number or email already exists") from exc
    return public_user(require_user(database, number))


def login_user(database: Database, number: str, password: str):
    row = database.fetchone(
        "SELECT number, password_hash, nickname, avatar, avatar_file, avatar_mime_type, avatar_color, background, gender, motto FROM users WHERE number = ?",
        number,
    )
    if row is None or not verify_password(password, row["password_hash"]):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid number or password")
    token = sessions.create(number)
    return {"token": token, "user": public_user(row)}


def update_account(database: Database, current_user: str, nickname: str | None, current_password: str | None, new_password: str | None):
    row = database.fetchone(
        "SELECT number, password_hash FROM users WHERE number = ?",
        current_user,
    )
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    updates = []
    params = []
    if nickname is not None:
        updates.append("nickname = ?")
        params.append(nickname.strip()[:48])
    if new_password is not None:
        if not current_password or not verify_password(current_password, row["password_hash"]):
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Current password is incorrect")
        updates.append("password_hash = ?")
        params.append(hash_password(new_password))
    if updates:
        updates.append("updated_at = CURRENT_TIMESTAMP")
        params.append(current_user)
        database.execute(
            f"UPDATE users SET {', '.join(updates)} WHERE number = ?",
            *params,
        )
    return {"user": public_user(require_user(database, current_user))}


def update_account_avatar(database: Database, current_user: str, stored_name: str, mime_type: str):
    if not mime_type.startswith("image/"):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Avatar must be an image")
    require_user(database, current_user)
    database.execute(
        """
        UPDATE users
        SET avatar_file = ?, avatar_mime_type = ?, updated_at = CURRENT_TIMESTAMP
        WHERE number = ?
        """,
        stored_name,
        mime_type,
        current_user,
    )
    return {"user": public_user(require_user(database, current_user))}


def search_users(database: Database, current_user: str, query: str):
    like = f"%{query.strip()}%"
    if not query.strip():
        return []
    rows = database.fetchall(
        """
        SELECT number, nickname, avatar, avatar_file, avatar_mime_type, avatar_color, background, gender, motto
        FROM users
        WHERE number <> ? AND (number LIKE ? OR nickname LIKE ?)
        ORDER BY number
        LIMIT 30
        """,
        current_user,
        like,
        like,
    )
    return [public_user(row) for row in rows]


def list_friends(database: Database, current_user: str):
    rows = database.fetchall(
        """
        SELECT u.number, u.nickname, u.avatar, u.avatar_file, u.avatar_mime_type, u.avatar_color, u.background, u.gender, u.motto, f.alias, f.tags
        FROM friendships f
        JOIN users u ON u.number = f.friend
        WHERE f.owner = ?
        ORDER BY lower(CASE WHEN f.alias <> '' THEN f.alias ELSE u.nickname END), u.number
        """,
        current_user,
    )
    return [friend_user(row) for row in rows]


def create_friend_request(database: Database, requester: str, receiver: str):
    if requester == receiver:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Cannot add yourself")
    require_user(database, receiver)
    existing_friend = database.fetchone(
        "SELECT 1 FROM friendships WHERE owner = ? AND friend = ?",
        requester,
        receiver,
    )
    if existing_friend:
        raise HTTPException(status.HTTP_409_CONFLICT, "Already friends")
    reciprocal = database.fetchone(
        """
        SELECT id FROM friend_requests
        WHERE requester = ? AND receiver = ? AND status = 'pending'
        """,
        receiver,
        requester,
    )
    if reciprocal:
        return accept_friend_request(database, requester, receiver)
    try:
        database.execute(
            """
            INSERT INTO friend_requests(requester, receiver, status)
            VALUES (?, ?, 'pending')
            ON CONFLICT(requester, receiver)
            DO UPDATE SET status = 'pending', updated_at = CURRENT_TIMESTAMP
            """,
            requester,
            receiver,
        )
    except sqlite3.IntegrityError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid friend request") from exc
    return {"status": "pending", "requester": requester, "receiver": receiver}


def list_friend_requests(database: Database, current_user: str):
    rows = database.fetchall(
        """
        SELECT u.number, u.nickname, u.avatar, u.avatar_file, u.avatar_mime_type, u.avatar_color, u.background, u.gender, u.motto, fr.created_at
        FROM friend_requests fr
        JOIN users u ON u.number = fr.requester
        WHERE fr.receiver = ? AND fr.status = 'pending'
        ORDER BY fr.created_at DESC
        """,
        current_user,
    )
    return [{**public_user(row), "created_at": utc_timestamp(row["created_at"])} for row in rows]


def list_friend_request_history(database: Database, current_user: str):
    rows = database.fetchall(
        """
        SELECT
            fr.requester,
            fr.receiver,
            fr.status,
            fr.created_at,
            fr.updated_at,
            u.number,
            u.nickname,
            u.avatar,
            u.avatar_file,
            u.avatar_mime_type,
            u.avatar_color,
            u.background,
            u.gender,
            u.motto
        FROM friend_requests fr
        JOIN users u ON u.number = CASE
            WHEN fr.requester = ? THEN fr.receiver
            ELSE fr.requester
        END
        WHERE fr.requester = ? OR fr.receiver = ?
        ORDER BY fr.updated_at DESC, fr.created_at DESC
        LIMIT 80
        """,
        current_user,
        current_user,
        current_user,
    )
    return [
        {
            **public_user(row),
            "requester": row["requester"],
            "receiver": row["receiver"],
            "direction": "incoming" if row["receiver"] == current_user else "outgoing",
            "status": row["status"],
            "created_at": utc_timestamp(row["created_at"]),
            "updated_at": utc_timestamp(row["updated_at"]),
        }
        for row in rows
    ]


def accept_friend_request(database: Database, current_user: str, requester: str):
    row = database.fetchone(
        """
        SELECT id FROM friend_requests
        WHERE requester = ? AND receiver = ? AND status = 'pending'
        """,
        requester,
        current_user,
    )
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Friend request not found")
    database.execute(
        """
        UPDATE friend_requests
        SET status = 'accepted', updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        row["id"],
    )
    database.execute("INSERT OR IGNORE INTO friendships(owner, friend) VALUES (?, ?)", current_user, requester)
    database.execute("INSERT OR IGNORE INTO friendships(owner, friend) VALUES (?, ?)", requester, current_user)
    return {"status": "accepted", "friend": requester}


def reject_friend_request(database: Database, current_user: str, requester: str):
    database.execute(
        """
        UPDATE friend_requests
        SET status = 'rejected', updated_at = CURRENT_TIMESTAMP
        WHERE requester = ? AND receiver = ? AND status = 'pending'
        """,
        requester,
        current_user,
    )
    return {"status": "rejected", "requester": requester}


def delete_friend(database: Database, current_user: str, friend: str):
    database.execute(
        "DELETE FROM friendships WHERE (owner = ? AND friend = ?) OR (owner = ? AND friend = ?)",
        current_user,
        friend,
        friend,
        current_user,
    )
    return {"status": "deleted", "friend": friend}


def member_row(database: Database, conversation_id: str, user_number: str):
    return database.fetchone(
        """
        SELECT c.id, c.type, c.title, c.owner, cm.role, cm.alias, cm.status
        FROM conversations c
        JOIN conversation_members cm ON cm.conversation_id = c.id
        WHERE c.id = ? AND cm.user_number = ? AND cm.status = 'active'
        """,
        conversation_id,
        user_number,
    )


def require_conversation_member(database: Database, conversation_id: str, user_number: str):
    row = member_row(database, conversation_id, user_number)
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Conversation not found")
    return row


def require_group_owner(database: Database, conversation_id: str, user_number: str):
    row = require_conversation_member(database, conversation_id, user_number)
    if row["type"] != "group":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Not a group conversation")
    if row["owner"] != user_number:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Only group owner can do this")
    return row


def conversation_members(database: Database, conversation_id: str):
    rows = database.fetchall(
        """
        SELECT u.number, u.nickname, u.avatar, u.avatar_file, u.avatar_mime_type, u.avatar_color, u.background, u.gender, u.motto, cm.role, cm.alias
        FROM conversation_members cm
        JOIN users u ON u.number = cm.user_number
        WHERE cm.conversation_id = ? AND cm.status = 'active'
        ORDER BY CASE WHEN cm.role = 'owner' THEN 0 ELSE 1 END, lower(u.nickname), u.number
        """,
        conversation_id,
    )
    members = []
    for row in rows:
        user = public_user(row)
        user["role"] = row["role"]
        user["group_alias"] = row["alias"] or ""
        members.append(user)
    return members


def last_message_for_conversation(database: Database, conversation_id: str, current_user: str, peer: str | None = None):
    if peer:
        row = database.fetchone(
            """
            SELECT
                m.id,
                m.conversation_id,
                m.sender,
                m.receiver,
                m.time,
                m.type,
                m.message,
                a.original_name AS file_name,
                CASE
                    WHEN a.stored_name IS NULL THEN NULL
                    ELSE '/api/files/' || a.stored_name
                END AS file_url,
                a.mime_type,
                a.size AS file_size
            FROM messages m
            LEFT JOIN attachments a ON a.message_id = m.id
            WHERE m.conversation_id = ?
               OR ((m.sender = ? AND m.receiver = ?) OR (m.sender = ? AND m.receiver = ?))
            ORDER BY m.id DESC
            LIMIT 1
            """,
            conversation_id,
            current_user,
            peer,
            peer,
            current_user,
        )
    else:
        row = database.fetchone(
            """
            SELECT
                m.id,
                m.conversation_id,
                m.sender,
                m.receiver,
                m.time,
                m.type,
                m.message,
                a.original_name AS file_name,
                CASE
                    WHEN a.stored_name IS NULL THEN NULL
                    ELSE '/api/files/' || a.stored_name
                END AS file_url,
                a.mime_type,
                a.size AS file_size
            FROM messages m
            LEFT JOIN attachments a ON a.message_id = m.id
            WHERE m.conversation_id = ?
            ORDER BY m.id DESC
            LIMIT 1
            """,
            conversation_id,
        )
    return message_from_row(row) if row else None


def list_conversations(database: Database, current_user: str):
    direct_items = []
    for friend in list_friends(database, current_user):
        conversation_id = ensure_direct_conversation(database, current_user, friend["number"])
        direct_items.append(
            {
                "id": conversation_id,
                "type": "direct",
                "title": friend.get("display_name") or friend["nickname"],
                "peer": friend,
                "members": [friend],
                "owner": None,
                "my_alias": "",
                "last_message": last_message_for_conversation(database, conversation_id, current_user, friend["number"]),
            }
        )

    group_rows = database.fetchall(
        """
        SELECT c.id, c.type, c.title, c.owner, c.updated_at, cm.alias
        FROM conversations c
        JOIN conversation_members cm ON cm.conversation_id = c.id
        WHERE c.type = 'group' AND cm.user_number = ? AND cm.status = 'active'
        ORDER BY c.updated_at DESC, c.created_at DESC
        """,
        current_user,
    )
    group_items = [
        {
            "id": row["id"],
            "type": "group",
            "title": row["title"],
            "peer": None,
            "members": conversation_members(database, row["id"]),
            "owner": row["owner"],
            "my_alias": row["alias"] or "",
            "last_message": last_message_for_conversation(database, row["id"], current_user),
        }
        for row in group_rows
    ]
    return direct_items + group_items


def create_group(database: Database, owner: str, title: str | None, members: list[str] | None):
    conversation_id = f"grp:{uuid.uuid4().hex}"
    clean_title = (title or "").strip()[:80] or "Group Chat"
    database.execute(
        """
        INSERT INTO conversations(id, type, title, owner)
        VALUES (?, 'group', ?, ?)
        """,
        conversation_id,
        clean_title,
        owner,
    )
    database.execute(
        """
        INSERT INTO conversation_members(conversation_id, user_number, role, status)
        VALUES (?, ?, 'owner', 'active')
        """,
        conversation_id,
        owner,
    )
    invitees = [member for member in members or [] if member != owner]
    result = create_group_invites(database, owner, conversation_id, invitees)
    return {"conversation": group_summary(database, conversation_id, owner), "invites": result["invites"], "messages": result["messages"]}


def group_summary(database: Database, conversation_id: str, current_user: str):
    row = require_conversation_member(database, conversation_id, current_user)
    return {
        "id": row["id"],
        "type": row["type"],
        "title": row["title"],
        "peer": None,
        "members": conversation_members(database, conversation_id),
        "owner": row["owner"],
        "my_alias": row["alias"] or "",
        "last_message": last_message_for_conversation(database, conversation_id, current_user),
    }


def create_group_invites(database: Database, inviter: str, conversation_id: str, invitees: list[str]):
    row = require_conversation_member(database, conversation_id, inviter)
    if row["type"] != "group":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Can only invite to groups")
    unique_invitees = []
    seen = set()
    for invitee in invitees:
        value = str(invitee).strip()
        if not value or value == inviter or value in seen:
            continue
        require_user(database, value)
        existing = member_row(database, conversation_id, value)
        if existing:
            continue
        seen.add(value)
        unique_invitees.append(value)

    invites = []
    messages = []
    for invitee in unique_invitees:
        cursor = database.execute(
            """
            INSERT INTO group_invites(conversation_id, inviter, invitee, status)
            VALUES (?, ?, ?, 'pending')
            """,
            conversation_id,
            inviter,
            invitee,
        )
        invite = database.fetchone(
            """
            SELECT id, conversation_id, inviter, invitee, status, created_at, updated_at
            FROM group_invites
            WHERE id = ?
            """,
            cursor.lastrowid,
        )
        invite_payload = group_invite_from_row(database, invite)
        invites.append(invite_payload)
        messages.append(save_group_invite_card(database, inviter, invitee, invite_payload))
    return {"invites": invites, "messages": messages}


def save_group_invite_card(database: Database, inviter: str, invitee: str, invite: dict):
    conversation_id = ensure_direct_conversation(database, inviter, invitee)
    body = json.dumps(
        {
            "invite_id": invite["id"],
            "conversation_id": invite["conversation_id"],
            "title": invite["conversation"]["title"],
            "inviter": inviter,
        },
        ensure_ascii=False,
    )
    cursor = database.execute(
        """
        INSERT INTO messages(conversation_id, sender, receiver, type, message)
        VALUES (?, ?, ?, 'group_invite', ?)
        """,
        conversation_id,
        inviter,
        invitee,
        body,
    )
    return fetch_message(database, cursor.lastrowid)


def group_invite_from_row(database: Database, row) -> dict:
    conversation = database.fetchone(
        "SELECT id, title, owner FROM conversations WHERE id = ?",
        row["conversation_id"],
    )
    return {
        "id": row["id"],
        "conversation_id": row["conversation_id"],
        "inviter": row["inviter"],
        "invitee": row["invitee"],
        "status": row["status"],
        "created_at": utc_timestamp(row["created_at"]),
        "updated_at": utc_timestamp(row["updated_at"]),
        "conversation": {
            "id": conversation["id"],
            "title": conversation["title"],
            "owner": conversation["owner"],
            "members": conversation_members(database, conversation["id"]),
        },
    }


def list_group_invites(database: Database, current_user: str):
    rows = database.fetchall(
        """
        SELECT id, conversation_id, inviter, invitee, status, created_at, updated_at
        FROM group_invites
        WHERE invitee = ? AND status = 'pending'
        ORDER BY created_at DESC
        """,
        current_user,
    )
    return [group_invite_from_row(database, row) for row in rows]


def answer_group_invite(database: Database, current_user: str, invite_id: int, accepted: bool):
    row = database.fetchone(
        """
        SELECT id, conversation_id, inviter, invitee, status, created_at, updated_at
        FROM group_invites
        WHERE id = ? AND invitee = ?
        """,
        invite_id,
        current_user,
    )
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Group invite not found")
    if row["status"] != "pending":
        raise HTTPException(status.HTTP_409_CONFLICT, "Group invite is no longer pending")
    next_status = "accepted" if accepted else "rejected"
    database.execute(
        """
        UPDATE group_invites
        SET status = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        next_status,
        invite_id,
    )
    if accepted:
        database.execute(
            """
            UPDATE group_invites
            SET status = 'accepted', updated_at = CURRENT_TIMESTAMP
            WHERE conversation_id = ? AND invitee = ? AND status = 'pending'
            """,
            row["conversation_id"],
            current_user,
        )
        database.execute(
            """
            INSERT INTO conversation_members(conversation_id, user_number, role, status)
            VALUES (?, ?, 'member', 'active')
            ON CONFLICT(conversation_id, user_number)
            DO UPDATE SET status = 'active'
            """,
            row["conversation_id"],
            current_user,
        )
    updated = database.fetchone(
        """
        SELECT id, conversation_id, inviter, invitee, status, created_at, updated_at
        FROM group_invites
        WHERE id = ?
        """,
        invite_id,
    )
    return {"invite": group_invite_from_row(database, updated)}


def update_group(database: Database, current_user: str, conversation_id: str, title: str | None):
    require_group_owner(database, conversation_id, current_user)
    if title is not None:
        database.execute(
            "UPDATE conversations SET title = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            title.strip()[:80] or "Group Chat",
            conversation_id,
        )
    return {"conversation": group_summary(database, conversation_id, current_user)}


def update_group_alias(database: Database, current_user: str, conversation_id: str, alias: str):
    require_conversation_member(database, conversation_id, current_user)
    database.execute(
        """
        UPDATE conversation_members
        SET alias = ?
        WHERE conversation_id = ? AND user_number = ?
        """,
        alias.strip()[:48],
        conversation_id,
        current_user,
    )
    return {"conversation": group_summary(database, conversation_id, current_user)}


def remove_group_member(database: Database, current_user: str, conversation_id: str, member: str):
    row = require_group_owner(database, conversation_id, current_user)
    if member == row["owner"]:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Owner cannot be removed")
    database.execute(
        """
        UPDATE conversation_members
        SET status = 'left'
        WHERE conversation_id = ? AND user_number = ?
        """,
        conversation_id,
        member,
    )
    return {"status": "removed", "conversation": group_summary(database, conversation_id, current_user)}


def update_friend_profile(database: Database, current_user: str, friend: str, alias: str | None, tags: list[str] | None):
    if not are_friends(database, current_user, friend):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Friend not found")
    updates = []
    params = []
    if alias is not None:
        updates.append("alias = ?")
        params.append(alias.strip()[:48])
    if tags is not None:
        updates.append("tags = ?")
        params.append(normalize_tags(tags))
    if updates:
        params.extend([current_user, friend])
        database.execute(
            f"UPDATE friendships SET {', '.join(updates)} WHERE owner = ? AND friend = ?",
            *params,
        )
    row = database.fetchone(
        """
        SELECT u.number, u.nickname, u.avatar, u.avatar_file, u.avatar_mime_type, u.avatar_color, u.background, u.gender, u.motto, f.alias, f.tags
        FROM friendships f
        JOIN users u ON u.number = f.friend
        WHERE f.owner = ? AND f.friend = ?
        """,
        current_user,
        friend,
    )
    return {"friend": friend_user(row)}


def are_friends(database: Database, user_a: str, user_b: str) -> bool:
    row = database.fetchone("SELECT 1 FROM friendships WHERE owner = ? AND friend = ?", user_a, user_b)
    return row is not None


def require_message_permission(database: Database, sender: str, receiver: str):
    require_user(database, receiver)
    if not are_friends(database, sender, receiver):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "You can only message friends")


def utc_timestamp(value) -> str:
    timestamp = str(value or "").strip()
    if not timestamp:
        return timestamp
    normalized = timestamp.replace(" ", "T")
    if normalized.endswith("Z") or "+" in normalized[10:] or "-" in normalized[10:]:
        return normalized
    return f"{normalized}Z"


def message_from_row(row) -> dict:
    message = dict(row)
    message["time"] = utc_timestamp(message["time"])
    if message.get("file_name"):
        message["attachment"] = {
            "name": message.pop("file_name"),
            "url": message.pop("file_url"),
            "mime_type": message.pop("mime_type"),
            "size": message.pop("file_size"),
        }
    else:
        message.pop("file_name", None)
        message.pop("file_url", None)
        message.pop("mime_type", None)
        message.pop("file_size", None)
        message["attachment"] = None
    return message


def fetch_message(database: Database, message_id: int):
    row = database.fetchone(
        """
        SELECT
            m.id,
            m.conversation_id,
            m.sender,
            m.receiver,
            m.time,
            m.type,
            m.message,
            a.original_name AS file_name,
            CASE
                WHEN a.stored_name IS NULL THEN NULL
                ELSE '/api/files/' || a.stored_name
            END AS file_url,
            a.mime_type,
            a.size AS file_size
        FROM messages m
        LEFT JOIN attachments a ON a.message_id = m.id
        WHERE m.id = ?
        """,
        message_id,
    )
    return message_from_row(row)


def audio_attachment_for_transcription(database: Database, current_user: str, message_id: int):
    row = database.fetchone(
        """
        SELECT
            m.id,
            m.conversation_id,
            m.sender,
            m.receiver,
            m.type,
            a.original_name,
            a.stored_name,
            a.mime_type,
            a.size
        FROM messages m
        JOIN attachments a ON a.message_id = m.id
        WHERE m.id = ?
        """,
        message_id,
    )
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Audio message not found")
    mime_type = row["mime_type"] or ""
    if row["type"] != "audio" and not mime_type.startswith("audio/"):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Message is not an audio attachment")
    if row["conversation_id"]:
        require_conversation_member(database, row["conversation_id"], current_user)
    elif current_user not in {row["sender"], row["receiver"]}:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "You cannot transcribe this message")
    return {
        "message_id": row["id"],
        "original_name": row["original_name"],
        "stored_name": row["stored_name"],
        "mime_type": mime_type or "application/octet-stream",
        "size": row["size"],
    }


def save_message(database: Database, sender: str, receiver: str, message_type: str, body: str):
    require_message_permission(database, sender, receiver)
    conversation_id = ensure_direct_conversation(database, sender, receiver)
    cursor = database.execute(
        """
        INSERT INTO messages(conversation_id, sender, receiver, type, message)
        VALUES (?, ?, ?, ?, ?)
        """,
        conversation_id,
        sender,
        receiver,
        message_type,
        body,
    )
    return fetch_message(database, cursor.lastrowid)


def save_attachment_message(
    database: Database,
    sender: str,
    receiver: str,
    original_name: str,
    stored_name: str,
    mime_type: str,
    size: int,
):
    require_message_permission(database, sender, receiver)
    conversation_id = ensure_direct_conversation(database, sender, receiver)
    message_type = attachment_message_type(mime_type)
    cursor = database.execute(
        """
        INSERT INTO messages(conversation_id, sender, receiver, type, message)
        VALUES (?, ?, ?, ?, ?)
        """,
        conversation_id,
        sender,
        receiver,
        message_type,
        original_name,
    )
    database.execute(
        """
        INSERT INTO attachments(message_id, original_name, stored_name, mime_type, size)
        VALUES (?, ?, ?, ?, ?)
        """,
        cursor.lastrowid,
        original_name,
        stored_name,
        mime_type,
        size,
    )
    return fetch_message(database, cursor.lastrowid)


def save_conversation_attachment_message(
    database: Database,
    sender: str,
    conversation_id: str,
    original_name: str,
    stored_name: str,
    mime_type: str,
    size: int,
):
    row = require_conversation_member(database, conversation_id, sender)
    if row["type"] == "direct":
        members = [member["number"] for member in conversation_members(database, conversation_id)]
        receiver = next((member for member in members if member != sender), sender)
        return save_attachment_message(database, sender, receiver, original_name, stored_name, mime_type, size)

    message_type = attachment_message_type(mime_type)
    cursor = database.execute(
        """
        INSERT INTO messages(conversation_id, sender, receiver, type, message)
        VALUES (?, ?, ?, ?, ?)
        """,
        conversation_id,
        sender,
        sender,
        message_type,
        original_name,
    )
    database.execute(
        """
        INSERT INTO attachments(message_id, original_name, stored_name, mime_type, size)
        VALUES (?, ?, ?, ?, ?)
        """,
        cursor.lastrowid,
        original_name,
        stored_name,
        mime_type,
        size,
    )
    database.execute("UPDATE conversations SET updated_at = CURRENT_TIMESTAMP WHERE id = ?", conversation_id)
    return fetch_message(database, cursor.lastrowid)


def attachment_message_type(mime_type: str):
    if mime_type.startswith("image/"):
        return "image"
    if mime_type.startswith("audio/"):
        return "audio"
    if mime_type.startswith("video/"):
        return "video"
    return "file"


def list_messages(database: Database, current_user: str, peer: str, limit: int):
    if not are_friends(database, current_user, peer):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "You can only read messages with friends")
    conversation_id = ensure_direct_conversation(database, current_user, peer)
    rows = database.fetchall(
        """
        SELECT
            m.id,
            m.conversation_id,
            m.sender,
            m.receiver,
            m.time,
            m.type,
            m.message,
            a.original_name AS file_name,
            CASE
                WHEN a.stored_name IS NULL THEN NULL
                ELSE '/api/files/' || a.stored_name
            END AS file_url,
            a.mime_type,
            a.size AS file_size
        FROM messages m
        LEFT JOIN attachments a ON a.message_id = m.id
        WHERE m.conversation_id = ? OR ((m.sender = ? AND m.receiver = ?) OR (m.sender = ? AND m.receiver = ?))
        ORDER BY m.id DESC
        LIMIT ?
        """,
        conversation_id,
        current_user,
        peer,
        peer,
        current_user,
        min(max(limit, 1), 200),
    )
    return [message_from_row(row) for row in reversed(rows)]


def list_conversation_messages(database: Database, current_user: str, conversation_id: str, limit: int):
    row = require_conversation_member(database, conversation_id, current_user)
    if row["type"] == "direct":
        members = [member["number"] for member in conversation_members(database, conversation_id)]
        peer = next((member for member in members if member != current_user), current_user)
        return list_messages(database, current_user, peer, limit)
    rows = database.fetchall(
        """
        SELECT
            m.id,
            m.conversation_id,
            m.sender,
            m.receiver,
            m.time,
            m.type,
            m.message,
            a.original_name AS file_name,
            CASE
                WHEN a.stored_name IS NULL THEN NULL
                ELSE '/api/files/' || a.stored_name
            END AS file_url,
            a.mime_type,
            a.size AS file_size
        FROM messages m
        LEFT JOIN attachments a ON a.message_id = m.id
        WHERE m.conversation_id = ?
        ORDER BY m.id DESC
        LIMIT ?
        """,
        conversation_id,
        min(max(limit, 1), 200),
    )
    return [message_from_row(message) for message in reversed(rows)]


def save_conversation_message(database: Database, sender: str, conversation_id: str, message_type: str, body: str):
    row = require_conversation_member(database, conversation_id, sender)
    if row["type"] == "direct":
        members = [member["number"] for member in conversation_members(database, conversation_id)]
        receiver = next((member for member in members if member != sender), sender)
        return save_message(database, sender, receiver, message_type, body)
    cursor = database.execute(
        """
        INSERT INTO messages(conversation_id, sender, receiver, type, message)
        VALUES (?, ?, ?, ?, ?)
        """,
        conversation_id,
        sender,
        sender,
        message_type,
        body,
    )
    database.execute("UPDATE conversations SET updated_at = CURRENT_TIMESTAMP WHERE id = ?", conversation_id)
    return fetch_message(database, cursor.lastrowid)
