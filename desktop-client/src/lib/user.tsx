import { fileUrl } from "../api/client";
import type { Conversation, User } from "../types";

export function displayName(user: User) {
  return user.display_name || user.alias || user.nickname || user.number;
}

function letterAvatarSrc(label: string, color = "#0076f6") {
  const letter = (label.trim().charAt(0) || "?").toUpperCase();
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="96" height="96" viewBox="0 0 96 96"><rect width="96" height="96" rx="12" fill="${color}"/><text x="48" y="58" text-anchor="middle" font-family="-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif" font-size="42" font-weight="700" fill="#fff">${letter}</text></svg>`;
  return `data:image/svg+xml;charset=utf-8,${encodeURIComponent(svg)}`;
}

export function userAvatarSrc(user: User) {
  return user.avatar_url ? fileUrl(user.avatar_url) : letterAvatarSrc(displayName(user), user.avatar_color || "#0076f6");
}

export function groupTitle(conversation: Conversation) {
  return conversation.title || conversation.members.map((member) => displayName(member)).join(", ") || "Group Chat";
}

export function conversationTitle(conversation: Conversation) {
  return conversation.type === "group" ? groupTitle(conversation) : conversation.peer ? displayName(conversation.peer) : conversation.title;
}

export function UserAvatar({ user, className = "avatar small" }: { user: User; className?: string }) {
  return <img className={className} src={userAvatarSrc(user)} alt="" draggable={false} />;
}

export function GroupAvatar({ conversation, className = "avatar small group-avatar" }: { conversation: Conversation; className?: string }) {
  const members = conversation.members.slice(0, 9);
  const gridSize = members.length <= 1 ? 1 : members.length <= 4 ? 4 : 9;
  return (
    <span className={`${className} group-avatar-count-${gridSize}`} aria-hidden="true">
      {members.map((member) => (
        <img key={member.number} src={userAvatarSrc(member)} alt="" draggable={false} />
      ))}
    </span>
  );
}

export function genderMarker(user: User) {
  if (user.gender === "female") {
    return { label: "Female", symbol: "♀", className: "female" };
  }
  if (user.gender === "male") {
    return { label: "Male", symbol: "♂", className: "male" };
  }
  return null;
}

export function contactGroupKey(user: User) {
  const first = displayName(user).trim().charAt(0).toUpperCase();
  return /^[A-Z]$/.test(first) ? first : "Others";
}
