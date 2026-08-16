import { request } from "./client";
import type { FriendRequest, FriendRequestRecord, User } from "../types";

export function searchUsers(token: string, query: string) {
  return request<{ users: User[] }>(`/api/users/search?q=${encodeURIComponent(query)}`, { token });
}

export function friends(token: string) {
  return request<{ friends: User[] }>("/api/friends", { token });
}

export function friendRequests(token: string) {
  return request<{ requests: FriendRequest[] }>("/api/friends/requests", { token });
}

export function friendRequestHistory(token: string) {
  return request<{ requests: FriendRequestRecord[] }>("/api/friends/requests/history", { token });
}

export function requestFriend(token: string, receiver: string) {
  return request<{ status: string }>("/api/friends/requests", {
    token,
    method: "POST",
    body: { receiver }
  });
}

export function acceptFriend(token: string, requester: string) {
  return request<{ status: string }>(`/api/friends/requests/${requester}/accept`, {
    token,
    method: "POST"
  });
}

export function rejectFriend(token: string, requester: string) {
  return request<{ status: string }>(`/api/friends/requests/${requester}/reject`, {
    token,
    method: "POST"
  });
}

export function deleteFriend(token: string, friend: string) {
  return request<{ status: string }>(`/api/friends/${friend}`, {
    token,
    method: "DELETE"
  });
}

export function updateFriend(token: string, friend: string, payload: { alias?: string; tags?: string[] }) {
  return request<{ friend: User }>(`/api/friends/${friend}`, {
    token,
    method: "PATCH",
    body: payload
  });
}
