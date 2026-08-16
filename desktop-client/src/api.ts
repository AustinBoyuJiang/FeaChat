import type { Conversation, FriendRequest, FriendRequestRecord, GroupInvite, Message, User } from "./types";

const API_URL = import.meta.env.VITE_API_URL ?? "http://127.0.0.1:8000";

type ApiOptions = {
  token?: string | null;
  method?: string;
  body?: object | FormData;
};

async function request<T>(path: string, options: ApiOptions = {}): Promise<T> {
  let body: BodyInit | undefined;
  if (options.body instanceof FormData) {
    body = options.body;
  } else if (options.body !== undefined) {
    body = JSON.stringify(options.body);
  }
  const isFormData = body instanceof FormData;
  const headers: Record<string, string> = {};
  if (!isFormData) {
    headers["Content-Type"] = "application/json";
  }
  if (options.token) {
    headers.Authorization = `Bearer ${options.token}`;
  }
  const response = await fetch(`${API_URL}${path}`, {
    method: options.method ?? "GET",
    headers,
    body
  });
  if (!response.ok) {
    const detail = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(typeof detail.detail === "string" ? detail.detail : "Request failed");
  }
  return response.json() as Promise<T>;
}

export const api = {
  apiUrl: API_URL,
  fileUrl(path: string, download = false) {
    const url = new URL(path.startsWith("http") ? path : `${API_URL}${path}`);
    if (download) {
      url.searchParams.set("download", "1");
    }
    return url.toString();
  },
  wsUrl(token: string) {
    const url = new URL(API_URL);
    url.protocol = url.protocol === "https:" ? "wss:" : "ws:";
    url.pathname = "/ws";
    url.search = `token=${encodeURIComponent(token)}`;
    return url.toString();
  },
  register(payload: { number: string; password: string; email: string; nickname?: string }) {
    return request<{ user: User }>("/api/auth/register", { method: "POST", body: payload });
  },
  login(payload: { number: string; password: string }) {
    return request<{ token: string; user: User }>("/api/auth/login", { method: "POST", body: payload });
  },
  me(token: string) {
    return request<{ user: User }>("/api/me", { token });
  },
  updateMe(token: string, payload: { nickname?: string; current_password?: string; new_password?: string }) {
    return request<{ user: User }>("/api/me", {
      token,
      method: "PATCH",
      body: payload
    });
  },
  uploadAvatar(token: string, file: File) {
    const body = new FormData();
    body.append("file", file);
    return request<{ user: User }>("/api/me/avatar", {
      token,
      method: "POST",
      body
    });
  },
  searchUsers(token: string, query: string) {
    return request<{ users: User[] }>(`/api/users/search?q=${encodeURIComponent(query)}`, { token });
  },
  friends(token: string) {
    return request<{ friends: User[] }>("/api/friends", { token });
  },
  conversations(token: string) {
    return request<{ conversations: Conversation[] }>("/api/conversations", { token });
  },
  friendRequests(token: string) {
    return request<{ requests: FriendRequest[] }>("/api/friends/requests", { token });
  },
  friendRequestHistory(token: string) {
    return request<{ requests: FriendRequestRecord[] }>("/api/friends/requests/history", { token });
  },
  groupInvites(token: string) {
    return request<{ invites: GroupInvite[] }>("/api/groups/invites", { token });
  },
  createGroup(token: string, payload: { title: string; members: string[] }) {
    return request<{ conversation: Conversation; invites: GroupInvite[]; messages: Message[] }>("/api/groups", {
      token,
      method: "POST",
      body: payload
    });
  },
  inviteToGroup(token: string, conversationId: string, invitees: string[]) {
    return request<{ invites: GroupInvite[]; messages: Message[] }>(`/api/conversations/${encodeURIComponent(conversationId)}/invites`, {
      token,
      method: "POST",
      body: { invitees }
    });
  },
  acceptGroupInvite(token: string, inviteId: number) {
    return request<{ invite: GroupInvite }>(`/api/groups/invites/${inviteId}/accept`, {
      token,
      method: "POST"
    });
  },
  rejectGroupInvite(token: string, inviteId: number) {
    return request<{ invite: GroupInvite }>(`/api/groups/invites/${inviteId}/reject`, {
      token,
      method: "POST"
    });
  },
  updateGroup(token: string, conversationId: string, payload: { title?: string }) {
    return request<{ conversation: Conversation }>(`/api/conversations/${encodeURIComponent(conversationId)}`, {
      token,
      method: "PATCH",
      body: payload
    });
  },
  updateGroupAlias(token: string, conversationId: string, alias: string) {
    return request<{ conversation: Conversation }>(`/api/conversations/${encodeURIComponent(conversationId)}/me`, {
      token,
      method: "PATCH",
      body: { alias }
    });
  },
  kickGroupMember(token: string, conversationId: string, member: string) {
    return request<{ status: string; conversation: Conversation }>(
      `/api/conversations/${encodeURIComponent(conversationId)}/members/${encodeURIComponent(member)}`,
      { token, method: "DELETE" }
    );
  },
  requestFriend(token: string, receiver: string) {
    return request<{ status: string }>("/api/friends/requests", {
      token,
      method: "POST",
      body: { receiver }
    });
  },
  acceptFriend(token: string, requester: string) {
    return request<{ status: string }>(`/api/friends/requests/${requester}/accept`, {
      token,
      method: "POST"
    });
  },
  rejectFriend(token: string, requester: string) {
    return request<{ status: string }>(`/api/friends/requests/${requester}/reject`, {
      token,
      method: "POST"
    });
  },
  deleteFriend(token: string, friend: string) {
    return request<{ status: string }>(`/api/friends/${friend}`, {
      token,
      method: "DELETE"
    });
  },
  updateFriend(token: string, friend: string, payload: { alias?: string; tags?: string[] }) {
    return request<{ friend: User }>(`/api/friends/${friend}`, {
      token,
      method: "PATCH",
      body: payload
    });
  },
  messages(token: string, peer: string) {
    return request<{ messages: Message[] }>(`/api/conversations/${peer}/messages`, { token });
  },
  conversationMessages(token: string, conversationId: string) {
    return request<{ messages: Message[] }>(`/api/conversations/by-id/${encodeURIComponent(conversationId)}/messages`, { token });
  },
  sendConversationMessage(token: string, conversationId: string, body: string) {
    return request<{ message: Message }>(`/api/conversations/by-id/${encodeURIComponent(conversationId)}/messages`, {
      token,
      method: "POST",
      body: { message_type: "text", body }
    });
  },
  sendMessage(token: string, peer: string, body: string) {
    return request<{ message: Message }>(`/api/conversations/${peer}/messages`, {
      token,
      method: "POST",
      body: { message_type: "text", body }
    });
  },
  uploadAttachment(token: string, peer: string, file: File) {
    const body = new FormData();
    body.append("file", file);
    return request<{ message: Message }>(`/api/conversations/${peer}/attachments`, {
      token,
      method: "POST",
      body
    });
  },
  uploadConversationAttachment(token: string, conversationId: string, file: File) {
    const body = new FormData();
    body.append("file", file);
    return request<{ message: Message }>(`/api/conversations/by-id/${encodeURIComponent(conversationId)}/attachments`, {
      token,
      method: "POST",
      body
    });
  }
};
