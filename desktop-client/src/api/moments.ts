import { request } from "./client";
import type { MomentNotification, MomentPost, MomentProfileSummary } from "../types";

export function moments(token: string) {
  return request<{ moments: MomentPost[] }>("/api/moments", { token });
}

export function userMoments(token: string, userNumber: string) {
  return request<{ moments: MomentPost[] }>(`/api/moments/users/${encodeURIComponent(userNumber)}`, { token });
}

export function momentProfileSummary(token: string, userNumber: string) {
  return request<MomentProfileSummary>(`/api/moments/users/${encodeURIComponent(userNumber)}/summary`, { token });
}

export function momentNotifications(token: string) {
  return request<{ notifications: MomentNotification[]; unread_count: number }>("/api/moments/notifications", { token });
}

export function markMomentNotificationsRead(token: string) {
  return request<{ unread_count: number }>("/api/moments/notifications/read", {
    token,
    method: "POST"
  });
}

export function createMoment(token: string, bodyText: string, files: File[]) {
  const body = new FormData();
  body.append("body", bodyText);
  for (const file of files) {
    body.append("files", file);
  }
  return request<{ moment: MomentPost }>("/api/moments", {
    token,
    method: "POST",
    body
  });
}

export function deleteMoment(token: string, postId: number) {
  return request<{ status: string; post_id: number }>(`/api/moments/${postId}`, {
    token,
    method: "DELETE"
  });
}

export function likeMoment(token: string, postId: number) {
  return request<{ moment: MomentPost }>(`/api/moments/${postId}/like`, {
    token,
    method: "POST"
  });
}

export function unlikeMoment(token: string, postId: number) {
  return request<{ moment: MomentPost }>(`/api/moments/${postId}/like`, {
    token,
    method: "DELETE"
  });
}

export function commentMoment(token: string, postId: number, body: string) {
  return request<{ moment: MomentPost }>(`/api/moments/${postId}/comments`, {
    token,
    method: "POST",
    body: { body }
  });
}
