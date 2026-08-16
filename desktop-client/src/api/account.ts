import { request } from "./client";
import type { User } from "../types";

export function me(token: string) {
  return request<{ user: User }>("/api/me", { token });
}

export function updateMe(token: string, payload: { nickname?: string; motto?: string; current_password?: string; new_password?: string }) {
  return request<{ user: User }>("/api/me", {
    token,
    method: "PATCH",
    body: payload
  });
}

export function uploadAvatar(token: string, file: File) {
  const body = new FormData();
  body.append("file", file);
  return request<{ user: User }>("/api/me/avatar", {
    token,
    method: "POST",
    body
  });
}
