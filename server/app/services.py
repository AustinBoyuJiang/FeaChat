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


def update_account(
    database: Database,
    current_user: str,
    nickname: str | None,
    motto: str | None,
    current_password: str | None,
    new_password: str | None,
):
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
    if motto is not None:
        updates.append("motto = ?")
        params.append(motto.strip()[:120])
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
        SELECT c.id, c.type, c.title, c.owner, c.status AS conversation_status, cm.role, cm.alias, cm.status, cm.left_at, cm.left_message_id
        FROM conversations c
        JOIN conversation_members cm ON cm.conversation_id = c.id
        WHERE c.id = ? AND cm.user_number = ?
        """,
        conversation_id,
        user_number,
    )


def require_conversation_member(database: Database, conversation_id: str, user_number: str):
    row = member_row(database, conversation_id, user_number)
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Conversation not found")
    return row


def require_active_conversation_member(database: Database, conversation_id: str, user_number: str):
    row = require_conversation_member(database, conversation_id, user_number)
    if row["conversation_status"] != "active" or row["status"] != "active":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Conversation is no longer active")
    return row


def require_group_owner(database: Database, conversation_id: str, user_number: str):
    row = require_active_conversation_member(database, conversation_id, user_number)
    if row["type"] != "group":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Not a group conversation")
    if row["owner"] != user_number:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Only group owner can do this")
    return row


def conversation_members(database: Database, conversation_id: str):
    rows = database.fetchall(
        """
        SELECT u.number, u.nickname, u.avatar, u.avatar_file, u.avatar_mime_type, u.avatar_color, u.background, u.gender, u.motto, cm.role, cm.alias, cm.joined_at
        FROM conversation_members cm
        JOIN users u ON u.number = cm.user_number
        WHERE cm.conversation_id = ? AND cm.status = 'active'
        ORDER BY CASE WHEN cm.role = 'owner' THEN 0 ELSE 1 END, cm.joined_at, lower(u.nickname), u.number
        """,
        conversation_id,
    )
    members = []
    for row in rows:
        user = public_user(row)
        user["role"] = row["role"]
        user["group_alias"] = row["alias"] or ""
        user["joined_at"] = utc_timestamp(row["joined_at"])
        members.append(user)
    return members


def conversation_participants(database: Database, conversation_id: str):
    rows = database.fetchall(
        """
        SELECT user_number
        FROM conversation_members
        WHERE conversation_id = ?
        ORDER BY joined_at, user_number
        """,
        conversation_id,
    )
    return [row["user_number"] for row in rows]


def active_conversation_participants(database: Database, conversation_id: str):
    rows = database.fetchall(
        """
        SELECT user_number
        FROM conversation_members
        WHERE conversation_id = ? AND status = 'active'
        ORDER BY joined_at, user_number
        """,
        conversation_id,
    )
    return [row["user_number"] for row in rows]


def visible_message_cutoff_for_member(row):
    if row is None or row["status"] != "left":
        return None
    if row["left_message_id"]:
        return ("id", row["left_message_id"])
    if row["left_at"]:
        return ("time", row["left_at"])
    return None


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
        member = member_row(database, conversation_id, current_user)
        cutoff = visible_message_cutoff_for_member(member)
        visibility_clause = f"AND m.{cutoff[0]} <= ?" if cutoff else ""
        params = [conversation_id]
        if cutoff:
            params.append(cutoff[1])
        row = database.fetchone(
            f"""
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
            {visibility_clause}
            ORDER BY m.id DESC
            LIMIT 1
            """,
            *params,
        )
    return message_from_row(row) if row else None


def user_for_direct_conversation(database: Database, current_user: str, peer: str) -> dict:
    row = database.fetchone(
        """
        SELECT u.number, u.nickname, u.avatar, u.avatar_file, u.avatar_mime_type, u.avatar_color, u.background, u.gender, u.motto, f.alias, f.tags
        FROM users u
        LEFT JOIN friendships f ON f.owner = ? AND f.friend = u.number
        WHERE u.number = ?
        """,
        current_user,
        peer,
    )
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    return friend_user(row) if row["alias"] is not None else {**public_user(row), "display_name": public_user(row)["nickname"], "tags": []}


def list_conversations(database: Database, current_user: str):
    direct_peers = {}
    for friend in list_friends(database, current_user):
        direct_peers[friend["number"]] = friend
        ensure_direct_conversation(database, current_user, friend["number"])

    historical_rows = database.fetchall(
        """
        SELECT c.id, other.user_number AS peer
        FROM conversations c
        JOIN conversation_members mine ON mine.conversation_id = c.id AND mine.user_number = ?
        JOIN conversation_members other ON other.conversation_id = c.id AND other.user_number <> ?
        WHERE c.type = 'direct'
          AND EXISTS (SELECT 1 FROM messages m WHERE m.conversation_id = c.id)
        """,
        current_user,
        current_user,
    )
    for row in historical_rows:
        if row["peer"] not in direct_peers:
            direct_peers[row["peer"]] = user_for_direct_conversation(database, current_user, row["peer"])

    direct_items = []
    for peer_number, friend in direct_peers.items():
        conversation_id = ensure_direct_conversation(database, current_user, peer_number)
        is_friend = are_friends(database, current_user, peer_number)
        direct_items.append(
            {
                "id": conversation_id,
                "type": "direct",
                "title": friend.get("display_name") or friend["nickname"],
                "peer": friend,
                "members": [friend],
                "owner": None,
                "my_alias": "",
                "status": "active" if is_friend else "inactive",
                "my_status": "active" if is_friend else "left",
                "last_message": last_message_for_conversation(database, conversation_id, current_user, peer_number),
            }
        )

    group_rows = database.fetchall(
        """
        SELECT c.id, c.type, c.title, c.owner, c.status AS conversation_status, c.updated_at, cm.alias, cm.status AS member_status
        FROM conversations c
        JOIN conversation_members cm ON cm.conversation_id = c.id
        WHERE c.type = 'group' AND cm.user_number = ?
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
            "status": row["conversation_status"],
            "my_status": row["member_status"],
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
        "status": row["conversation_status"],
        "my_status": row["status"],
        "last_message": last_message_for_conversation(database, conversation_id, current_user),
    }


def create_group_invites(database: Database, inviter: str, conversation_id: str, invitees: list[str]):
    row = require_active_conversation_member(database, conversation_id, inviter)
    if row["type"] != "group":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Can only invite to groups")
    if row["conversation_status"] != "active":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Group is dissolved")
    unique_invitees = []
    seen = set()
    for invitee in invitees:
        value = str(invitee).strip()
        if not value or value == inviter or value in seen:
            continue
        require_user(database, value)
        existing = member_row(database, conversation_id, value)
        if existing and existing["status"] == "active":
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
    avatar_members = [
        {
            "number": member["number"],
            "nickname": member["nickname"],
            "display_name": member.get("group_alias") or member["nickname"] or member["number"],
            "avatar_url": member.get("avatar_url"),
            "avatar_color": member.get("avatar_color"),
        }
        for member in conversation_members(database, invite["conversation_id"])[:9]
    ]
    body = json.dumps(
        {
            "invite_id": invite["id"],
            "conversation_id": invite["conversation_id"],
            "title": invite["conversation"]["title"],
            "inviter": inviter,
            "avatar_members": avatar_members,
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


def save_system_message(database: Database, conversation_id: str, actor: str, body: str):
    cursor = database.execute(
        """
        INSERT INTO messages(conversation_id, sender, receiver, type, message)
        VALUES (?, ?, ?, 'system', ?)
        """,
        conversation_id,
        actor,
        actor,
        body.strip(),
    )
    database.execute("UPDATE conversations SET updated_at = CURRENT_TIMESTAMP WHERE id = ?", conversation_id)
    return fetch_message(database, cursor.lastrowid)


def member_display_name(database: Database, conversation_id: str, number: str):
    row = database.fetchone(
        """
        SELECT u.number, u.nickname, cm.alias
        FROM conversation_members cm
        JOIN users u ON u.number = cm.user_number
        WHERE cm.conversation_id = ? AND cm.user_number = ?
        """,
        conversation_id,
        number,
    )
    if row is None:
        user = require_user(database, number)
        return user["nickname"] or number
    return row["alias"] or row["nickname"] or number


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
    conversation = database.fetchone("SELECT status FROM conversations WHERE id = ?", row["conversation_id"])
    if conversation is None or conversation["status"] != "active":
        raise HTTPException(status.HTTP_409_CONFLICT, "Group is no longer active")
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
            DO UPDATE SET status = 'active', left_at = NULL, left_message_id = NULL
            """,
            row["conversation_id"],
            current_user,
        )
        system_message = save_system_message(
            database,
            row["conversation_id"],
            current_user,
            f"{member_display_name(database, row['conversation_id'], current_user)} joined the group",
        )
    else:
        system_message = None
    updated = database.fetchone(
        """
        SELECT id, conversation_id, inviter, invitee, status, created_at, updated_at
        FROM group_invites
        WHERE id = ?
        """,
        invite_id,
    )
    return {"invite": group_invite_from_row(database, updated), "message": system_message}


def update_group(database: Database, current_user: str, conversation_id: str, title: str | None):
    require_group_owner(database, conversation_id, current_user)
    message = None
    if title is not None:
        clean_title = title.strip()[:80] or "Group Chat"
        database.execute(
            "UPDATE conversations SET title = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            clean_title,
            conversation_id,
        )
        message = save_system_message(database, conversation_id, current_user, f"Group name changed to {clean_title}")
    return {"conversation": group_summary(database, conversation_id, current_user), "message": message}


def update_group_alias(database: Database, current_user: str, conversation_id: str, alias: str):
    require_active_conversation_member(database, conversation_id, current_user)
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
    removed_name = member_display_name(database, conversation_id, member)
    message = save_system_message(database, conversation_id, current_user, f"{removed_name} was removed from the group")
    database.execute(
        """
        UPDATE conversation_members
        SET status = 'left', left_at = CURRENT_TIMESTAMP, left_message_id = ?
        WHERE conversation_id = ? AND user_number = ?
        """,
        message["id"],
        conversation_id,
        member,
    )
    return {"status": "removed", "conversation": group_summary(database, conversation_id, current_user), "message": message}


def leave_group(database: Database, current_user: str, conversation_id: str):
    row = require_active_conversation_member(database, conversation_id, current_user)
    if row["type"] != "group":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Not a group conversation")
    if row["owner"] == current_user:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Group owner must disband the group")
    name = member_display_name(database, conversation_id, current_user)
    message = save_system_message(database, conversation_id, current_user, f"{name} left the group")
    database.execute(
        """
        UPDATE conversation_members
        SET status = 'left', left_at = CURRENT_TIMESTAMP, left_message_id = ?
        WHERE conversation_id = ? AND user_number = ?
        """,
        message["id"],
        conversation_id,
        current_user,
    )
    return {"status": "left", "conversation_id": conversation_id, "message": message}


def dissolve_group(database: Database, current_user: str, conversation_id: str):
    require_group_owner(database, conversation_id, current_user)
    database.execute(
        """
        UPDATE conversations
        SET status = 'dissolved', updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        conversation_id,
    )
    database.execute(
        """
        UPDATE group_invites
        SET status = 'rejected', updated_at = CURRENT_TIMESTAMP
        WHERE conversation_id = ? AND status = 'pending'
        """,
        conversation_id,
    )
    message = save_system_message(database, conversation_id, current_user, "Group chat was disbanded")
    return {"status": "dissolved", "conversation_id": conversation_id, "message": message}


def transfer_group_owner(database: Database, current_user: str, conversation_id: str, new_owner: str):
    row = require_group_owner(database, conversation_id, current_user)
    target = member_row(database, conversation_id, new_owner)
    if target is None or target["status"] != "active":
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Member not found")
    if new_owner == row["owner"]:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Member is already the owner")
    database.execute(
        """
        UPDATE conversation_members
        SET role = CASE WHEN user_number = ? THEN 'owner' ELSE 'member' END
        WHERE conversation_id = ?
        """,
        new_owner,
        conversation_id,
    )
    database.execute(
        "UPDATE conversations SET owner = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        new_owner,
        conversation_id,
    )
    name = member_display_name(database, conversation_id, new_owner)
    message = save_system_message(database, conversation_id, current_user, f"{name} became the new group owner")
    return {"status": "transferred", "conversation": group_summary(database, conversation_id, current_user), "message": message}


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


def require_direct_history_access(database: Database, current_user: str, peer: str):
    require_user(database, peer)
    conversation_id = direct_conversation_id(current_user, peer)
    row = database.fetchone(
        """
        SELECT 1
        FROM conversation_members mine
        JOIN conversation_members other ON other.conversation_id = mine.conversation_id
        WHERE mine.conversation_id = ?
          AND mine.user_number = ?
          AND other.user_number = ?
        """,
        conversation_id,
        current_user,
        peer,
    )
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Conversation not found")
    return conversation_id


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
    row = require_active_conversation_member(database, conversation_id, sender)
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
    if are_friends(database, current_user, peer):
        conversation_id = ensure_direct_conversation(database, current_user, peer)
    else:
        conversation_id = require_direct_history_access(database, current_user, peer)
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
    cutoff = visible_message_cutoff_for_member(row)
    visibility_clause = f"AND m.{cutoff[0]} <= ?" if cutoff else ""
    params = [conversation_id]
    if cutoff:
        params.append(cutoff[1])
    params.append(min(max(limit, 1), 200))
    rows = database.fetchall(
        f"""
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
        {visibility_clause}
        ORDER BY m.id DESC
        LIMIT ?
        """,
        *params,
    )
    return [message_from_row(message) for message in reversed(rows)]


def save_conversation_message(database: Database, sender: str, conversation_id: str, message_type: str, body: str):
    row = require_active_conversation_member(database, conversation_id, sender)
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


def moment_visible_to_user(database: Database, current_user: str, author: str) -> bool:
    return author == current_user or are_friends(database, current_user, author)


def require_moment_access(database: Database, current_user: str, post_id: int):
    row = database.fetchone(
        """
        SELECT
            p.id,
            p.author,
            p.body,
            p.created_at,
            p.updated_at,
            u.number,
            u.nickname,
            u.avatar,
            u.avatar_file,
            u.avatar_mime_type,
            u.avatar_color,
            u.background,
            u.gender,
            u.motto
        FROM moment_posts p
        JOIN users u ON u.number = p.author
        WHERE p.id = ?
        """,
        post_id,
    )
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Moment not found")
    if not moment_visible_to_user(database, current_user, row["author"]):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "You cannot view this moment")
    return row


def moment_image_from_row(row) -> dict:
    return {
        "id": row["id"],
        "name": row["original_name"],
        "url": f"/api/files/{row['stored_name']}",
        "mime_type": row["mime_type"],
        "size": row["size"],
    }


def moment_comment_from_row(row) -> dict:
    return {
        "id": row["id"],
        "post_id": row["post_id"],
        "author": public_user(row),
        "body": row["body"],
        "created_at": utc_timestamp(row["created_at"]),
    }


def moment_from_row(database: Database, current_user: str, row) -> dict:
    images = database.fetchall(
        """
        SELECT id, original_name, stored_name, mime_type, size
        FROM moment_images
        WHERE post_id = ?
        ORDER BY position, id
        """,
        row["id"],
    )
    likes = database.fetchall(
        """
        SELECT u.number, u.nickname, u.avatar, u.avatar_file, u.avatar_mime_type, u.avatar_color, u.background, u.gender, u.motto
        FROM moment_likes l
        JOIN users u ON u.number = l.user_number
        WHERE l.post_id = ?
        ORDER BY l.created_at, l.user_number
        """,
        row["id"],
    )
    comments = database.fetchall(
        """
        SELECT
            c.id,
            c.post_id,
            c.body,
            c.created_at,
            u.number,
            u.nickname,
            u.avatar,
            u.avatar_file,
            u.avatar_mime_type,
            u.avatar_color,
            u.background,
            u.gender,
            u.motto
        FROM moment_comments c
        JOIN users u ON u.number = c.author
        WHERE c.post_id = ?
        ORDER BY c.created_at, c.id
        """,
        row["id"],
    )
    author = public_user(row)
    like_users = [public_user(like) for like in likes]
    return {
        "id": row["id"],
        "author": author,
        "body": row["body"],
        "images": [moment_image_from_row(image) for image in images],
        "likes": like_users,
        "liked_by_me": any(user["number"] == current_user for user in like_users),
        "comments": [moment_comment_from_row(comment) for comment in comments],
        "created_at": utc_timestamp(row["created_at"]),
        "updated_at": utc_timestamp(row["updated_at"]),
    }


def list_moments(database: Database, current_user: str, limit: int = 50):
    rows = database.fetchall(
        """
        SELECT
            p.id,
            p.author,
            p.body,
            p.created_at,
            p.updated_at,
            u.number,
            u.nickname,
            u.avatar,
            u.avatar_file,
            u.avatar_mime_type,
            u.avatar_color,
            u.background,
            u.gender,
            u.motto
        FROM moment_posts p
        JOIN users u ON u.number = p.author
        WHERE p.author = ?
           OR EXISTS (
                SELECT 1
                FROM friendships f
                WHERE f.owner = ? AND f.friend = p.author
           )
        ORDER BY p.created_at DESC, p.id DESC
        LIMIT ?
        """,
        current_user,
        current_user,
        min(max(limit, 1), 100),
    )
    return [moment_from_row(database, current_user, row) for row in rows]


def list_user_moments(database: Database, current_user: str, author: str, limit: int = 50):
    require_user(database, author)
    if not moment_visible_to_user(database, current_user, author):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "You cannot view this user's moments")
    rows = database.fetchall(
        """
        SELECT
            p.id,
            p.author,
            p.body,
            p.created_at,
            p.updated_at,
            u.number,
            u.nickname,
            u.avatar,
            u.avatar_file,
            u.avatar_mime_type,
            u.avatar_color,
            u.background,
            u.gender,
            u.motto
        FROM moment_posts p
        JOIN users u ON u.number = p.author
        WHERE p.author = ?
        ORDER BY p.created_at DESC, p.id DESC
        LIMIT ?
        """,
        author,
        min(max(limit, 1), 100),
    )
    return [moment_from_row(database, current_user, row) for row in rows]


def moment_profile_summary(database: Database, current_user: str, author: str):
    user = public_user(require_user(database, author))
    if not moment_visible_to_user(database, current_user, author):
        return {"user": user, "images": []}
    rows = database.fetchall(
        """
        SELECT i.id, i.original_name, i.stored_name, i.mime_type, i.size
        FROM moment_images i
        JOIN moment_posts p ON p.id = i.post_id
        WHERE p.author = ?
        ORDER BY p.created_at DESC, p.id DESC, i.position ASC, i.id ASC
        LIMIT 4
        """,
        author,
    )
    return {"user": user, "images": [moment_image_from_row(row) for row in rows]}


def create_moment_notification(database: Database, owner: str, actor: str, post_id: int, notification_type: str, comment_id: int | None = None):
    if owner == actor:
        return
    database.execute(
        """
        INSERT INTO moment_notifications(owner, actor, post_id, type, comment_id)
        VALUES (?, ?, ?, ?, ?)
        """,
        owner,
        actor,
        post_id,
        notification_type,
        comment_id,
    )


def list_moment_notifications(database: Database, current_user: str, limit: int = 80):
    rows = database.fetchall(
        """
        SELECT
            n.id,
            n.post_id,
            n.type,
            n.is_read,
            n.created_at,
            c.body AS comment_body,
            p.body AS post_body,
            u.number,
            u.nickname,
            u.avatar,
            u.avatar_file,
            u.avatar_mime_type,
            u.avatar_color,
            u.background,
            u.gender,
            u.motto,
            (
                SELECT mi.stored_name
                FROM moment_images mi
                WHERE mi.post_id = n.post_id
                ORDER BY mi.position, mi.id
                LIMIT 1
            ) AS image_stored_name,
            (
                SELECT mi.original_name
                FROM moment_images mi
                WHERE mi.post_id = n.post_id
                ORDER BY mi.position, mi.id
                LIMIT 1
            ) AS image_original_name,
            (
                SELECT mi.mime_type
                FROM moment_images mi
                WHERE mi.post_id = n.post_id
                ORDER BY mi.position, mi.id
                LIMIT 1
            ) AS image_mime_type,
            (
                SELECT mi.size
                FROM moment_images mi
                WHERE mi.post_id = n.post_id
                ORDER BY mi.position, mi.id
                LIMIT 1
            ) AS image_size
        FROM moment_notifications n
        JOIN users u ON u.number = n.actor
        JOIN moment_posts p ON p.id = n.post_id
        LEFT JOIN moment_comments c ON c.id = n.comment_id
        WHERE n.owner = ?
        ORDER BY n.created_at DESC, n.id DESC
        LIMIT ?
        """,
        current_user,
        min(max(limit, 1), 150),
    )
    notifications = []
    for row in rows:
        image = None
        if row["image_stored_name"]:
            image = {
                "name": row["image_original_name"],
                "url": f"/api/files/{row['image_stored_name']}",
                "mime_type": row["image_mime_type"],
                "size": row["image_size"],
            }
        notifications.append(
            {
                "id": row["id"],
                "post_id": row["post_id"],
                "type": row["type"],
                "is_read": bool(row["is_read"]),
                "created_at": utc_timestamp(row["created_at"]),
                "actor": public_user(row),
                "comment_body": row["comment_body"] or "",
                "post_body": row["post_body"] or "",
                "post_image": image,
            }
        )
    return notifications


def moment_unread_count(database: Database, current_user: str) -> int:
    row = database.fetchone(
        "SELECT COUNT(*) AS count FROM moment_notifications WHERE owner = ? AND is_read = 0",
        current_user,
    )
    return int(row["count"] if row else 0)


def mark_moment_notifications_read(database: Database, current_user: str):
    database.execute("UPDATE moment_notifications SET is_read = 1 WHERE owner = ?", current_user)
    return {"status": "ok"}


def create_moment(
    database: Database,
    current_user: str,
    body: str,
    images: list[tuple[str, str, str, int]],
):
    text = body.strip()
    if not text and not images:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Moment needs text or images")
    if len(images) > 9:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "A moment can include at most 9 images")
    cursor = database.execute(
        """
        INSERT INTO moment_posts(author, body)
        VALUES (?, ?)
        """,
        current_user,
        text[:4000],
    )
    post_id = cursor.lastrowid
    for index, (original_name, stored_name, mime_type, size) in enumerate(images):
        if not mime_type.startswith("image/"):
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Moments only support image attachments")
        database.execute(
            """
            INSERT INTO moment_images(post_id, original_name, stored_name, mime_type, size, position)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            post_id,
            original_name,
            stored_name,
            mime_type,
            size,
            index,
        )
    return moment_from_row(database, current_user, require_moment_access(database, current_user, post_id))


def delete_moment(database: Database, current_user: str, post_id: int):
    row = require_moment_access(database, current_user, post_id)
    if row["author"] != current_user:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Only the author can delete this moment")
    images = database.fetchall(
        "SELECT stored_name FROM moment_images WHERE post_id = ?",
        post_id,
    )
    database.execute("DELETE FROM moment_posts WHERE id = ?", post_id)
    return {
        "status": "deleted",
        "post_id": post_id,
        "files": [image["stored_name"] for image in images],
    }


def like_moment(database: Database, current_user: str, post_id: int):
    row = require_moment_access(database, current_user, post_id)
    cursor = database.execute(
        """
        INSERT OR IGNORE INTO moment_likes(post_id, user_number)
        VALUES (?, ?)
        """,
        post_id,
        current_user,
    )
    if cursor.rowcount:
        create_moment_notification(database, row["author"], current_user, post_id, "like")
    return moment_from_row(database, current_user, require_moment_access(database, current_user, post_id))


def unlike_moment(database: Database, current_user: str, post_id: int):
    require_moment_access(database, current_user, post_id)
    database.execute(
        "DELETE FROM moment_likes WHERE post_id = ? AND user_number = ?",
        post_id,
        current_user,
    )
    return moment_from_row(database, current_user, require_moment_access(database, current_user, post_id))


def comment_on_moment(database: Database, current_user: str, post_id: int, body: str):
    row = require_moment_access(database, current_user, post_id)
    text = body.strip()
    if not text:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Comment cannot be empty")
    cursor = database.execute(
        """
        INSERT INTO moment_comments(post_id, author, body)
        VALUES (?, ?, ?)
        """,
        post_id,
        current_user,
        text[:1000],
    )
    create_moment_notification(database, row["author"], current_user, post_id, "comment", cursor.lastrowid)
    return moment_from_row(database, current_user, require_moment_access(database, current_user, post_id))
