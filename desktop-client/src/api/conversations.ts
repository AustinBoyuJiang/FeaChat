import { request } from "./client";
import type { Conversation, GroupInvite, Message } from "../types";

export function conversations(token: string) {
  return request<{ conversations: Conversation[] }>("/api/conversations", { token });
}

export function groupInvites(token: string) {
  return request<{ invites: GroupInvite[] }>("/api/groups/invites", { token });
}

export function createGroup(token: string, payload: { title: string; members: string[] }) {
  return request<{ conversation: Conversation; invites: GroupInvite[]; messages: Message[] }>("/api/groups", {
    token,
    method: "POST",
    body: payload
  });
}

export function inviteToGroup(token: string, conversationId: string, invitees: string[]) {
  return request<{ invites: GroupInvite[]; messages: Message[] }>(`/api/conversations/${encodeURIComponent(conversationId)}/invites`, {
    token,
    method: "POST",
    body: { invitees }
  });
}

export function acceptGroupInvite(token: string, inviteId: number) {
  return request<{ invite: GroupInvite }>(`/api/groups/invites/${inviteId}/accept`, {
    token,
    method: "POST"
  });
}

export function rejectGroupInvite(token: string, inviteId: number) {
  return request<{ invite: GroupInvite }>(`/api/groups/invites/${inviteId}/reject`, {
    token,
    method: "POST"
  });
}

export function updateGroup(token: string, conversationId: string, payload: { title?: string }) {
  return request<{ conversation: Conversation }>(`/api/conversations/${encodeURIComponent(conversationId)}`, {
    token,
    method: "PATCH",
    body: payload
  });
}

export function updateGroupAlias(token: string, conversationId: string, alias: string) {
  return request<{ conversation: Conversation }>(`/api/conversations/${encodeURIComponent(conversationId)}/me`, {
    token,
    method: "PATCH",
    body: { alias }
  });
}

export function kickGroupMember(token: string, conversationId: string, member: string) {
  return request<{ status: string; conversation: Conversation }>(
    `/api/conversations/${encodeURIComponent(conversationId)}/members/${encodeURIComponent(member)}`,
    { token, method: "DELETE" }
  );
}

export function messages(token: string, peer: string) {
  return request<{ messages: Message[] }>(`/api/conversations/${peer}/messages`, { token });
}

export function conversationMessages(token: string, conversationId: string) {
  return request<{ messages: Message[] }>(`/api/conversations/by-id/${encodeURIComponent(conversationId)}/messages`, { token });
}

export function sendConversationMessage(token: string, conversationId: string, body: string, messageType = "text") {
  return request<{ message: Message }>(`/api/conversations/by-id/${encodeURIComponent(conversationId)}/messages`, {
    token,
    method: "POST",
    body: { message_type: messageType, body }
  });
}

export function sendMessage(token: string, peer: string, body: string, messageType = "text") {
  return request<{ message: Message }>(`/api/conversations/${peer}/messages`, {
    token,
    method: "POST",
    body: { message_type: messageType, body }
  });
}

export function uploadAttachment(token: string, peer: string, file: File) {
  const body = new FormData();
  body.append("file", file);
  return request<{ message: Message }>(`/api/conversations/${peer}/attachments`, {
    token,
    method: "POST",
    body
  });
}

export function uploadConversationAttachment(token: string, conversationId: string, file: File) {
  const body = new FormData();
  body.append("file", file);
  return request<{ message: Message }>(`/api/conversations/by-id/${encodeURIComponent(conversationId)}/attachments`, {
    token,
    method: "POST",
    body
  });
}

export function transcribeMessage(token: string, messageId: number) {
  return request<{ text: string; model: string }>(`/api/messages/${messageId}/transcription`, {
    token,
    method: "POST"
  });
}
