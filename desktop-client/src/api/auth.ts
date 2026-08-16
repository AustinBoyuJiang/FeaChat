import { request } from "./client";
import type { User } from "../types";

export function register(payload: { number: string; password: string; email: string; nickname?: string }) {
  return request<{ user: User }>("/api/auth/register", { method: "POST", body: payload });
}

export function login(payload: { number: string; password: string }) {
  return request<{ token: string; user: User }>("/api/auth/login", { method: "POST", body: payload });
}
