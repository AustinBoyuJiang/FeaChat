import type { Message } from "../types";

export const MESSAGE_TIME_GAP_SECONDS = 300;
export type CallMessagePayload = {
  mode: "voice" | "video";
  outcome: "ended" | "canceled" | "declined";
  duration_seconds?: number | null;
};
export type GroupInviteAvatarMember = {
  number: string;
  nickname: string;
  display_name?: string;
  avatar_url?: string | null;
  avatar_color?: string | null;
};
export type GroupInvitePayload = {
  invite_id: number;
  conversation_id: string;
  title: string;
  inviter: string;
  avatar_members?: GroupInviteAvatarMember[];
};

export function uniqueMessages(messages: Message[]) {
  const seen = new Set<number>();
  return messages.filter((message) => {
    if (seen.has(message.id)) {
      return false;
    }
    seen.add(message.id);
    return true;
  });
}

export function parseMessageTime(value: string) {
  const normalized = value.includes("T") ? value : value.replace(" ", "T");
  const withZone = /(?:Z|[+-]\d{2}:?\d{2})$/i.test(normalized) ? normalized : `${normalized}Z`;
  const date = new Date(withZone);
  return Number.isNaN(date.getTime()) ? new Date() : date;
}

function startOfDay(date: Date) {
  return new Date(date.getFullYear(), date.getMonth(), date.getDate());
}

function startOfWeek(date: Date) {
  const day = date.getDay() || 7;
  const weekStart = startOfDay(date);
  weekStart.setDate(weekStart.getDate() - day + 1);
  return weekStart;
}

function formatClock(date: Date) {
  return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

export function formatMessageTimestamp(value: string) {
  const date = parseMessageTime(value);
  const now = new Date();
  const today = startOfDay(now);
  const target = startOfDay(date);
  const dayDiff = Math.round((today.getTime() - target.getTime()) / 86_400_000);
  const clock = formatClock(date);

  if (dayDiff === 0) {
    return clock;
  }
  if (dayDiff === 1) {
    return `Yesterday ${clock}`;
  }
  if (dayDiff > 1 && startOfWeek(date).getTime() === startOfWeek(now).getTime()) {
    return `${date.toLocaleDateString([], { weekday: "long" })} ${clock}`;
  }
  if (date.getFullYear() === now.getFullYear()) {
    return `${date.getMonth() + 1}/${date.getDate()} ${clock}`;
  }
  return `${date.getFullYear()}/${date.getMonth() + 1}/${date.getDate()} ${clock}`;
}

export function shouldShowTimestamp(messages: Message[], index: number) {
  if (index === 0) {
    return true;
  }
  const current = parseMessageTime(messages[index].time).getTime();
  const previous = parseMessageTime(messages[index - 1].time).getTime();
  return current - previous >= MESSAGE_TIME_GAP_SECONDS * 1000;
}

export function sortMessages(messages: Message[]) {
  return [...messages].sort((a, b) => {
    const byTime = parseMessageTime(a.time).getTime() - parseMessageTime(b.time).getTime();
    return byTime === 0 ? a.id - b.id : byTime;
  });
}

export function formatBytes(size: number) {
  if (size < 1024) {
    return `${size} B`;
  }
  if (size < 1024 * 1024) {
    return `${(size / 1024).toFixed(1)} KB`;
  }
  return `${(size / 1024 / 1024).toFixed(1)} MB`;
}

export function messagePreview(message: Message) {
  if (message.type === "system") {
    return message.message || "[System]";
  }
  if (message.type === "group_invite") {
    const invite = parseGroupInviteMessage(message);
    return invite?.title ? `[Group Invite] ${invite.title}` : "[Group Invite]";
  }
  if (message.type === "call") {
    return formatCallMessage(message);
  }
  if (message.attachment) {
    const attachmentName = message.attachment.name.trim();
    if (isAudioMessage(message)) {
      const duration = voiceDurationLabel(message);
      return duration ? `[Audio] ${duration}` : attachmentName ? `[Audio] ${attachmentName}` : "[Audio]";
    }
    if (isImageMessage(message)) {
      return attachmentName ? `[Image] ${attachmentName}` : "[Image]";
    }
    if (isVideoMessage(message)) {
      return attachmentName ? `[Video] ${attachmentName}` : "[Video]";
    }
    return attachmentName ? `[File] ${attachmentName}` : "[File]";
  }
  const messageText = message.message.trim();
  if (isAudioMessage(message)) {
    const duration = voiceDurationLabel(message);
    return duration ? `[Audio] ${duration}` : messageText ? `[Audio] ${messageText}` : "[Audio]";
  }
  if (isImageMessage(message)) {
    return messageText ? `[Image] ${messageText}` : "[Image]";
  }
  if (isVideoMessage(message)) {
    return messageText ? `[Video] ${messageText}` : "[Video]";
  }
  if (message.type === "file") {
    return messageText ? `[File] ${messageText}` : "[File]";
  }
  return message.message || "[Message]";
}

function formatCallDuration(seconds: number) {
  const safeSeconds = Math.max(0, Math.floor(seconds));
  const minutes = Math.floor(safeSeconds / 60);
  const rest = safeSeconds % 60;
  return `${minutes}:${rest.toString().padStart(2, "0")}`;
}

export function parseCallMessage(message: Message) {
  if (message.type !== "call") {
    return null;
  }
  try {
    const payload = JSON.parse(message.message) as CallMessagePayload;
    if (payload.mode !== "voice" && payload.mode !== "video") {
      return null;
    }
    if (!["ended", "canceled", "declined"].includes(payload.outcome)) {
      return null;
    }
    return payload;
  } catch {
    return null;
  }
}

export function formatCallMessage(message: Message) {
  const payload = parseCallMessage(message);
  if (!payload) {
    return message.message || "[Call]";
  }
  const label = payload.mode === "video" ? "Video call" : "Voice call";
  if (payload.outcome === "ended") {
    return `${label} ended${payload.duration_seconds ? ` ${formatCallDuration(payload.duration_seconds)}` : ""}`;
  }
  if (payload.outcome === "declined") {
    return `${label} declined`;
  }
  return `${label} canceled`;
}

export function parseGroupInviteMessage(message: Message) {
  if (message.type !== "group_invite") {
    return null;
  }
  try {
    return JSON.parse(message.message) as GroupInvitePayload;
  } catch {
    return null;
  }
}

export function isImageMessage(message: Message) {
  return message.type === "image" || message.attachment?.mime_type.startsWith("image/") || hasFileExtension(message, IMAGE_EXTENSIONS);
}

export function isAudioMessage(message: Message) {
  return (
    message.type === "audio" ||
    message.attachment?.mime_type.startsWith("audio/") ||
    hasFileExtension(message, AUDIO_EXTENSIONS) ||
    /^voice message\s+\d+s\./i.test(message.attachment?.name || message.message || "")
  );
}

export function isVideoMessage(message: Message) {
  return message.type === "video" || message.attachment?.mime_type.startsWith("video/") || hasFileExtension(message, VIDEO_EXTENSIONS);
}

export function voiceDurationLabel(message: Message) {
  const filename = message.attachment?.name || message.message || "";
  const match = filename.match(/Voice message\s+(\d+)s/i);
  if (!match) {
    return "";
  }
  return `${match[1]}"`;
}

const IMAGE_EXTENSIONS = [".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".heic", ".heif", ".tiff"];
const AUDIO_EXTENSIONS = [".m4a", ".mp3", ".wav", ".aac", ".ogg", ".opus", ".flac"];
const VIDEO_EXTENSIONS = [".mp4", ".mov", ".webm", ".m4v", ".avi", ".mkv"];

function hasFileExtension(message: Message, extensions: string[]) {
  const name = (message.attachment?.name || message.message || "").toLowerCase();
  return extensions.some((extension) => name.endsWith(extension));
}
