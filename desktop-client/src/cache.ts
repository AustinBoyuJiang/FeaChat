import type { Message } from "./types";

export type Theme = "classic" | "dark";

type CachedConversation = {
  messages: Message[];
  updatedAt: string;
  clearedAt?: string;
};

type UserCache = {
  version: 1;
  theme: Theme;
  conversations: Record<string, CachedConversation>;
};

const MAX_CACHED_MESSAGES = 200;

function cacheKey(number: string) {
  return `feachat.cache.${number}`;
}

function emptyCache(): UserCache {
  return {
    version: 1,
    theme: "classic",
    conversations: {}
  };
}

function normalizeCache(value: unknown): UserCache {
  if (!value || typeof value !== "object") {
    return emptyCache();
  }
  const candidate = value as Partial<UserCache>;
  return {
    version: 1,
    theme: candidate.theme === "dark" ? "dark" : "classic",
    conversations: candidate.conversations && typeof candidate.conversations === "object" ? candidate.conversations : {}
  };
}

export function readUserCache(number: string): UserCache {
  const raw = localStorage.getItem(cacheKey(number));
  if (!raw) {
    const legacyTheme = localStorage.getItem(`feachat.theme.${number}`);
    return { ...emptyCache(), theme: legacyTheme === "dark" ? "dark" : "classic" };
  }
  try {
    return normalizeCache(JSON.parse(raw));
  } catch {
    return emptyCache();
  }
}

function writeUserCache(number: string, cache: UserCache) {
  localStorage.setItem(cacheKey(number), JSON.stringify(cache));
}

export function updateUserCache(number: string, updater: (cache: UserCache) => UserCache) {
  writeUserCache(number, updater(readUserCache(number)));
}

export function readTheme(number: string): Theme {
  return readUserCache(number).theme;
}

export function writeTheme(number: string, theme: Theme) {
  updateUserCache(number, (cache) => ({ ...cache, theme }));
  localStorage.removeItem(`feachat.theme.${number}`);
}

export function readCachedMessages(number: string, peer: string) {
  const conversation = readUserCache(number).conversations[peer];
  if (!conversation) {
    return [];
  }
  return filterClearedMessages(conversation.messages, conversation.clearedAt);
}

export function writeCachedMessages(number: string, peer: string, messages: Message[]) {
  const current = readUserCache(number).conversations[peer];
  const nextMessages = filterClearedMessages(uniqueMessages(messages), current?.clearedAt).slice(-MAX_CACHED_MESSAGES);
  updateUserCache(number, (cache) => ({
    ...cache,
    conversations: {
      ...cache.conversations,
      [peer]: {
        messages: nextMessages,
        updatedAt: new Date().toISOString(),
        clearedAt: current?.clearedAt
      }
    }
  }));
}

export function mergeCachedMessages(number: string, peer: string, messages: Message[]) {
  const cached = readCachedMessages(number, peer);
  writeCachedMessages(number, peer, [...cached, ...messages]);
}

export function clearCachedMessages(number: string, peer: string) {
  updateUserCache(number, (cache) => ({
    ...cache,
    conversations: {
      ...cache.conversations,
      [peer]: {
        messages: [],
        updatedAt: new Date().toISOString(),
        clearedAt: new Date().toISOString()
      }
    }
  }));
}

export function filterClearedMessages(messages: Message[], clearedAt?: string) {
  if (!clearedAt) {
    return messages;
  }
  const clearedTime = new Date(clearedAt).getTime();
  return messages.filter((message) => parseUtcMessageTime(message.time).getTime() > clearedTime);
}

function uniqueMessages(messages: Message[]) {
  const seen = new Set<number>();
  return messages.filter((message) => {
    if (seen.has(message.id)) {
      return false;
    }
    seen.add(message.id);
    return true;
  });
}

function parseUtcMessageTime(value: string) {
  const normalized = value.includes("T") ? value : value.replace(" ", "T");
  const withZone = /(?:Z|[+-]\d{2}:?\d{2})$/i.test(normalized) ? normalized : `${normalized}Z`;
  const date = new Date(withZone);
  return Number.isNaN(date.getTime()) ? new Date(0) : date;
}
