import { ChangeEvent, FormEvent, Fragment, MouseEvent, useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  Aperture,
  Check,
  CircleUserRound,
  Copy,
  Download,
  FileText,
  Image as ImageIcon,
  Menu,
  LogOut,
  Mic,
  MessageCircle,
  MessageSquare,
  Minus,
  MoreHorizontal,
  Paperclip,
  Pencil,
  Phone,
  PhoneOff,
  Pin,
  PinOff,
  Plus,
  Search,
  Send,
  Settings,
  Smile,
  Square,
  Trash2,
  UserPlus,
  Video,
  X
} from "lucide-react";

import { api } from "./api";
import {
  clearCachedMessages,
  mergeCachedMessages,
  readMutedPeers,
  readCachedMessages,
  readPinnedChatKeys,
  readUnreadCounts,
  readTheme,
  writeCachedMessages,
  writeMutedPeers,
  writePinnedChatKeys,
  writeUnreadCounts,
  writeTheme,
  type Theme
} from "./cache";
import { WindowControls } from "./components/WindowControls";
import {
  formatBytes,
  formatCallMessage,
  formatMessageTimestamp,
  isAudioMessage,
  isImageMessage,
  isVideoMessage,
  messagePreview,
  parseCallMessage,
  parseMessageTime,
  parseGroupInviteMessage,
  sortMessages,
  shouldShowTimestamp,
  uniqueMessages,
  voiceDurationLabel
} from "./lib/messages";
import { setDockUnreadBadge } from "./lib/dockBadge";
import { playIncomingMessageSound, startIncomingCallRingtone, stopIncomingCallRingtone } from "./lib/sounds";
import { startWindowDrag, toggleMaximizeFromDragArea } from "./lib/window";
import {
  contactGroupKey,
  conversationTitle,
  displayName,
  genderMarker,
  GroupAvatar,
  groupTitle,
  UserAvatar,
  userAvatarSrc
} from "./lib/user";
import type { Conversation, FriendRequest, FriendRequestRecord, GroupInvite, Message, User } from "./types";

type AuthMode = "login" | "register";
type Section = "chats" | "contacts" | "newFriends" | "moments";
type ProfileRelation = "self" | "friend" | "stranger";
type ContactPickerMode = "createGroup" | "inviteGroup" | "kickGroup";
type InlineEditTarget = "profileAlias" | "profileTags" | "groupAlias" | "groupName";
type SettingsSection = "account" | "appearance";
type ChatListItem = { kind: "group"; conversation: Conversation } | { kind: "direct"; friend: User };
type ChatContextMenuState = {
  key: string;
  title: string;
  x: number;
  y: number;
} | null;
type MessageContextMenuState = {
  message: Message;
  x: number;
  y: number;
} | null;
type ConfirmDialogState = {
  title: string;
  body: string;
  confirmLabel: string;
  destructive?: boolean;
  onConfirm: () => void;
} | null;
type CallMode = "voice" | "video";
type CallSignal =
  | { kind: "offer"; mode: CallMode; description: RTCSessionDescriptionInit }
  | { kind: "answer"; description: RTCSessionDescriptionInit }
  | { kind: "ice"; candidate: RTCIceCandidateInit }
  | { kind: "end" }
  | { kind: "reject" };
type CallState =
  | { status: "idle" }
  | { status: "incoming"; mode: CallMode; peerNumber: string; peerName: string; conversationId?: string }
  | { status: "outgoing" | "connecting" | "active"; mode: CallMode; peerNumber: string; peerName: string; conversationId?: string };
type RecordingState = "idle" | "recording" | "stopping";

type ProfileCardState = {
  user: User;
  x: number;
  y: number;
  canDelete: boolean;
  relation: ProfileRelation;
} | null;

const params = new URLSearchParams(window.location.search);
const initialNumber = params.get("number") ?? "alice1";
const initialPassword = params.get("password") ?? "secret1";
const initialNickname = params.get("nickname") ?? (initialNumber === "bob001" ? "Bob" : "Alice");
const initialEmail = params.get("email") ?? `${initialNumber}@example.com`;
const noTextAssist = {
  autoCapitalize: "none",
  autoCorrect: "off",
  spellCheck: false
} as const;
const LEGACY_CACHE_BRIDGE_URL = "http://127.0.0.1:1420/legacy-cache-bridge.html";
const LEGACY_CACHE_ORIGIN = "http://127.0.0.1:1420";
const MAX_VOICE_RECORDING_SECONDS = 60;
const EMOJI_ITEMS = ["😀", "😂", "😊", "😍", "🥰", "😎", "😭", "😅", "🙃", "😴", "👍", "🙏", "👏", "💪", "🔥", "✨", "🎉", "❤️", "💙", "✅", "☕", "🍰", "🌙", "⭐"];
const KAOMOJI_ITEMS = ["(＾▽＾)", "(｡•̀ᴗ-)✧", "(╯°□°）╯", "¯\\_(ツ)_/¯", "(；′⌒`)", "(づ￣ ³￣)づ", "(｀・ω・´)", "(。-`ω´-)", "(╥﹏╥)", "ヽ(•‿•)ノ"];

function migrateLegacyLocalCache(onMigrated: () => void) {
  if (window.location.hostname !== "localhost") {
    return () => undefined;
  }
  const iframe = document.createElement("iframe");
  iframe.src = LEGACY_CACHE_BRIDGE_URL;
  iframe.title = "Legacy cache migration";
  iframe.style.display = "none";

  const cleanup = () => {
    window.removeEventListener("message", handleMessage);
    iframe.remove();
  };
  const timer = window.setTimeout(cleanup, 2500);
  function importLegacyValue(key: string, value: string | null) {
    if (value === null || !key.startsWith("feachat.")) {
      return false;
    }
    const currentValue = localStorage.getItem(key);
    if (key.startsWith("feachat.cache.") && currentValue) {
      try {
        const legacyCache = JSON.parse(value) as { theme?: Theme; conversations?: Record<string, unknown> };
        const currentCache = JSON.parse(currentValue) as { theme?: Theme; conversations?: Record<string, unknown> };
        localStorage.setItem(
          key,
          JSON.stringify({
            ...legacyCache,
            ...currentCache,
            theme: legacyCache.theme ?? currentCache.theme,
            conversations: {
              ...(legacyCache.conversations ?? {}),
              ...(currentCache.conversations ?? {})
            }
          })
        );
        return true;
      } catch {
        return false;
      }
    }
    if (key.startsWith("feachat.theme.")) {
      const number = key.replace("feachat.theme.", "");
      const cacheKey = `feachat.cache.${number}`;
      const cacheValue = localStorage.getItem(cacheKey);
      if (cacheValue && (value === "classic" || value === "dark")) {
        try {
          const cache = JSON.parse(cacheValue) as { theme?: Theme };
          localStorage.setItem(cacheKey, JSON.stringify({ ...cache, theme: value }));
          return true;
        } catch {
          return false;
        }
      }
    }
    if (currentValue !== null) {
      return false;
    }
    localStorage.setItem(key, value);
    return true;
  }

  function handleMessage(event: MessageEvent) {
    if (event.origin !== LEGACY_CACHE_ORIGIN) {
      return;
    }
    const data = event.data as { source?: string; values?: Record<string, string> };
    if (data.source !== "feachat-legacy-cache" || !data.values) {
      return;
    }
    let changed = false;
    for (const [key, value] of Object.entries(data.values)) {
      changed = importLegacyValue(key, value) || changed;
    }
    if (changed) {
      onMigrated();
    }
    window.clearTimeout(timer);
    cleanup();
  }

  window.addEventListener("message", handleMessage);
  document.body.appendChild(iframe);
  return () => {
    window.clearTimeout(timer);
    cleanup();
  };
}

export default function App() {
  const [mode, setMode] = useState<AuthMode>("login");
  const [token, setToken] = useState<string | null>(() => localStorage.getItem("feachat.token"));
  const [me, setMe] = useState<User | null>(() => {
    const raw = localStorage.getItem("feachat.user");
    return raw ? (JSON.parse(raw) as User) : null;
  });
  const [number, setNumber] = useState(initialNumber);
  const [password, setPassword] = useState(initialPassword);
  const [email, setEmail] = useState(initialEmail);
  const [nickname, setNickname] = useState(initialNickname);
  const [friends, setFriends] = useState<User[]>([]);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [groupInvites, setGroupInvites] = useState<GroupInvite[]>([]);
  const [requests, setRequests] = useState<FriendRequest[]>([]);
  const [requestHistory, setRequestHistory] = useState<FriendRequestRecord[]>([]);
  const [selected, setSelected] = useState<User | null>(null);
  const [selectedGroup, setSelectedGroup] = useState<Conversation | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [draft, setDraft] = useState("");
  const [query, setQuery] = useState("");
  const [addFriendOpen, setAddFriendOpen] = useState(false);
  const [addQuery, setAddQuery] = useState("");
  const [addSearchResults, setAddSearchResults] = useState<User[]>([]);
  const [addMenuOpen, setAddMenuOpen] = useState(false);
  const [contactPickerMode, setContactPickerMode] = useState<ContactPickerMode | null>(null);
  const [contactPickerSearch, setContactPickerSearch] = useState("");
  const [pickedContacts, setPickedContacts] = useState<string[]>([]);
  const [groupAliasDraft, setGroupAliasDraft] = useState("");
  const [groupRenameDraft, setGroupRenameDraft] = useState("");
  const [inlineEdit, setInlineEdit] = useState<InlineEditTarget | null>(null);
  const [status, setStatus] = useState("");
  const [socketState, setSocketState] = useState("offline");
  const [activeSection, setActiveSection] = useState<Section>("chats");
  const [profileCard, setProfileCard] = useState<ProfileCardState>(null);
  const [profileMenuOpen, setProfileMenuOpen] = useState(false);
  const [profileAliasDraft, setProfileAliasDraft] = useState("");
  const [profileTagsDraft, setProfileTagsDraft] = useState("");
  const [profileStatus, setProfileStatus] = useState("");
  const [appMenuOpen, setAppMenuOpen] = useState(false);
  const [conversationMenuOpen, setConversationMenuOpen] = useState(false);
  const [callMenuOpen, setCallMenuOpen] = useState(false);
  const [callState, setCallState] = useState<CallState>({ status: "idle" });
  const [callMediaVersion, setCallMediaVersion] = useState(0);
  const [remoteStreams, setRemoteStreams] = useState<Record<string, MediaStream>>({});
  const [chatSearchOpen, setChatSearchOpen] = useState(false);
  const [chatSearchQuery, setChatSearchQuery] = useState("");
  const [mutedPeers, setMutedPeers] = useState<Set<string>>(() => (me ? readMutedPeers(me.number) : new Set()));
  const [unreadCounts, setUnreadCounts] = useState<Record<string, number>>(() => (me ? readUnreadCounts(me.number) : {}));
  const [pinnedChatKeys, setPinnedChatKeys] = useState<string[]>(() => (me ? readPinnedChatKeys(me.number) : []));
  const [chatContextMenu, setChatContextMenu] = useState<ChatContextMenuState>(null);
  const [messageContextMenu, setMessageContextMenu] = useState<MessageContextMenuState>(null);
  const [confirmDialog, setConfirmDialog] = useState<ConfirmDialogState>(null);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [settingsSection, setSettingsSection] = useState<SettingsSection>("account");
  const [accountNameDraft, setAccountNameDraft] = useState("");
  const [currentPasswordDraft, setCurrentPasswordDraft] = useState("");
  const [newPasswordDraft, setNewPasswordDraft] = useState("");
  const [confirmPasswordDraft, setConfirmPasswordDraft] = useState("");
  const [accountStatus, setAccountStatus] = useState("");
  const [accountError, setAccountError] = useState("");
  const [theme, setTheme] = useState<Theme>("classic");
  const [uploading, setUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState("");
  const [uploadError, setUploadError] = useState("");
  const [pendingFiles, setPendingFiles] = useState<File[]>([]);
  const [emojiPickerOpen, setEmojiPickerOpen] = useState(false);
  const [recordingState, setRecordingState] = useState<RecordingState>("idle");
  const [recordingSeconds, setRecordingSeconds] = useState(0);
  const [playingAudioId, setPlayingAudioId] = useState<number | null>(null);
  const [transcribingMessageId, setTranscribingMessageId] = useState<number | null>(null);
  const [transcriptions, setTranscriptions] = useState<Record<number, string>>({});
  const [transcriptionErrors, setTranscriptionErrors] = useState<Record<number, string>>({});
  const [previewMessages, setPreviewMessages] = useState<Record<string, Message>>({});
  const wsRef = useRef<WebSocket | null>(null);
  const bottomRef = useRef<HTMLDivElement | null>(null);
  const scrollBehaviorRef = useRef<ScrollBehavior>("auto");
  const peerConnectionsRef = useRef<Record<string, RTCPeerConnection>>({});
  const localStreamRef = useRef<MediaStream | null>(null);
  const remoteStreamRef = useRef<MediaStream | null>(null);
  const callStateRef = useRef<CallState>({ status: "idle" });
  const callStartedAtRef = useRef<number | null>(null);
  const callRingtoneStopRef = useRef<(() => void) | null>(null);
  const mutedPeersRef = useRef<Set<string>>(mutedPeers);
  const incomingOfferRef = useRef<RTCSessionDescriptionInit | null>(null);
  const pendingIceCandidatesRef = useRef<Record<string, RTCIceCandidateInit[]>>({});
  const localVideoRef = useRef<HTMLVideoElement | null>(null);
  const remoteVideoRef = useRef<HTMLVideoElement | null>(null);
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const avatarInputRef = useRef<HTMLInputElement | null>(null);
  const appMenuRef = useRef<HTMLDivElement | null>(null);
  const addMenuRef = useRef<HTMLDivElement | null>(null);
  const callMenuRef = useRef<HTMLDivElement | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const voiceChunksRef = useRef<Blob[]>([]);
  const voiceStartedAtRef = useRef<number | null>(null);
  const voiceTimerRef = useRef<number | null>(null);
  const voiceStreamRef = useRef<MediaStream | null>(null);
  const voicePlaybackUrlsRef = useRef<Record<number, string>>({});

  const selectedNumber = selected?.number;
  const selectedGroupId = selectedGroup?.id;

  function latestMessage(messages: Array<Message | null | undefined>) {
    return sortMessages(messages.filter((message): message is Message => Boolean(message))).at(-1) ?? null;
  }

  function replaceMessages(nextMessages: Message[], behavior: ScrollBehavior = "auto") {
    scrollBehaviorRef.current = behavior;
    setMessages(nextMessages);
  }

  function appendMessages(updater: (current: Message[]) => Message[], behavior: ScrollBehavior = "smooth") {
    scrollBehaviorRef.current = behavior;
    setMessages(updater);
  }

  function setPreviewMessage(key: string, message: Message | null) {
    setPreviewMessages((current) => {
      const next = { ...current };
      if (message) {
        next[key] = latestMessage([current[key], message]) ?? message;
      } else {
        delete next[key];
      }
      return next;
    });
  }

  function persistUnreadCounts(nextCounts: Record<string, number>) {
    if (me?.number) {
      writeUnreadCounts(me.number, nextCounts);
    }
  }

  function incrementUnreadCount(key: string) {
    setUnreadCounts((current) => {
      const next = { ...current, [key]: Math.min((current[key] ?? 0) + 1, 999) };
      persistUnreadCounts(next);
      return next;
    });
  }

  function clearUnreadCount(key: string) {
    setUnreadCounts((current) => {
      if (!current[key]) {
        return current;
      }
      const next = { ...current };
      delete next[key];
      persistUnreadCounts(next);
      return next;
    });
  }

  function persistPinnedChatKeys(nextKeys: string[]) {
    if (me?.number) {
      writePinnedChatKeys(me.number, nextKeys);
    }
  }

  function togglePinnedChat(key: string) {
    setPinnedChatKeys((current) => {
      const next = current.includes(key) ? current.filter((item) => item !== key) : [key, ...current];
      persistPinnedChatKeys(next);
      return next;
    });
    setChatContextMenu(null);
  }

  function unpinChat(key: string) {
    setPinnedChatKeys((current) => {
      if (!current.includes(key)) {
        return current;
      }
      const next = current.filter((item) => item !== key);
      persistPinnedChatKeys(next);
      return next;
    });
  }

  function clearLocalConversation(key: string) {
    if (!me) {
      return;
    }
    clearCachedMessages(me.number, key);
    setPreviewMessage(key, null);
    clearUnreadCount(key);
    unpinChat(key);
    if (selected?.number === key || selectedGroup?.id === key) {
      setSelected(null);
      setSelectedGroup(null);
      replaceMessages([], "auto");
    }
    setConversationMenuOpen(false);
    setChatContextMenu(null);
    setChatSearchQuery("");
    setChatSearchOpen(false);
  }

  function askToDeleteChat(key: string, title: string) {
    setChatContextMenu(null);
    setConfirmDialog({
      title: "Delete Chat",
      body: `Delete local chat history with ${title}? This only clears this device's cache.`,
      confirmLabel: "Delete",
      destructive: true,
      onConfirm: () => clearLocalConversation(key)
    });
  }

  function openChatContextMenu(event: MouseEvent<HTMLElement>, key: string, title: string) {
    event.preventDefault();
    event.stopPropagation();
    setConversationMenuOpen(false);
    setCallMenuOpen(false);
    setAddMenuOpen(false);
    setMessageContextMenu(null);
    setChatContextMenu({
      key,
      title,
      x: Math.min(event.clientX, window.innerWidth - 178),
      y: Math.min(event.clientY, window.innerHeight - 96)
    });
  }

  function openMessageContextMenu(event: MouseEvent<HTMLElement>, message: Message) {
    event.preventDefault();
    event.stopPropagation();
    setConversationMenuOpen(false);
    setCallMenuOpen(false);
    setChatContextMenu(null);
    setMessageContextMenu({
      message,
      x: Math.min(event.clientX, window.innerWidth - 184),
      y: Math.min(event.clientY, window.innerHeight - 132)
    });
  }

  async function copyMessageText(message: Message) {
    setMessageContextMenu(null);
    if (!message.message) {
      return;
    }
    try {
      await navigator.clipboard.writeText(message.message);
      setUploadStatus("Copied");
      setUploadError("");
    } catch {
      setUploadError("Copy failed");
    }
  }

  async function transcribeAudioMessage(message: Message) {
    if (!token || !isAudioMessage(message)) {
      return;
    }
    setMessageContextMenu(null);
    setTranscribingMessageId(message.id);
    setTranscriptionErrors((current) => {
      const next = { ...current };
      delete next[message.id];
      return next;
    });
    try {
      const response = await api.transcribeMessage(token, message.id);
      setTranscriptions((current) => ({ ...current, [message.id]: response.text || "No speech detected" }));
    } catch (error) {
      setTranscriptionErrors((current) => ({
        ...current,
        [message.id]: error instanceof Error ? error.message : "Transcription failed"
      }));
    } finally {
      setTranscribingMessageId(null);
    }
  }

  function askToClearSelectedConversation() {
    if ((!selected && !selectedGroup) || !me) {
      return;
    }
    const key = selectedGroup?.id ?? selected!.number;
    const title = selectedGroup ? groupTitle(selectedGroup) : displayName(selected!);
    setConversationMenuOpen(false);
    setConfirmDialog({
      title: "Clear Chat History",
      body: `Clear local chat history with ${title}? This only clears this device's cache.`,
      confirmLabel: "Clear",
      destructive: true,
      onConfirm: () => clearLocalConversation(key)
    });
  }

  function confirmDialogAction() {
    const action = confirmDialog?.onConfirm;
    setConfirmDialog(null);
    action?.();
  }

  function insertEmojiText(value: string) {
    const textarea = textareaRef.current;
    const start = textarea?.selectionStart ?? draft.length;
    const end = textarea?.selectionEnd ?? draft.length;
    const nextDraft = `${draft.slice(0, start)}${value}${draft.slice(end)}`;
    setDraft(nextDraft);
    window.setTimeout(() => {
      textarea?.focus();
      const nextCursor = start + value.length;
      textarea?.setSelectionRange(nextCursor, nextCursor);
    }, 0);
  }

  function supportedAudioMimeType() {
    const candidates = ["audio/mp4;codecs=mp4a.40.2", "audio/mp4", "audio/aac", "audio/webm;codecs=opus", "audio/webm"];
    if (!window.MediaRecorder) {
      return "";
    }
    const audio = document.createElement("audio");
    const playableAndRecordable = candidates.find((mimeType) => MediaRecorder.isTypeSupported(mimeType) && audio.canPlayType(mimeType));
    return playableAndRecordable ?? candidates.find((mimeType) => MediaRecorder.isTypeSupported(mimeType)) ?? "";
  }

  function voiceFileExtension(mimeType: string) {
    if (mimeType.includes("mp4") || mimeType.includes("aac")) {
      return "m4a";
    }
    if (mimeType.includes("ogg")) {
      return "ogg";
    }
    return "webm";
  }

  function stopVoiceTimer() {
    if (voiceTimerRef.current !== null) {
      window.clearInterval(voiceTimerRef.current);
      voiceTimerRef.current = null;
    }
  }

  function stopVoiceStream() {
    voiceStreamRef.current?.getTracks().forEach((track) => track.stop());
    voiceStreamRef.current = null;
  }

  function stopVoiceRecording() {
    if (recordingState !== "recording") {
      return;
    }
    setRecordingState("stopping");
    stopVoiceTimer();
    mediaRecorderRef.current?.stop();
  }

  async function startVoiceRecording() {
    if (!token || (!selected && !selectedGroup)) {
      setUploadError("Select a chat before recording voice");
      return;
    }
    if (!navigator.mediaDevices?.getUserMedia || !window.MediaRecorder) {
      setUploadError("Voice recording is unavailable in this window. Restart FeaChat from the updated Tauri app and allow microphone permission.");
      return;
    }
    setUploadError("");
    setUploadStatus("");
    setEmojiPickerOpen(false);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mimeType = supportedAudioMimeType();
      const recorder = new MediaRecorder(stream, mimeType ? { mimeType } : undefined);
      voiceChunksRef.current = [];
      voiceStartedAtRef.current = Date.now();
      voiceStreamRef.current = stream;
      mediaRecorderRef.current = recorder;
      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          voiceChunksRef.current.push(event.data);
        }
      };
      recorder.onstop = () => {
        stopVoiceTimer();
        stopVoiceStream();
        const elapsedSeconds = Math.max(1, Math.min(MAX_VOICE_RECORDING_SECONDS, Math.round(((Date.now() - (voiceStartedAtRef.current ?? Date.now())) / 1000))));
        const blobType = recorder.mimeType || mimeType || "audio/webm";
        const blob = new Blob(voiceChunksRef.current, { type: blobType });
        if (blob.size > 0) {
          const file = new File([blob], `Voice message ${elapsedSeconds}s.${voiceFileExtension(blobType)}`, { type: blobType });
          setPendingFiles((current) => [...current, file]);
        }
        voiceChunksRef.current = [];
        voiceStartedAtRef.current = null;
        mediaRecorderRef.current = null;
        setRecordingSeconds(0);
        setRecordingState("idle");
      };
      recorder.start();
      setRecordingSeconds(0);
      setRecordingState("recording");
      voiceTimerRef.current = window.setInterval(() => {
        const elapsedSeconds = Math.floor((Date.now() - (voiceStartedAtRef.current ?? Date.now())) / 1000);
        setRecordingSeconds(Math.min(MAX_VOICE_RECORDING_SECONDS, elapsedSeconds));
        if (elapsedSeconds >= MAX_VOICE_RECORDING_SECONDS) {
          stopVoiceTimer();
          mediaRecorderRef.current?.stop();
          setRecordingState("stopping");
        }
      }, 250);
    } catch (error) {
      stopVoiceTimer();
      stopVoiceStream();
      mediaRecorderRef.current = null;
      setRecordingState("idle");
      setRecordingSeconds(0);
      setUploadError(error instanceof Error ? error.message : "Could not start voice recording");
    }
  }

  function toggleVoiceRecording() {
    if (recordingState === "recording") {
      stopVoiceRecording();
    } else if (recordingState === "idle") {
      startVoiceRecording();
    }
  }

  async function playVoiceMessage(message: Message, audio: HTMLAudioElement) {
    if (!message.attachment) {
      return;
    }
    if (!audio.paused) {
      audio.pause();
      return;
    }
    document.querySelectorAll<HTMLAudioElement>(".voice-message audio").forEach((item) => {
      if (item !== audio) {
        item.pause();
      }
    });
    try {
      await audio.play();
      return;
    } catch {
      // Some macOS WebViews refuse direct HTTP media playback. A blob URL fallback keeps old voice messages usable.
    }
    try {
      let objectUrl = voicePlaybackUrlsRef.current[message.id];
      if (!objectUrl) {
        const response = await fetch(api.fileUrl(message.attachment.url));
        if (!response.ok) {
          throw new Error("Voice playback failed");
        }
        const blob = await response.blob();
        objectUrl = URL.createObjectURL(blob);
        voicePlaybackUrlsRef.current[message.id] = objectUrl;
      }
      audio.src = objectUrl;
      audio.load();
      await audio.play();
    } catch {
      setPlayingAudioId(null);
    }
  }

  function syncConversationPreviews(nextConversations: Conversation[], userNumber: string) {
    const previewEntries = new Map<string, Message | null>();
    for (const conversation of nextConversations) {
      const key = conversation.type === "group" ? conversation.id : conversation.peer?.number;
      if (!key) {
        continue;
      }
      if (conversation.last_message) {
        mergeCachedMessages(userNumber, key, [conversation.last_message]);
      }
      previewEntries.set(key, latestMessage(readCachedMessages(userNumber, key)));
    }
    setPreviewMessages((current) => {
      const next = { ...current };
      for (const [key, message] of previewEntries) {
        if (message) {
          next[key] = message;
        } else {
          delete next[key];
        }
      }
      return next;
    });
  }

  function clearTransientUi() {
    setStatus("");
    setQuery("");
    setAddFriendOpen(false);
    setAddMenuOpen(false);
    setCallMenuOpen(false);
    setAddQuery("");
    setAddSearchResults([]);
    setInlineEdit(null);
    setConversationMenuOpen(false);
    setChatContextMenu(null);
    setMessageContextMenu(null);
    setChatSearchOpen(false);
    setChatSearchQuery("");
    setEmojiPickerOpen(false);
  }

  async function loadContacts(activeToken = token, activeUserNumber = me?.number) {
    if (!activeToken) {
      return;
    }
    const [friendData, conversationData, requestData, historyData, groupInviteData] = await Promise.all([
      api.friends(activeToken),
      api.conversations(activeToken),
      api.friendRequests(activeToken),
      api.friendRequestHistory(activeToken),
      api.groupInvites(activeToken)
    ]);
    setFriends(friendData.friends);
    setConversations(conversationData.conversations);
    if (activeUserNumber) {
      syncConversationPreviews(conversationData.conversations, activeUserNumber);
    }
    setSelected((current) => friendData.friends.find((friend) => friend.number === current?.number) ?? current);
    setSelectedGroup((current) => conversationData.conversations.find((conversation) => conversation.id === current?.id) ?? current);
    setRequests(requestData.requests);
    setRequestHistory(historyData.requests);
    setGroupInvites(groupInviteData.invites);
  }

  async function loadMessages(peer: User) {
    if (!token || !me) {
      return;
    }
    setActiveSection("chats");
    clearTransientUi();
    setSelected(peer);
    setSelectedGroup(null);
    clearUnreadCount(peer.number);
    replaceMessages(readCachedMessages(me.number, peer.number), "auto");
    try {
      const response = await api.messages(token, peer.number);
      const nextMessages = uniqueMessages(response.messages);
      writeCachedMessages(me.number, peer.number, nextMessages);
      setPreviewMessage(peer.number, latestMessage(nextMessages));
      replaceMessages(readCachedMessages(me.number, peer.number), "auto");
    } catch (error) {
      if (error instanceof Error && error.message === "Not authenticated") {
        logout();
        return;
      }
      setStatus(error instanceof Error ? error.message : "Failed to load messages");
    }
  }

  async function loadGroupMessages(group: Conversation) {
    if (!token || !me) {
      return;
    }
    setActiveSection("chats");
    clearTransientUi();
    setSelected(null);
    setSelectedGroup(group);
    clearUnreadCount(group.id);
    setGroupAliasDraft(group.my_alias ?? "");
    setGroupRenameDraft(groupTitle(group));
    replaceMessages(readCachedMessages(me.number, group.id), "auto");
    try {
      const response = await api.conversationMessages(token, group.id);
      const nextMessages = uniqueMessages(response.messages);
      writeCachedMessages(me.number, group.id, nextMessages);
      setPreviewMessage(group.id, latestMessage(nextMessages));
      replaceMessages(readCachedMessages(me.number, group.id), "auto");
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Failed to load group messages");
    }
  }

  async function loginWithCredentials(credentials: {
    number: string;
    password: string;
    email: string;
    nickname: string;
    shouldRegister?: boolean;
  }) {
    setStatus("");
    try {
      if (credentials.shouldRegister) {
        await api.register(credentials).catch((error) => {
          if (error instanceof Error && error.message.includes("already exists")) {
            return;
          }
          throw error;
        });
      }
      const response = await api.login({
        number: credentials.number,
        password: credentials.password
      });
      setToken(response.token);
      setMe(response.user);
      localStorage.setItem("feachat.token", response.token);
      localStorage.setItem("feachat.user", JSON.stringify(response.user));
      await loadContacts(response.token, response.user.number);
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Authentication failed");
    }
  }

  async function authenticate(event: FormEvent) {
    event.preventDefault();
    await loginWithCredentials({
      number,
      password,
      email,
      nickname,
      shouldRegister: mode === "register"
    });
  }

  function logout() {
    wsRef.current?.close();
    localStorage.removeItem("feachat.token");
    localStorage.removeItem("feachat.user");
    setStatus("");
    setToken(null);
    setMe(null);
    setFriends([]);
    setConversations([]);
    setGroupInvites([]);
    setRequests([]);
    setRequestHistory([]);
    setSelected(null);
    setSelectedGroup(null);
    replaceMessages([], "auto");
    setAddFriendOpen(false);
    setAddQuery("");
    setAddSearchResults([]);
    setAddMenuOpen(false);
    setContactPickerMode(null);
    setPickedContacts([]);
    setContactPickerSearch("");
    setPendingFiles([]);
    setUploadStatus("");
    setUploadError("");
    setConversationMenuOpen(false);
    setChatContextMenu(null);
    setConfirmDialog(null);
    setPinnedChatKeys([]);
    setChatSearchOpen(false);
    setChatSearchQuery("");
  }

  function applyTheme(nextTheme: Theme) {
    if (!me) {
      return;
    }
    setTheme(nextTheme);
    writeTheme(me.number, nextTheme);
  }

  function storeMe(user: User) {
    setMe(user);
    localStorage.setItem("feachat.user", JSON.stringify(user));
    setProfileCard((current) => (current?.user.number === user.number ? { ...current, user } : current));
  }

  async function saveAccountSettings(event: FormEvent) {
    event.preventDefault();
    if (!token || !me) {
      return;
    }
    setAccountStatus("");
    setAccountError("");
    const payload: { nickname?: string; current_password?: string; new_password?: string } = {
      nickname: accountNameDraft.trim()
    };
    if (newPasswordDraft || currentPasswordDraft || confirmPasswordDraft) {
      if (newPasswordDraft !== confirmPasswordDraft) {
        setAccountError("Passwords do not match");
        return;
      }
      payload.current_password = currentPasswordDraft;
      payload.new_password = newPasswordDraft;
    }
    try {
      const response = await api.updateMe(token, payload);
      storeMe(response.user);
      setAccountNameDraft(response.user.nickname || response.user.number);
      setCurrentPasswordDraft("");
      setNewPasswordDraft("");
      setConfirmPasswordDraft("");
      setAccountStatus("Saved");
      await loadContacts();
    } catch (error) {
      setAccountError(error instanceof Error ? error.message : "Failed to save account");
    }
  }

  async function uploadAccountAvatar(event: ChangeEvent<HTMLInputElement>) {
    const file = event.currentTarget.files?.[0];
    event.currentTarget.value = "";
    if (!token || !file) {
      return;
    }
    if (!file.type.startsWith("image/")) {
      setAccountError("Avatar must be an image");
      return;
    }
    setAccountStatus("");
    setAccountError("");
    try {
      const response = await api.uploadAvatar(token, file);
      storeMe(response.user);
      setAccountStatus("Avatar updated");
      await loadContacts();
    } catch (error) {
      setAccountError(error instanceof Error ? error.message : "Failed to upload avatar");
    }
  }

  async function searchPeople() {
    if (!token || !addQuery.trim()) {
      setAddSearchResults([]);
      return;
    }
    try {
      const response = await api.searchUsers(token, addQuery);
      setAddSearchResults(response.users);
      setStatus(response.users.length ? "" : "No matching users");
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Search failed");
    }
  }

  async function requestFriend(receiver: string) {
    if (!token) {
      return;
    }
    try {
      const response = await api.requestFriend(token, receiver);
      setStatus(response.status === "accepted" ? "Friend request accepted" : "Friend request sent");
      setAddSearchResults([]);
      setAddQuery("");
      setAddFriendOpen(false);
      setProfileCard(null);
      await loadContacts();
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Failed to send friend request");
    }
  }

  function openContactPicker(mode: ContactPickerMode) {
    setContactPickerMode(mode);
    setContactPickerSearch("");
    setPickedContacts([]);
    setAddMenuOpen(false);
    setAddFriendOpen(false);
  }

  function closeContactPicker() {
    setContactPickerMode(null);
    setContactPickerSearch("");
    setPickedContacts([]);
  }

  function togglePickedContact(number: string) {
    setPickedContacts((current) =>
      current.includes(number) ? current.filter((item) => item !== number) : [...current, number]
    );
  }

  async function confirmContactPicker() {
    if (!token || !contactPickerMode || pickedContacts.length === 0) {
      return;
    }
    try {
      if (contactPickerMode === "createGroup") {
        const response = await api.createGroup(token, { title: "", members: pickedContacts });
        await loadContacts();
        await loadGroupMessages(response.conversation);
      } else if (contactPickerMode === "inviteGroup" && selectedGroup) {
        await api.inviteToGroup(token, selectedGroup.id, pickedContacts);
        await loadContacts();
      } else if (contactPickerMode === "kickGroup" && selectedGroup) {
        let latest = selectedGroup;
        for (const member of pickedContacts) {
          const response = await api.kickGroupMember(token, selectedGroup.id, member);
          latest = response.conversation;
        }
        setSelectedGroup(latest);
        await loadContacts();
      }
      closeContactPicker();
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Failed to update group");
    }
  }

  async function acceptInvite(inviteId: number) {
    if (!token) {
      return;
    }
    try {
      await api.acceptGroupInvite(token, inviteId);
      await loadContacts();
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Failed to accept invite");
      await loadContacts();
    }
  }

  async function rejectInvite(inviteId: number) {
    if (!token) {
      return;
    }
    await api.rejectGroupInvite(token, inviteId);
    await loadContacts();
  }

  async function saveGroupAlias() {
    if (!token || !selectedGroup) {
      return;
    }
    const response = await api.updateGroupAlias(token, selectedGroup.id, groupAliasDraft);
    setSelectedGroup(response.conversation);
    setInlineEdit(null);
    await loadContacts();
  }

  async function renameGroup() {
    if (!token || !selectedGroup) {
      return;
    }
    const response = await api.updateGroup(token, selectedGroup.id, { title: groupRenameDraft });
    setSelectedGroup(response.conversation);
    setInlineEdit(null);
    await loadContacts();
  }

  async function acceptFriend(requester: string) {
    if (!token) {
      return;
    }
    await api.acceptFriend(token, requester);
    await loadContacts();
  }

  async function rejectFriend(requester: string) {
    if (!token) {
      return;
    }
    await api.rejectFriend(token, requester);
    await loadContacts();
  }

  async function deleteFriend(friend: string) {
    if (!token) {
      return;
    }
    await api.deleteFriend(token, friend);
    if (selected?.number === friend) {
      setSelected(null);
      replaceMessages([], "auto");
    }
    await loadContacts();
  }

  function openProfileCard(event: MouseEvent<HTMLElement>, user: User, canDelete = false) {
    event.stopPropagation();
    const rect = event.currentTarget.getBoundingClientRect();
    const relation: ProfileRelation =
      user.number === me?.number
        ? "self"
        : canDelete || friends.some((friend) => friend.number === user.number)
          ? "friend"
          : "stranger";
    setProfileMenuOpen(false);
    setInlineEdit(null);
    setProfileAliasDraft(user.alias ?? "");
    setProfileTagsDraft((user.tags ?? []).join(", "));
    setProfileStatus("");
    setProfileCard({
      user,
      canDelete: relation === "friend",
      relation,
      x: Math.max(12, Math.min(rect.right + 10, window.innerWidth - 340)),
      y: Math.max(12, Math.min(rect.top, window.innerHeight - 340))
    });
  }

  function messageFromProfile() {
    if (!profileCard || profileCard.relation !== "friend") {
      return;
    }
    const peer = friends.find((friend) => friend.number === profileCard.user.number) ?? profileCard.user;
    setProfileCard(null);
    loadMessages(peer);
  }

  async function deleteFromProfile() {
    if (!profileCard?.canDelete) {
      return;
    }
    await deleteFriend(profileCard.user.number);
    setProfileCard(null);
  }

  async function saveFriendProfile() {
    if (!token || !profileCard?.canDelete) {
      return;
    }
    const tags = profileTagsDraft
      .split(",")
      .map((tag) => tag.trim())
      .filter(Boolean);
    const response = await api.updateFriend(token, profileCard.user.number, {
      alias: profileAliasDraft,
      tags
    });
    setProfileCard((current) => (current ? { ...current, user: response.friend } : current));
    setSelected((current) => (current?.number === response.friend.number ? response.friend : current));
    setFriends((current) => current.map((friend) => (friend.number === response.friend.number ? response.friend : friend)));
    setProfileStatus("Saved");
    setProfileMenuOpen(false);
    setInlineEdit(null);
  }

  function clearConversation() {
    askToClearSelectedConversation();
  }

  function toggleMuteSelected() {
    if ((!selected && !selectedGroup) || !me) {
      return;
    }
    const muteKey = selectedGroup?.id ?? selected!.number;
    setMutedPeers((current) => {
      const next = new Set(current);
      if (next.has(muteKey)) {
        next.delete(muteKey);
      } else {
        next.add(muteKey);
      }
      writeMutedPeers(me.number, next);
      return next;
    });
  }

  function peerName(number: string) {
    if (me?.number === number) {
      return displayName(me);
    }
    return displayName(friends.find((friend) => friend.number === number) ?? ({ number, nickname: number } as User));
  }

  function callPeerUser() {
    if (callState.status === "idle") {
      return null;
    }
    return friends.find((friend) => friend.number === callState.peerNumber) ?? selected ?? null;
  }

  function sendCallSignal(receiver: string, signal: CallSignal, conversationId?: string) {
    if (wsRef.current?.readyState !== WebSocket.OPEN) {
      setStatus("Call signaling is offline");
      return false;
    }
    wsRef.current.send(JSON.stringify({ type: "call_signal", receiver, conversation_id: conversationId, signal }));
    return true;
  }

  function callDurationSeconds() {
    return callStartedAtRef.current ? Math.max(0, Math.round((Date.now() - callStartedAtRef.current) / 1000)) : null;
  }

  function markCallActive() {
    callStartedAtRef.current ??= Date.now();
    setCallState((current) => (current.status === "idle" ? current : { ...current, status: "active" }));
  }

  async function recordCallMessage(
    currentCall: Exclude<CallState, { status: "idle" }>,
    outcome: "ended" | "canceled" | "declined",
    durationSeconds: number | null = callDurationSeconds()
  ) {
    if (!token) {
      return;
    }
    const body = JSON.stringify({
      mode: currentCall.mode,
      outcome,
      duration_seconds: outcome === "ended" ? durationSeconds : null
    });
    const conversationId = currentCall.conversationId;
    const receiver = conversationId ? undefined : currentCall.peerNumber;
    const key = conversationId ?? receiver;
    if (!key) {
      return;
    }
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(
        JSON.stringify({
          type: "send_message",
          receiver,
          conversation_id: conversationId,
          message_type: "call",
          body
        })
      );
      return;
    }
    const response = conversationId
      ? await api.sendConversationMessage(token, conversationId, body, "call")
      : await api.sendMessage(token, receiver!, body, "call");
    setPreviewMessage(key, response.message);
    appendMessages((current) => {
      const nextMessages = uniqueMessages([...current, response.message]);
      if (me) {
        writeCachedMessages(me.number, key, nextMessages);
      }
      return nextMessages;
    });
  }

  function closeCallMedia() {
    callRingtoneStopRef.current?.();
    callRingtoneStopRef.current = null;
    Object.values(peerConnectionsRef.current).forEach((connection) => connection.close());
    peerConnectionsRef.current = {};
    localStreamRef.current?.getTracks().forEach((track) => track.stop());
    localStreamRef.current = null;
    remoteStreamRef.current = null;
    setRemoteStreams({});
    incomingOfferRef.current = null;
    pendingIceCandidatesRef.current = {};
    setCallMediaVersion((version) => version + 1);
  }

  function finishCall(notifyPeer = true) {
    const currentCall = callStateRef.current;
    const durationSeconds = callDurationSeconds();
    if (notifyPeer && currentCall.status !== "idle") {
      const outcome = currentCall.status === "active" ? "ended" : "canceled";
      sendCallSignal(currentCall.conversationId ? "" : currentCall.peerNumber, { kind: "end" }, currentCall.conversationId);
      void recordCallMessage(currentCall, outcome, durationSeconds);
    }
    closeCallMedia();
    callStartedAtRef.current = null;
    setCallState({ status: "idle" });
  }

  async function applyPendingIceCandidates(peerNumber: string) {
    const pc = peerConnectionsRef.current[peerNumber];
    if (!pc?.remoteDescription) {
      return;
    }
    const candidates = pendingIceCandidatesRef.current[peerNumber] ?? [];
    pendingIceCandidatesRef.current[peerNumber] = [];
    for (const candidate of candidates) {
      await pc.addIceCandidate(candidate).catch(() => undefined);
    }
  }

  async function ensureLocalStream(mode: CallMode) {
    if (!navigator.mediaDevices?.getUserMedia) {
      throw new Error("Camera and microphone are unavailable in this window. Restart FeaChat from the updated Tauri app and allow macOS media permission.");
    }
    if (!localStreamRef.current) {
      localStreamRef.current = await navigator.mediaDevices.getUserMedia({ audio: true, video: mode === "video" });
    }
    return localStreamRef.current;
  }

  async function createCallConnection(peerNumber: string, mode: CallMode) {
    const stream = await ensureLocalStream(mode);
    const pc = new RTCPeerConnection({ iceServers: [{ urls: "stun:stun.l.google.com:19302" }] });
    peerConnectionsRef.current[peerNumber] = pc;
    stream.getTracks().forEach((track) => pc.addTrack(track, stream));
    pc.onicecandidate = (event) => {
      if (event.candidate) {
        sendCallSignal(peerNumber, { kind: "ice", candidate: event.candidate.toJSON() });
      }
    };
    pc.ontrack = (event) => {
      remoteStreamRef.current = event.streams[0] ?? remoteStreamRef.current;
      if (event.streams[0]) {
        setRemoteStreams((current) => ({ ...current, [peerNumber]: event.streams[0] }));
      }
      setCallMediaVersion((version) => version + 1);
    };
    pc.onconnectionstatechange = () => {
      if (pc.connectionState === "connected") {
        markCallActive();
      }
      if (["failed", "closed"].includes(pc.connectionState)) {
        finishCall(false);
      }
    };
    setCallMediaVersion((version) => version + 1);
    return pc;
  }

  async function startCall(mode: CallMode) {
    if (!selected && !selectedGroup) {
      setStatus("Select a chat before calling");
      return;
    }
    if (callState.status !== "idle") {
      setStatus("Finish the current call first");
      return;
    }
    setStatus("");
    setCallMenuOpen(false);
    const targets = selectedGroup
      ? selectedGroup.members.filter((member) => member.number !== me?.number).map((member) => member.number)
      : selected
        ? [selected.number]
        : [];
    if (targets.length === 0) {
      setStatus("No available call participants");
      return;
    }
    closeCallMedia();
    callStartedAtRef.current = null;
    const conversationId = selectedGroup?.id;
    const title = selectedGroup ? groupTitle(selectedGroup) : displayName(selected!);
    setCallState({ status: "outgoing", mode, peerNumber: conversationId ?? targets[0], peerName: title, conversationId });
    try {
      await ensureLocalStream(mode);
      for (const target of targets) {
        const pc = await createCallConnection(target, mode);
        const offer = await pc.createOffer();
        await pc.setLocalDescription(offer);
        sendCallSignal(target, { kind: "offer", mode, description: offer }, conversationId);
      }
    } catch (error) {
      finishCall(false);
      setStatus(error instanceof Error ? error.message : "Could not start call");
    }
  }

  async function acceptCall() {
    if (callState.status !== "incoming" || !incomingOfferRef.current) {
      return;
    }
    callRingtoneStopRef.current?.();
    callRingtoneStopRef.current = null;
    setStatus("");
    const { peerNumber, mode } = callState;
    const offer = incomingOfferRef.current;
    const pendingIce = pendingIceCandidatesRef.current[peerNumber] ?? [];
    setCallState({ ...callState, status: "connecting" });
    try {
      closeCallMedia();
      pendingIceCandidatesRef.current[peerNumber] = pendingIce;
      const pc = await createCallConnection(peerNumber, mode);
      await pc.setRemoteDescription(offer);
      await applyPendingIceCandidates(peerNumber);
      const answer = await pc.createAnswer();
      await pc.setLocalDescription(answer);
      sendCallSignal(peerNumber, { kind: "answer", description: answer });
      markCallActive();
    } catch (error) {
      sendCallSignal(peerNumber, { kind: "reject" });
      finishCall(false);
      setStatus(error instanceof Error ? error.message : "Could not answer call");
    }
  }

  function rejectCall() {
    if (callState.status !== "incoming") {
      return;
    }
    callRingtoneStopRef.current?.();
    callRingtoneStopRef.current = null;
    sendCallSignal(callState.peerNumber, { kind: "reject" });
    finishCall(false);
  }

  async function handleCallSignal(sender: string, signal: CallSignal, conversationId?: string) {
    if (signal.kind === "offer") {
      if (callStateRef.current.status !== "idle") {
        sendCallSignal(sender, { kind: "reject" });
        return;
      }
      incomingOfferRef.current = signal.description;
      const incomingGroup = conversationId ? conversations.find((conversation) => conversation.id === conversationId) : null;
      callStartedAtRef.current = null;
      callRingtoneStopRef.current?.();
      callRingtoneStopRef.current = startIncomingCallRingtone();
      setCallState({
        status: "incoming",
        mode: signal.mode,
        peerNumber: sender,
        peerName: incomingGroup ? `${groupTitle(incomingGroup)} · ${peerName(sender)}` : peerName(sender),
        conversationId
      });
      return;
    }
    if (signal.kind === "answer") {
      await peerConnectionsRef.current[sender]?.setRemoteDescription(signal.description);
      await applyPendingIceCandidates(sender);
      markCallActive();
      return;
    }
    if (signal.kind === "ice") {
      const pc = peerConnectionsRef.current[sender];
      if (pc?.remoteDescription) {
        await pc.addIceCandidate(signal.candidate).catch(() => undefined);
      } else {
        pendingIceCandidatesRef.current[sender] = [...(pendingIceCandidatesRef.current[sender] ?? []), signal.candidate];
      }
      return;
    }
    if (signal.kind === "reject") {
      callRingtoneStopRef.current?.();
      callRingtoneStopRef.current = null;
      const currentCall = callStateRef.current;
      if (currentCall.status !== "idle") {
        void recordCallMessage(currentCall, "declined", null);
      }
      finishCall(false);
      setStatus("Call declined");
      return;
    }
    if (signal.kind === "end") {
      callRingtoneStopRef.current?.();
      callRingtoneStopRef.current = null;
      finishCall(false);
      setStatus("Call ended");
    }
  }

  async function sendMessage(event: FormEvent) {
    event.preventDefault();
    if (!token || (!selected && !selectedGroup) || uploading || recordingState !== "idle" || (!draft.trim() && pendingFiles.length === 0)) {
      return;
    }
    const text = draft.trim();
    const filesToSend = pendingFiles;
    setDraft("");
    setPendingFiles([]);
    setUploadError("");

    if (text && wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(
        JSON.stringify({
          type: "send_message",
          receiver: selected?.number,
          conversation_id: selectedGroup?.id,
          message_type: "text",
          body: text
        })
      );
    } else if (text) {
      const response = selectedGroup
        ? await api.sendConversationMessage(token, selectedGroup.id, text)
        : await api.sendMessage(token, selected!.number, text);
      const key = selectedGroup?.id ?? selected!.number;
      setPreviewMessage(key, response.message);
      appendMessages((current) => {
        const nextMessages = uniqueMessages([...current, response.message]);
        if (me) {
          writeCachedMessages(me.number, key, nextMessages);
        }
        return nextMessages;
      });
    }

    if (filesToSend.length > 0) {
      await uploadFiles(filesToSend);
    }
  }

  async function sendAttachments(event: ChangeEvent<HTMLInputElement>) {
    const files = Array.from(event.currentTarget.files ?? []);
    event.currentTarget.value = "";
    if (files.length === 0) {
      return;
    }
    if (!token || (!selected && !selectedGroup)) {
      setUploadError("Select a chat before attaching files");
      return;
    }
    setUploadError("");
    setPendingFiles((current) => [...current, ...files]);
  }

  async function uploadFiles(files: File[]) {
    if (!token || (!selected && !selectedGroup) || files.length === 0) {
      return;
    }
    setUploading(true);
    setUploadStatus(`Uploading ${files.length === 1 ? files[0].name : `${files.length} files`}...`);
    try {
      for (const file of files) {
        const response = selectedGroup
          ? await api.uploadConversationAttachment(token, selectedGroup.id, file)
          : await api.uploadAttachment(token, selected!.number, file);
        const key = selectedGroup?.id ?? selected!.number;
        setPreviewMessage(key, response.message);
        appendMessages((current) => {
          const nextMessages = uniqueMessages([...current, response.message]);
          if (me) {
            writeCachedMessages(me.number, key, nextMessages);
          }
          return nextMessages;
        });
      }
      setUploadStatus("");
    } catch (error) {
      setUploadError(error instanceof Error ? error.message : "File upload failed");
    } finally {
      setUploading(false);
      setUploadStatus("");
    }
  }

  async function downloadAttachment(attachment: NonNullable<Message["attachment"]>) {
    setUploadError("");
    try {
      const response = await fetch(api.fileUrl(attachment.url, true));
      if (!response.ok) {
        throw new Error("Download failed");
      }
      const blob = await response.blob();
      const objectUrl = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = objectUrl;
      link.download = attachment.name || "download";
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.setTimeout(() => URL.revokeObjectURL(objectUrl), 1000);
    } catch (error) {
      setUploadError(error instanceof Error ? error.message : "Download failed");
    }
  }

  useEffect(() => {
    if (!token) {
      return;
    }
    loadContacts(token, me?.number).catch((error) => {
      if (error instanceof Error && error.message === "Not authenticated") {
        logout();
        return;
      }
      setStatus(error instanceof Error ? error.message : "Failed to load contacts");
    });
  }, [token, me?.number]);

  useEffect(() => {
    if (!token || !me?.number) {
      return;
    }
    const interval = window.setInterval(() => {
      loadContacts(token, me.number).catch(() => undefined);
    }, 5000);
    return () => window.clearInterval(interval);
  }, [token, me?.number]);

  useEffect(() => {
    if (!me) {
      setUnreadCounts({});
      setPinnedChatKeys([]);
      setDockUnreadBadge(0);
      return;
    }
    setTheme(readTheme(me.number));
    setMutedPeers(readMutedPeers(me.number));
    setUnreadCounts(readUnreadCounts(me.number));
    setPinnedChatKeys(readPinnedChatKeys(me.number));
    return migrateLegacyLocalCache(() => {
      setTheme(readTheme(me.number));
      setMutedPeers(readMutedPeers(me.number));
      setUnreadCounts(readUnreadCounts(me.number));
      setPinnedChatKeys(readPinnedChatKeys(me.number));
    });
  }, [me?.number]);

  useEffect(() => {
    const preventNativeContextMenu = (event: Event) => {
      event.preventDefault();
    };
    document.addEventListener("contextmenu", preventNativeContextMenu);
    return () => document.removeEventListener("contextmenu", preventNativeContextMenu);
  }, []);

  useEffect(() => {
    const totalUnread = Object.values(unreadCounts).reduce((sum, count) => sum + count, 0);
    setDockUnreadBadge(totalUnread);
  }, [unreadCounts]);

  useEffect(() => {
    if (!appMenuOpen) {
      return;
    }
    const closeMenu = (event: PointerEvent) => {
      if (!appMenuRef.current?.contains(event.target as Node)) {
        setAppMenuOpen(false);
      }
    };
    document.addEventListener("pointerdown", closeMenu);
    return () => document.removeEventListener("pointerdown", closeMenu);
  }, [appMenuOpen]);

  useEffect(() => {
    if (!addMenuOpen) {
      return;
    }
    const closeMenu = (event: PointerEvent) => {
      if (!addMenuRef.current?.contains(event.target as Node)) {
        setAddMenuOpen(false);
      }
    };
    document.addEventListener("pointerdown", closeMenu);
    return () => document.removeEventListener("pointerdown", closeMenu);
  }, [addMenuOpen]);

  useEffect(() => {
    if (!callMenuOpen) {
      return;
    }
    const closeMenu = (event: PointerEvent) => {
      if (!callMenuRef.current?.contains(event.target as Node)) {
        setCallMenuOpen(false);
      }
    };
    document.addEventListener("pointerdown", closeMenu);
    return () => document.removeEventListener("pointerdown", closeMenu);
  }, [callMenuOpen]);

  useEffect(() => {
    if (!chatContextMenu) {
      return;
    }
    const closeMenu = () => setChatContextMenu(null);
    document.addEventListener("pointerdown", closeMenu);
    window.addEventListener("resize", closeMenu);
    return () => {
      document.removeEventListener("pointerdown", closeMenu);
      window.removeEventListener("resize", closeMenu);
    };
  }, [chatContextMenu]);

  useEffect(() => {
    if (!messageContextMenu) {
      return;
    }
    const closeMenu = () => setMessageContextMenu(null);
    document.addEventListener("pointerdown", closeMenu);
    window.addEventListener("resize", closeMenu);
    return () => {
      document.removeEventListener("pointerdown", closeMenu);
      window.removeEventListener("resize", closeMenu);
    };
  }, [messageContextMenu]);

  useEffect(() => {
    callStateRef.current = callState;
  }, [callState]);

  useEffect(() => {
    return () => {
      stopIncomingCallRingtone();
      stopVoiceTimer();
      mediaRecorderRef.current?.stop();
      stopVoiceStream();
      Object.values(voicePlaybackUrlsRef.current).forEach((objectUrl) => URL.revokeObjectURL(objectUrl));
      voicePlaybackUrlsRef.current = {};
      setDockUnreadBadge(0);
    };
  }, []);

  useEffect(() => {
    mutedPeersRef.current = mutedPeers;
  }, [mutedPeers]);

  useEffect(() => {
    if (params.get("autoLogin") !== "1") {
      return;
    }
    if (me?.number === initialNumber) {
      return;
    }
    loginWithCredentials({
      number: initialNumber,
      password: initialPassword,
      email: initialEmail,
      nickname: initialNickname,
      shouldRegister: params.get("register") === "1"
    });
  }, []);

  useEffect(() => {
    if (!token) {
      return;
    }
    const socket = new WebSocket(api.wsUrl(token));
    wsRef.current = socket;
    socket.onopen = () => setSocketState("online");
    socket.onclose = () => setSocketState("offline");
    socket.onerror = () => setSocketState("error");
    socket.onmessage = (event) => {
      const payload = JSON.parse(event.data);
      if (payload.type === "message") {
        const message = payload.message as Message;
        const groupId = message.conversation_id?.startsWith("grp:") ? message.conversation_id : null;
        const peer = groupId ?? (message.sender === me?.number ? message.receiver : message.sender);
        const isCurrentConversation = groupId ? groupId === selectedGroupId : peer === selectedNumber;
        if (message.sender !== me?.number && message.type !== "call" && !mutedPeersRef.current.has(peer)) {
          playIncomingMessageSound();
        }
        if (message.sender !== me?.number && !isCurrentConversation) {
          incrementUnreadCount(peer);
        }
        if (me?.number) {
          mergeCachedMessages(me.number, peer, [message]);
          setPreviewMessage(peer, message);
        }
        appendMessages((current) => {
          if (!isCurrentConversation) {
            return current;
          }
          return uniqueMessages([...current, message]);
        });
        loadContacts().catch(() => undefined);
      } else if (payload.type === "call_signal") {
        handleCallSignal(payload.sender, payload.signal as CallSignal, payload.conversation_id).catch((error) => {
          setStatus(error instanceof Error ? error.message : "Call signaling failed");
        });
      }
    };
    return () => {
      socket.close();
    };
  }, [token, me?.number, selectedNumber, selectedGroupId]);

  useEffect(() => {
    const behavior = scrollBehaviorRef.current;
    bottomRef.current?.scrollIntoView({ behavior, block: "end" });
    scrollBehaviorRef.current = "smooth";
  }, [messages]);

  useEffect(() => {
    if (localVideoRef.current) {
      localVideoRef.current.srcObject = localStreamRef.current;
    }
    if (remoteVideoRef.current) {
      remoteVideoRef.current.srcObject = remoteStreamRef.current;
    }
  }, [callMediaVersion, callState.status]);

  const orderedFriends = useMemo(() => [...friends].sort((a, b) => displayName(a).localeCompare(displayName(b))), [friends]);
  const friendNumbers = useMemo(() => new Set(friends.map((friend) => friend.number)), [friends]);
  const filteredFriends = useMemo(() => {
    const needle = query.trim().toLowerCase();
    if (!needle) {
      return orderedFriends;
    }
    return orderedFriends.filter((friend) => {
      return displayName(friend).toLowerCase().includes(needle) || friend.number.toLowerCase().includes(needle);
    });
  }, [orderedFriends, query]);
  const groupConversations = useMemo(() => {
    const groups = conversations.filter((conversation) => conversation.type === "group");
    const needle = query.trim().toLowerCase();
    if (!needle) {
      return groups;
    }
    return groups.filter((conversation) => groupTitle(conversation).toLowerCase().includes(needle));
  }, [conversations, query]);
  const pinnedChatKeySet = useMemo(() => new Set(pinnedChatKeys), [pinnedChatKeys]);
  function chatItemKey(item: ChatListItem) {
    return item.kind === "group" ? item.conversation.id : item.friend.number;
  }
  function chatItemTitle(item: ChatListItem) {
    return item.kind === "group" ? conversationTitle(item.conversation) : displayName(item.friend);
  }
  function compareChatItems(a: ChatListItem, b: ChatListItem) {
    const aKey = chatItemKey(a);
    const bKey = chatItemKey(b);
    const aMessage = previewMessages[aKey];
    const bMessage = previewMessages[bKey];
    const aTime = aMessage ? parseMessageTime(aMessage.time).getTime() : 0;
    const bTime = bMessage ? parseMessageTime(bMessage.time).getTime() : 0;
    if (aTime !== bTime) {
      return bTime - aTime;
    }
    return chatItemTitle(a).localeCompare(chatItemTitle(b));
  }
  const chatListItems = useMemo(() => {
    const searching = query.trim().length > 0;
    const items: ChatListItem[] = [
      ...groupConversations.map((conversation) => ({ kind: "group" as const, conversation })),
      ...filteredFriends.map((friend) => ({ kind: "direct" as const, friend }))
    ].filter((item) => {
      return searching || Boolean(previewMessages[chatItemKey(item)]);
    });
    return items.sort((a, b) => {
      const aPinned = pinnedChatKeySet.has(chatItemKey(a));
      const bPinned = pinnedChatKeySet.has(chatItemKey(b));
      if (aPinned !== bPinned) {
        return aPinned ? -1 : 1;
      }
      return compareChatItems(a, b);
    });
  }, [filteredFriends, groupConversations, pinnedChatKeySet, previewMessages, query]);
  const pinnedChatListCount = useMemo(
    () => chatListItems.filter((item) => pinnedChatKeySet.has(chatItemKey(item))).length,
    [chatListItems, pinnedChatKeySet]
  );
  const contentTitle = selectedGroup
    ? groupTitle(selectedGroup)
    : selected
      ? displayName(selected)
    : activeSection === "contacts"
      ? "Contacts"
      : activeSection === "newFriends"
        ? "New Friends"
        : "FeaChat";
  const orderedMessages = useMemo(() => sortMessages(messages), [messages]);
  const filteredMessages = useMemo(() => {
    const query = chatSearchQuery.trim().toLowerCase();
    if (!query) {
      return orderedMessages;
    }
    return orderedMessages.filter((message) => messagePreview(message).toLowerCase().includes(query));
  }, [orderedMessages, chatSearchQuery]);
  const knownUsersByNumber = useMemo(() => {
    const users = new Map<string, User>();
    if (me) {
      users.set(me.number, me);
    }
    for (const friend of friends) {
      users.set(friend.number, friend);
    }
    for (const conversation of conversations) {
      for (const member of conversation.members) {
        users.set(member.number, member);
      }
      if (conversation.peer) {
        users.set(conversation.peer.number, conversation.peer);
      }
    }
    return users;
  }, [conversations, friends, me]);
  const chatListPreviewText = useCallback(
    (message: Message) => {
      const text = messagePreview(message);
      if (!me || message.sender === me.number) {
        return text;
      }
      const sender = knownUsersByNumber.get(message.sender);
      return `${sender ? displayName(sender) : message.sender}: ${text}`;
    },
    [knownUsersByNumber, me]
  );
  const conversationPreviews = useMemo(() => {
    return Object.fromEntries(
      [
        ...friends.map((friend) => {
          const last = previewMessages[friend.number] ?? null;
          return [
            friend.number,
            last
              ? {
                  text: chatListPreviewText(last),
                  time: formatMessageTimestamp(last.time)
                }
              : { text: "No messages yet" }
          ];
        }),
        ...groupConversations.map((conversation) => {
          const last = previewMessages[conversation.id] ?? null;
          return [
            conversation.id,
            last
              ? {
                  text: chatListPreviewText(last),
                  time: formatMessageTimestamp(last.time)
                }
              : { text: "No messages yet" }
          ];
        })
      ]
    );
  }, [chatListPreviewText, friends, groupConversations, previewMessages]);
  const contactGroups = useMemo(() => {
    const groups = new Map<string, User[]>();
    for (const friend of filteredFriends) {
      const key = contactGroupKey(friend);
      groups.set(key, [...(groups.get(key) ?? []), friend]);
    }
    const letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ".split("");
    return [...letters, "Others"].flatMap((key) => {
      const people = groups.get(key) ?? [];
      return people.length ? [{ key, people }] : [];
    });
  }, [filteredFriends]);
  const selectedGroupMemberNumbers = useMemo(
    () => new Set(selectedGroup?.members.map((member) => member.number) ?? []),
    [selectedGroup]
  );
  const contactPickerPeople = useMemo(() => {
    const needle = contactPickerSearch.trim().toLowerCase();
    const source =
      contactPickerMode === "kickGroup" && selectedGroup
        ? selectedGroup.members.filter((member) => member.number !== me?.number)
        : orderedFriends;
    return source.filter((user) => {
      if (!needle) {
        return true;
      }
      return displayName(user).toLowerCase().includes(needle) || user.number.toLowerCase().includes(needle);
    });
  }, [contactPickerMode, contactPickerSearch, me?.number, orderedFriends, selectedGroup]);
  const contactPickerGroups = useMemo(() => {
    const groups = new Map<string, User[]>();
    for (const person of contactPickerPeople) {
      const key = contactGroupKey(person);
      groups.set(key, [...(groups.get(key) ?? []), person]);
    }
    const letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ".split("");
    return [...letters, "Others"].flatMap((key) => {
      const people = groups.get(key) ?? [];
      return people.length ? [{ key, people }] : [];
    });
  }, [contactPickerPeople]);
  const pickedUsers = useMemo(
    () =>
      pickedContacts
        .map((number) => contactPickerPeople.find((person) => person.number === number) ?? friends.find((friend) => friend.number === number))
        .filter((user): user is User => Boolean(user)),
    [contactPickerPeople, friends, pickedContacts]
  );
  const contactPickerTitle =
    contactPickerMode === "createGroup"
      ? "Start Group Chat"
      : contactPickerMode === "inviteGroup"
        ? "Add Members"
        : "Remove Members";
  const contactPickerAction = contactPickerMode === "kickGroup" ? "Remove" : "Finish";
  const pendingGroupInviteIds = useMemo(() => new Set(groupInvites.map((invite) => invite.id)), [groupInvites]);
  const joinedGroupIds = useMemo(
    () => new Set(conversations.filter((conversation) => conversation.type === "group").map((conversation) => conversation.id)),
    [conversations]
  );
  const contactGroupConversations = useMemo(
    () => [...conversations.filter((conversation) => conversation.type === "group")].sort((a, b) => groupTitle(a).localeCompare(groupTitle(b))),
    [conversations]
  );
  const totalUnread = Object.values(unreadCounts).reduce((sum, count) => sum + count, 0);
  const pendingFriendRequestCount = requests.length;

  if (!token || !me) {
    return (
      <main className="auth-shell" onContextMenu={(event) => event.preventDefault()}>
        <WindowControls />
        <section className="auth-panel">
          <div className="brand-row">
            <div className="brand-mark">F</div>
            <div>
              <h1>FeaChat</h1>
              <p>Desktop messaging, rebuilt on the new stack.</p>
            </div>
          </div>
          <form className="auth-form" onSubmit={authenticate}>
            <div className="mode-tabs">
              <button type="button" className={mode === "login" ? "active" : ""} onClick={() => setMode("login")}>
                Login
              </button>
              <button
                type="button"
                className={mode === "register" ? "active" : ""}
                onClick={() => setMode("register")}
              >
                Register
              </button>
            </div>
            <label>
              Number
              <input {...noTextAssist} value={number} onChange={(event) => setNumber(event.target.value)} />
            </label>
            <label>
              Password
              <input {...noTextAssist} value={password} onChange={(event) => setPassword(event.target.value)} type="password" />
            </label>
            {mode === "register" && (
              <>
                <label>
                  Email
                  <input {...noTextAssist} value={email} onChange={(event) => setEmail(event.target.value)} />
                </label>
                <label>
                  Display Name
                  <input {...noTextAssist} value={nickname} onChange={(event) => setNickname(event.target.value)} />
                </label>
              </>
            )}
            {status && <p className="status-text">{status}</p>}
            <button className="primary-action" type="submit">
              {mode === "register" ? "Create account" : "Login"}
            </button>
          </form>
        </section>
      </main>
    );
  }

  return (
    <main className={`app-shell theme-${theme}`} onContextMenu={(event) => event.preventDefault()}>
      <WindowControls />
      <aside className="rail" onMouseDown={startWindowDrag} onDoubleClick={toggleMaximizeFromDragArea}>
        <button className="self-avatar" title="Profile" onClick={(event) => openProfileCard(event, me, false)}>
          <img src={userAvatarSrc(me)} alt="" draggable={false} />
        </button>
        <button
          title="Chats"
          className={`rail-button ${activeSection === "chats" ? "active" : ""}`}
          onClick={() => {
            setActiveSection("chats");
            clearTransientUi();
          }}
        >
          <MessageCircle size={21} />
          {totalUnread > 0 && <span className="rail-badge">{totalUnread}</span>}
        </button>
        <button
          title="Contacts"
          className={`rail-button ${activeSection === "contacts" || activeSection === "newFriends" ? "active" : ""}`}
          onClick={() => {
            setActiveSection("contacts");
            setSelected(null);
            setSelectedGroup(null);
            replaceMessages([], "auto");
            clearTransientUi();
          }}
        >
          <CircleUserRound size={21} />
          {pendingFriendRequestCount > 0 && <span className="rail-badge">{pendingFriendRequestCount}</span>}
        </button>
        <button
          title="Moments"
          className={`rail-button ${activeSection === "moments" ? "active" : ""}`}
          onClick={() => {
            setActiveSection("moments");
            setSelected(null);
            setSelectedGroup(null);
            replaceMessages([], "auto");
            clearTransientUi();
          }}
        >
          <Aperture size={21} />
        </button>
        <div className="rail-bottom" ref={appMenuRef}>
          <button className="rail-button" title="Menu" onClick={() => setAppMenuOpen((open) => !open)}>
            <Menu size={21} />
          </button>
          {appMenuOpen && (
            <div className="app-menu">
              <button
                onClick={() => {
                  setSettingsSection("account");
                  setAccountNameDraft(me.nickname || me.number);
                  setCurrentPasswordDraft("");
                  setNewPasswordDraft("");
                  setConfirmPasswordDraft("");
                  setAccountStatus("");
                  setAccountError("");
                  setSettingsOpen(true);
                  setAppMenuOpen(false);
                }}
              >
                <Settings size={16} />
                Settings
              </button>
              <button>
                <MessageSquare size={16} />
                Feedback
              </button>
              <button onClick={logout}>
                <LogOut size={16} />
                Log Out
              </button>
            </div>
          )}
        </div>
      </aside>

      <section className="sidebar">
        <div className="search-row" onMouseDown={startWindowDrag} onDoubleClick={toggleMaximizeFromDragArea}>
          <div className="search-field">
            <Search size={16} />
            <input
              {...noTextAssist}
              placeholder="Search"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter") {
                  event.preventDefault();
                }
              }}
            />
          </div>
          <div className="add-menu-anchor" ref={addMenuRef}>
            <button
              className="add-button"
              type="button"
              onClick={(event) => {
                event.stopPropagation();
                setStatus("");
                setAddMenuOpen((open) => !open);
                setAddFriendOpen(false);
                setAddSearchResults([]);
                setAddQuery("");
              }}
              title="Add"
            >
              <Plus size={20} />
            </button>
            {addMenuOpen && (
              <div className="add-popover">
                <button type="button" onClick={() => openContactPicker("createGroup")}>
                  <MessageCircle size={20} />
                  Start Group Chat
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setAddMenuOpen(false);
                    setAddFriendOpen(true);
                    setAddQuery("");
                    setAddSearchResults([]);
                  }}
                >
                  <UserPlus size={20} />
                  Add Contacts
                </button>
              </div>
            )}
          </div>
        </div>
        {status && <p className="inline-status">{status}</p>}
        {addFriendOpen && (
          <div className="add-friend-panel">
            <div className="add-friend-search">
              <Search size={15} />
              <input
                {...noTextAssist}
                autoFocus
                placeholder="FeaChat ID or name"
                value={addQuery}
                onChange={(event) => setAddQuery(event.target.value)}
                onKeyDown={(event) => {
                  if (event.key === "Enter") {
                    event.preventDefault();
                    searchPeople();
                  }
                }}
              />
              <button type="button" onClick={searchPeople}>
                Search
              </button>
            </div>
            {addSearchResults.length > 0 && (
              <div className="add-results">
                {addSearchResults.map((user) => {
                  return (
                    <button
                      className="person-row add-result-row"
                      key={user.number}
                      type="button"
                      onClick={(event) => openProfileCard(event, user, friendNumbers.has(user.number))}
                    >
                      <UserAvatar user={user} />
                      <span>
                        <strong>{displayName(user)}</strong>
                        <small>{user.number}</small>
                      </span>
                    </button>
                  );
                })}
              </div>
            )}
          </div>
        )}

        {activeSection === "moments" ? (
          <div className="moments-placeholder">
            <Aperture size={34} />
            <strong>Moments</strong>
            <span>Coming soon</span>
          </div>
        ) : (
          <>
            <div className="stack-block grow">
              <div className="friend-list">
                {activeSection === "newFriends" ? (
                  <div className="new-friends-list">
                    <h3>Group Invites</h3>
                    {groupInvites.length > 0 ? (
                      groupInvites.map((invite) => (
                        <div className="request-row" key={invite.id}>
                          <span className="request-profile">
                            <GroupAvatar conversation={{ ...invite.conversation, type: "group", peer: null, my_alias: "", last_message: null }} />
                            <span>
                              <strong>{invite.conversation.title}</strong>
                              <small>Invited by {invite.inviter}</small>
                            </span>
                          </span>
                          <button onClick={() => acceptInvite(invite.id)} title="Accept">
                            <Check size={16} />
                          </button>
                          <button onClick={() => rejectInvite(invite.id)} title="Reject">
                            <X size={16} />
                          </button>
                        </div>
                      ))
                    ) : (
                      <p className="empty-list-note">No group invites</p>
                    )}
                    <h3>Friend Requests</h3>
                    {requests.length > 0 ? (
                      requests.map((request) => (
                        <div className="request-row" key={request.number}>
                          <button className="request-profile" onClick={(event) => openProfileCard(event, request, false)}>
                            <UserAvatar user={request} />
                            <span>
                              <strong>{displayName(request)}</strong>
                              <small>{request.number}</small>
                            </span>
                          </button>
                          <button onClick={() => acceptFriend(request.number)} title="Accept">
                            <Check size={16} />
                          </button>
                          <button onClick={() => rejectFriend(request.number)} title="Reject">
                            <X size={16} />
                          </button>
                        </div>
                      ))
                    ) : (
                      <p className="empty-list-note">No pending requests</p>
                    )}
                    <h3>History</h3>
                    {requestHistory.length > 0 ? (
                      requestHistory.map((record) => (
                        <div className="request-history-row" key={`${record.requester}-${record.receiver}`}>
                          <UserAvatar user={record} className="avatar contact-avatar" />
                          <span>
                            <strong>{displayName(record)}</strong>
                            <small>
                              {record.direction === "incoming" ? "Received" : "Sent"} · {record.status}
                            </small>
                          </span>
                        </div>
                      ))
                    ) : (
                      <p className="empty-list-note">No request history</p>
                    )}
                  </div>
                ) : activeSection === "contacts" ? (
                  <>
                    <button
                      className="person-row contact-row new-friends-entry"
                      type="button"
                      onClick={() => {
                        setActiveSection("newFriends");
                        setSelected(null);
                        setSelectedGroup(null);
                        replaceMessages([], "auto");
                        clearTransientUi();
                        loadContacts().catch(() => undefined);
                      }}
                    >
                      <span className="avatar contact-avatar">
                        <UserPlus size={17} />
                      </span>
                      <span>
                        <strong>New Friends</strong>
                      </span>
                      {requests.length > 0 && <span className="request-count">{requests.length}</span>}
                    </button>
                    {contactGroupConversations.length > 0 && (
                      <div className="contact-group my-groups-contact-group">
                        <div className="contact-letter">My Groups</div>
                        {contactGroupConversations.map((conversation) => (
                          <button
                            key={conversation.id}
                            className={`person-row contact-row ${selectedGroup?.id === conversation.id ? "selected" : ""}`}
                            onClick={() => {
                              if (selectedGroup?.id !== conversation.id) {
                                loadGroupMessages(conversation);
                              }
                            }}
                          >
                            <GroupAvatar conversation={conversation} className="avatar contact-avatar group-avatar" />
                            <span>
                              <strong>{groupTitle(conversation)}</strong>
                            </span>
                          </button>
                        ))}
                      </div>
                    )}
                    {contactGroups.map((group) => (
                      <div className="contact-group" key={group.key}>
                        <div className="contact-letter">{group.key}</div>
                        {group.people.map((friend) => (
                          <button
                            key={friend.number}
                            className={`person-row contact-row ${selected?.number === friend.number ? "selected" : ""}`}
                            onClick={() => {
                              if (selected?.number !== friend.number) {
                                loadMessages(friend);
                              }
                            }}
                          >
                            <span
                              className="avatar-button"
                              onClick={(event) => {
                                event.stopPropagation();
                                openProfileCard(event, friend, true);
                              }}
                            >
                              <UserAvatar user={friend} className="avatar contact-avatar" />
                            </span>
                            <span>
                              <strong>{displayName(friend)}</strong>
                            </span>
                          </button>
                        ))}
                      </div>
                    ))}
                  </>
                ) : (
                  <>
                    {chatListItems.map((item, index) => {
                      const separator =
                        index === pinnedChatListCount && pinnedChatListCount > 0 && pinnedChatListCount < chatListItems.length;
                      if (item.kind === "group") {
                        const { conversation } = item;
                        return (
                          <Fragment key={conversation.id}>
                            {separator && <div className="chat-list-separator" />}
                            <button
                              className={`person-row ${selectedGroup?.id === conversation.id ? "selected" : ""}`}
                              onClick={() => {
                                if (selectedGroup?.id !== conversation.id) {
                                  loadGroupMessages(conversation);
                                }
                              }}
                              onContextMenu={(event) => openChatContextMenu(event, conversation.id, conversationTitle(conversation))}
                            >
                              <span className="chat-avatar-wrap">
                                <GroupAvatar conversation={conversation} />
                                {unreadCounts[conversation.id] > 0 && <span className="unread-badge">{unreadCounts[conversation.id]}</span>}
                              </span>
                              <span>
                                <span className="person-title-row">
                                  <strong>{conversationTitle(conversation)}</strong>
                                  {conversationPreviews[conversation.id]?.time && (
                                    <time className="chat-preview-time">{conversationPreviews[conversation.id].time}</time>
                                  )}
                                </span>
                                <small>{conversationPreviews[conversation.id]?.text ?? "No messages yet"}</small>
                              </span>
                            </button>
                          </Fragment>
                        );
                      }
                      const { friend } = item;
                      return (
                        <Fragment key={friend.number}>
                          {separator && <div className="chat-list-separator" />}
                          <button
                            className={`person-row ${selected?.number === friend.number ? "selected" : ""}`}
                            onClick={() => {
                              if (selected?.number !== friend.number) {
                                loadMessages(friend);
                              }
                            }}
                            onContextMenu={(event) => openChatContextMenu(event, friend.number, displayName(friend))}
                          >
                            <span className="chat-avatar-wrap">
                              <UserAvatar user={friend} />
                              {unreadCounts[friend.number] > 0 && <span className="unread-badge">{unreadCounts[friend.number]}</span>}
                            </span>
                            <span>
                              <span className="person-title-row">
                                <strong>{displayName(friend)}</strong>
                                {conversationPreviews[friend.number]?.time && (
                                  <time className="chat-preview-time">{conversationPreviews[friend.number].time}</time>
                                )}
                              </span>
                              <small>{conversationPreviews[friend.number]?.text ?? "No messages yet"}</small>
                            </span>
                          </button>
                        </Fragment>
                      );
                    })}
                  </>
                )}
              </div>
            </div>
          </>
        )}
      </section>

      <section className="conversation">
        <header className="conversation-header" onMouseDown={startWindowDrag} onDoubleClick={toggleMaximizeFromDragArea}>
          {selected || selectedGroup ? (
            <>
              <h2>{selectedGroup ? groupTitle(selectedGroup) : displayName(selected!)}</h2>
              <div className="conversation-tools">
                {(selected || selectedGroup) && (
                  <div className="call-menu-anchor" ref={callMenuRef}>
                    <button
                      className={`conversation-more call-button ${callMenuOpen ? "active" : ""}`}
                      type="button"
                      title="Call"
                      onClick={(event) => {
                        event.stopPropagation();
                        setCallMenuOpen((open) => !open);
                        setConversationMenuOpen(false);
                      }}
                    >
                      <Phone size={19} />
                    </button>
                    {callMenuOpen && (
                      <div className="call-popover">
                        <button type="button" onClick={() => startCall("voice")}>
                          <Phone size={17} />
                          Voice Call
                        </button>
                        <button type="button" onClick={() => startCall("video")}>
                          <Video size={17} />
                          Video Call
                        </button>
                      </div>
                    )}
                  </div>
                )}
                <button
                  className="conversation-more"
                  type="button"
                  title="Conversation options"
                  onClick={() => setConversationMenuOpen((open) => !open)}
                >
                  <MoreHorizontal size={22} />
                </button>
              </div>
            </>
          ) : (
            <h2>{contentTitle}</h2>
          )}
        </header>
        {selected || selectedGroup ? (
          <>
            {chatSearchOpen && (
              <div className="chat-search">
                <Search size={15} />
                <input
                  {...noTextAssist}
                  autoFocus
                  value={chatSearchQuery}
                  placeholder="Search messages"
                  onChange={(event) => setChatSearchQuery(event.target.value)}
                />
                <span>{chatSearchQuery.trim() ? `${filteredMessages.length} found` : "All messages"}</span>
                <button
                  type="button"
                  onClick={() => {
                    setChatSearchOpen(false);
                    setChatSearchQuery("");
                  }}
                >
                  <X size={14} />
                </button>
              </div>
            )}
            <div className="message-list">
              {filteredMessages.map((message, index) => {
                const mine = message.sender === me.number;
                const user =
                  mine
                    ? me
                    : selectedGroup?.members.find((member) => member.number === message.sender) ?? selected ?? me;
                const inviteCard = parseGroupInviteMessage(message);
                const callMessage = parseCallMessage(message);
                const audioMessage = isAudioMessage(message);
                const videoMessage = isVideoMessage(message);
                const invitePending = inviteCard ? pendingGroupInviteIds.has(inviteCard.invite_id) : false;
                const inviteJoined = inviteCard ? joinedGroupIds.has(inviteCard.conversation_id) : false;
                return (
                  <Fragment key={message.id}>
                    {shouldShowTimestamp(filteredMessages, index) && (
                      <div className="time-stamp">{formatMessageTimestamp(message.time)}</div>
                    )}
                    <div className={`message-row ${mine ? "mine" : "theirs"}`}>
                      {!mine && (
                        <button className="message-avatar" onClick={(event) => openProfileCard(event, user, true)}>
                          <UserAvatar user={user} className="avatar message-avatar-image" />
                        </button>
                      )}
                      <div
                        className={`bubble ${message.attachment ? "with-attachment" : ""} ${audioMessage ? "audio-bubble" : ""} ${inviteCard ? "invite-bubble" : ""} ${callMessage ? "call-bubble" : ""}`}
                        onContextMenu={(event) => openMessageContextMenu(event, message)}
                      >
                        {inviteCard ? (
                          <div className="group-invite-card">
                            <strong>{inviteCard.title}</strong>
                            <small>Group invite from {inviteCard.inviter}</small>
                            {invitePending ? (
                              <button type="button" onClick={() => acceptInvite(inviteCard.invite_id)}>
                                Accept Invite
                              </button>
                            ) : (
                              <span className="invite-state">{inviteJoined ? "Joined" : "Invite Used"}</span>
                            )}
                          </div>
                        ) : callMessage ? (
                          <div className="call-message-card">
                            {callMessage.mode === "video" ? <Video size={15} /> : <Phone size={15} />}
                            <span>{formatCallMessage(message)}</span>
                          </div>
                        ) : message.attachment ? (
                          isImageMessage(message) ? (
                            <div className="image-message-card">
                              <a className="image-message" href={api.fileUrl(message.attachment.url)} target="_blank">
                                <img src={api.fileUrl(message.attachment.url)} alt={message.attachment.name} />
                              </a>
                              <div className="attachment-footer">
                                <span>{message.attachment.name}</span>
                                <button
                                  className="file-download"
                                  type="button"
                                  onClick={() => downloadAttachment(message.attachment!)}
                                >
                                  <Download size={15} />
                                  Download
                                </button>
                              </div>
                            </div>
                          ) : audioMessage ? (
                            <div className="voice-message-wrap">
                              <div
                                className={`voice-message ${playingAudioId === message.id ? "playing" : ""}`}
                                role="button"
                                tabIndex={0}
                                onClick={(event) => {
                                  const audio = event.currentTarget.querySelector("audio");
                                  if (!audio) {
                                    return;
                                  }
                                  void playVoiceMessage(message, audio);
                                }}
                                onKeyDown={(event) => {
                                  if (event.key === "Enter" || event.key === " ") {
                                    event.preventDefault();
                                    event.currentTarget.click();
                                  }
                                }}
                              >
                                <Mic size={17} />
                                <span className="voice-wave" aria-hidden="true">
                                  <i />
                                  <i />
                                  <i />
                                </span>
                                <span className="voice-duration">{voiceDurationLabel(message)}</span>
                                <audio
                                  src={api.fileUrl(message.attachment.url)}
                                  preload="metadata"
                                  onPlay={() => setPlayingAudioId(message.id)}
                                  onPause={() => setPlayingAudioId((current) => (current === message.id ? null : current))}
                                  onEnded={() => setPlayingAudioId((current) => (current === message.id ? null : current))}
                                />
                                <button
                                  className="file-download"
                                  type="button"
                                  title="Download"
                                  onClick={(event) => {
                                    event.stopPropagation();
                                    downloadAttachment(message.attachment!);
                                  }}
                                >
                                  <Download size={15} />
                                </button>
                              </div>
                              {(transcribingMessageId === message.id || transcriptions[message.id] || transcriptionErrors[message.id]) && (
                                <span className={`voice-transcript ${transcriptionErrors[message.id] ? "error" : ""}`}>
                                  {transcribingMessageId === message.id
                                    ? "Transcribing..."
                                    : transcriptionErrors[message.id] || transcriptions[message.id]}
                                </span>
                              )}
                            </div>
                          ) : videoMessage ? (
                            <div className="video-message-card">
                              <video controls src={api.fileUrl(message.attachment.url)} />
                              <div className="attachment-footer">
                                <span>{message.attachment.name}</span>
                                <button
                                  className="file-download"
                                  type="button"
                                  onClick={() => downloadAttachment(message.attachment!)}
                                >
                                  <Download size={15} />
                                  Download
                                </button>
                              </div>
                            </div>
                          ) : (
                            <div className="file-message">
                              <FileText size={22} />
                              <span>
                                <strong>{message.attachment.name}</strong>
                                <small>{formatBytes(message.attachment.size)}</small>
                              </span>
                              <button
                                className="file-download"
                                type="button"
                                onClick={() => downloadAttachment(message.attachment!)}
                              >
                                <Download size={15} />
                                Download
                              </button>
                            </div>
                          )
                        ) : (
                          <p>{message.message}</p>
                        )}
                      </div>
                      {mine && (
                        <button className="message-avatar" onClick={(event) => openProfileCard(event, user, false)}>
                          <UserAvatar user={user} className="avatar message-avatar-image" />
                        </button>
                      )}
                    </div>
                  </Fragment>
                );
              })}
              <div ref={bottomRef} />
            </div>
            <form className="composer" onSubmit={sendMessage}>
              <textarea
                ref={textareaRef}
                {...noTextAssist}
                placeholder=""
                value={draft}
                onChange={(event) => setDraft(event.target.value)}
                onKeyDown={(event) => {
                  if (event.key === "Enter" && !event.shiftKey) {
                    event.preventDefault();
                    sendMessage(event);
                  }
                }}
              />
              <div className={`composer-meta ${pendingFiles.length > 0 || recordingState !== "idle" ? "active" : ""}`}>
                {pendingFiles.length > 0 && (
                  <div className="pending-files">
                    {pendingFiles.map((file, index) => (
                      <span key={`${file.name}-${file.size}-${index}`}>{file.name}</span>
                    ))}
                    <button type="button" onClick={() => setPendingFiles([])} title="Clear attachments">
                      <X size={14} />
                    </button>
                  </div>
                )}
                {recordingState !== "idle" && (
                  <div className="recording-pill">
                    <span />
                    {recordingState === "recording" ? `Recording ${recordingSeconds}s` : "Saving voice..."}
                  </div>
                )}
              </div>
              <div className="composer-actions">
                <div className="emoji-anchor">
                  <button
                    type="button"
                    className="composer-icon"
                    title="Emoji"
                    onClick={() => setEmojiPickerOpen((open) => !open)}
                  >
                    <Smile size={17} />
                  </button>
                  {emojiPickerOpen && (
                    <div className="emoji-popover">
                      <section>
                        <strong>Emoji</strong>
                        <div className="emoji-grid">
                          {EMOJI_ITEMS.map((item) => (
                            <button key={item} type="button" onClick={() => insertEmojiText(item)}>
                              {item}
                            </button>
                          ))}
                        </div>
                      </section>
                      <section>
                        <strong>Kaomoji</strong>
                        <div className="kaomoji-grid">
                          {KAOMOJI_ITEMS.map((item) => (
                            <button key={item} type="button" onClick={() => insertEmojiText(item)}>
                              {item}
                            </button>
                          ))}
                        </div>
                      </section>
                    </div>
                  )}
                </div>
                <button
                  type="button"
                  className={`composer-icon voice-record-button ${recordingState === "recording" ? "recording" : ""}`}
                  disabled={uploading || recordingState === "stopping"}
                  title={recordingState === "recording" ? "Stop recording" : "Record voice"}
                  onClick={toggleVoiceRecording}
                >
                  {recordingState === "recording" ? <Square size={14} /> : <Mic size={17} />}
                </button>
                <button
                  type="button"
                  className="composer-icon"
                  disabled={uploading}
                  title="Attach image or file"
                  onClick={() => fileInputRef.current?.click()}
                >
                  {uploading ? <ImageIcon size={17} /> : <Paperclip size={17} />}
                </button>
                <input ref={fileInputRef} className="file-input" type="file" multiple onChange={sendAttachments} />
                <button className="send-button" type="submit" disabled={uploading || recordingState !== "idle" || (!draft.trim() && pendingFiles.length === 0)}>
                  <Send size={16} />
                  Send
                </button>
              </div>
              {uploadStatus && <p className="conversation-status">{uploadStatus}</p>}
            </form>
            {conversationMenuOpen && (
              <aside className="conversation-settings" onMouseDown={(event) => event.stopPropagation()}>
                <div className="conversation-members">
                  {selectedGroup ? (
                    <div className="group-settings-members">
                      {selectedGroup.members.slice(0, 9).map((member) => (
                        <button
                          className="settings-member"
                          key={member.number}
                          type="button"
                          onClick={(event) => openProfileCard(event, member, friendNumbers.has(member.number))}
                        >
                          <UserAvatar user={member} />
                          <span>{member.group_alias || displayName(member)}</span>
                        </button>
                      ))}
                      <button className="settings-member member-action" type="button" onClick={() => openContactPicker("inviteGroup")}>
                        <span className="member-action-box">
                          <Plus size={24} />
                        </span>
                        <span>Add</span>
                      </button>
                      {selectedGroup.owner === me.number && selectedGroup.members.length > 1 && (
                        <button className="settings-member member-action" type="button" onClick={() => openContactPicker("kickGroup")}>
                          <span className="member-action-box">
                            <Minus size={24} />
                          </span>
                          <span>Remove</span>
                        </button>
                      )}
                    </div>
                  ) : (
                    <button className="settings-member" type="button" onClick={(event) => openProfileCard(event, selected!, true)}>
                      <UserAvatar user={selected!} />
                      <span>{displayName(selected!)}</span>
                    </button>
                  )}
                </div>
                {selectedGroup && (
                  <div className="group-details">
                    {selectedGroup.owner === me.number && (
                      <div className="editable-row">
                        <span>Group Name</span>
                        {inlineEdit === "groupName" ? (
                          <input
                            {...noTextAssist}
                            autoFocus
                            value={groupRenameDraft}
                            onChange={(event) => setGroupRenameDraft(event.target.value)}
                            onKeyDown={(event) => {
                              if (event.key === "Enter") {
                                event.preventDefault();
                                renameGroup();
                              }
                            }}
                          />
                        ) : (
                          <strong>{groupTitle(selectedGroup)}</strong>
                        )}
                        <button
                          type="button"
                          onClick={() => {
                            if (inlineEdit === "groupName") {
                              renameGroup();
                            } else {
                              setGroupRenameDraft(groupTitle(selectedGroup));
                              setInlineEdit("groupName");
                            }
                          }}
                          title={inlineEdit === "groupName" ? "Save" : "Edit"}
                        >
                          {inlineEdit === "groupName" ? <Check size={16} /> : <Pencil size={15} />}
                        </button>
                      </div>
                    )}
                    <div className="editable-row">
                      <span>My Alias in Group</span>
                      {inlineEdit === "groupAlias" ? (
                        <input
                          {...noTextAssist}
                          autoFocus
                          value={groupAliasDraft}
                          onChange={(event) => setGroupAliasDraft(event.target.value)}
                          onKeyDown={(event) => {
                            if (event.key === "Enter") {
                              event.preventDefault();
                              saveGroupAlias();
                            }
                          }}
                        />
                      ) : (
                        <strong>{selectedGroup.my_alias || "Not set"}</strong>
                      )}
                      <button
                        type="button"
                        onClick={() => {
                          if (inlineEdit === "groupAlias") {
                            saveGroupAlias();
                          } else {
                            setGroupAliasDraft(selectedGroup.my_alias ?? "");
                            setInlineEdit("groupAlias");
                          }
                        }}
                        title={inlineEdit === "groupAlias" ? "Save" : "Edit"}
                      >
                        {inlineEdit === "groupAlias" ? <Check size={16} /> : <Pencil size={15} />}
                      </button>
                    </div>
                  </div>
                )}
                <button
                  className="settings-row"
                  type="button"
                  onClick={() => {
                    setChatSearchOpen(true);
                    setConversationMenuOpen(false);
                  }}
                >
                  <span>Search Chat History</span>
                  <span className="row-chevron">›</span>
                </button>
	                <label className="settings-row switch-row">
	                  <span>Mute Notifications</span>
	                  <input type="checkbox" checked={mutedPeers.has(selectedGroup?.id ?? selected!.number)} onChange={toggleMuteSelected} />
	                  <span className="switch-track" aria-hidden="true" />
	                </label>
                <button className="settings-row clear-row" type="button" onClick={clearConversation}>
                  Clear Chat History
                </button>
              </aside>
            )}
          </>
        ) : (
          <div className="empty-state">
            <MessageCircle size={42} />
            <h2>Select a Chat</h2>
            <p>Choose a contact from the left list.</p>
          </div>
        )}
      </section>

      {chatContextMenu && (
        <div
          className="chat-context-menu"
          style={{ left: chatContextMenu.x, top: chatContextMenu.y }}
          onPointerDown={(event) => event.stopPropagation()}
        >
          <button type="button" onClick={() => togglePinnedChat(chatContextMenu.key)}>
            {pinnedChatKeySet.has(chatContextMenu.key) ? <PinOff size={15} /> : <Pin size={15} />}
            {pinnedChatKeySet.has(chatContextMenu.key) ? "Unpin" : "Pin"}
          </button>
          <button type="button" className="danger" onClick={() => askToDeleteChat(chatContextMenu.key, chatContextMenu.title)}>
            <Trash2 size={15} />
            Delete Chat
          </button>
        </div>
      )}

      {messageContextMenu && (
        <div
          className="chat-context-menu message-context-menu"
          style={{ left: messageContextMenu.x, top: messageContextMenu.y }}
          onPointerDown={(event) => event.stopPropagation()}
        >
          {messageContextMenu.message.attachment ? (
            <>
              <button
                type="button"
                onClick={() => {
                  const attachment = messageContextMenu.message.attachment!;
                  setMessageContextMenu(null);
                  downloadAttachment(attachment);
                }}
              >
                <Download size={15} />
                Download
              </button>
              {isAudioMessage(messageContextMenu.message) && (
                <button type="button" onClick={() => transcribeAudioMessage(messageContextMenu.message)}>
                  <FileText size={15} />
                  Transcribe
                </button>
              )}
            </>
          ) : messageContextMenu.message.message ? (
            <button type="button" onClick={() => copyMessageText(messageContextMenu.message)}>
              <Copy size={15} />
              Copy
            </button>
          ) : null}
        </div>
      )}

      {confirmDialog && (
        <div className="confirm-overlay" onMouseDown={() => setConfirmDialog(null)}>
          <section className="confirm-card" onMouseDown={(event) => event.stopPropagation()}>
            <h3>{confirmDialog.title}</h3>
            <p>{confirmDialog.body}</p>
            <div className="confirm-actions">
              <button type="button" onClick={() => setConfirmDialog(null)}>
                Cancel
              </button>
              <button
                type="button"
                className={confirmDialog.destructive ? "destructive" : ""}
                onClick={confirmDialogAction}
              >
                {confirmDialog.confirmLabel}
              </button>
            </div>
          </section>
        </div>
      )}

      {callState.status !== "idle" && (
        <div className="call-overlay">
          {(() => {
            const peer = callPeerUser();
            const remoteEntries = Object.entries(remoteStreams);
            const statusLabel =
              callState.status === "incoming"
                ? `Incoming ${callState.mode === "video" ? "video" : "voice"} call`
                : callState.status === "outgoing"
                  ? "Calling..."
                  : callState.status === "connecting"
                    ? "Connecting..."
                    : callState.mode === "video"
                      ? "Video call"
                      : "Voice call";
            return (
              <section className={`call-card call-${callState.mode}`}>
                <div className="call-header">
                  {peer ? <UserAvatar user={peer} className="avatar call-avatar" /> : <span className="avatar call-avatar">{callState.peerName.charAt(0)}</span>}
                  <span>
                    <strong>{callState.peerName}</strong>
                    <small>{statusLabel}</small>
                  </span>
                </div>
                <div className="call-media">
                  {callState.mode === "video" ? (
                    <>
                      <div className="remote-video-grid">
                        {remoteEntries.length > 0 ? (
                          remoteEntries.map(([number, stream]) => (
                            <video
                              key={number}
                              ref={(node) => {
                                if (node) {
                                  node.srcObject = stream;
                                }
                              }}
                              className="remote-video"
                              autoPlay
                              playsInline
                            />
                          ))
                        ) : (
                          <div className="remote-video-placeholder">Waiting for video...</div>
                        )}
                      </div>
                      <video ref={localVideoRef} className="local-video" autoPlay muted playsInline />
                    </>
                  ) : (
                    <>
                      {remoteEntries.map(([number, stream]) => (
                        <audio
                          key={number}
                          ref={(node) => {
                            if (node) {
                              node.srcObject = stream;
                            }
                          }}
                          className="call-hidden-media"
                          autoPlay
                        />
                      ))}
                      <div className="voice-call-mark">
                        <Phone size={28} />
                      </div>
                    </>
                  )}
                </div>
                <div className="call-actions">
                  {callState.status === "incoming" ? (
                    <>
                      <button className="call-action accept" type="button" onClick={acceptCall}>
                        <Phone size={17} />
                        Accept
                      </button>
                      <button className="call-action decline" type="button" onClick={rejectCall}>
                        <PhoneOff size={17} />
                        Decline
                      </button>
                    </>
                  ) : (
                    <button className="call-action decline" type="button" onClick={() => finishCall(true)}>
                      <PhoneOff size={17} />
                      Hang Up
                    </button>
                  )}
                </div>
              </section>
            );
          })()}
        </div>
      )}

      {profileCard && (
        <div className="profile-backdrop" onClick={() => setProfileCard(null)}>
          {(() => {
            const marker = genderMarker(profileCard.user);
            return (
              <section
                className="profile-card"
                style={{ left: profileCard.x, top: profileCard.y }}
                onClick={(event) => event.stopPropagation()}
              >
                <div className="profile-top">
                  <UserAvatar user={profileCard.user} className="profile-avatar" />
                  <div className="profile-title">
                    <h2>
                      {displayName(profileCard.user)}
                      {marker && (
                        <span className={`gender-marker ${marker.className}`} aria-label={marker.label}>
                          {marker.symbol}
                        </span>
                      )}
                    </h2>
                    <p>Name: {profileCard.user.nickname || profileCard.user.number}</p>
                    <p>FeaChat ID: {profileCard.user.number}</p>
                  </div>
                </div>
                {profileCard.canDelete && (
                  <>
                    <button className="profile-more" type="button" onClick={() => setProfileMenuOpen((open) => !open)}>
                      <MoreHorizontal size={20} />
                    </button>
                    {profileMenuOpen && (
                      <div className="profile-menu">
                        <button type="button" onClick={deleteFromProfile}>
                          Delete Friend
                        </button>
                      </div>
                    )}
                  </>
                )}
                <div className="profile-meta">
                  <div className="editable-row profile-editable-row">
                    <span>Alias</span>
                    {inlineEdit === "profileAlias" ? (
                      <input
                        {...noTextAssist}
                        autoFocus
                        value={profileAliasDraft}
                        onChange={(event) => setProfileAliasDraft(event.target.value)}
                        onKeyDown={(event) => {
                          if (event.key === "Enter") {
                            event.preventDefault();
                            saveFriendProfile();
                          }
                        }}
                      />
                    ) : (
                      <strong>{profileCard.user.alias || "None"}</strong>
                    )}
                    {profileCard.canDelete && (
                      <button
                        type="button"
                        onClick={() => {
                          if (inlineEdit === "profileAlias") {
                            saveFriendProfile();
                          } else {
                            setProfileAliasDraft(profileCard.user.alias ?? "");
                            setInlineEdit("profileAlias");
                          }
                        }}
                        title={inlineEdit === "profileAlias" ? "Save" : "Edit"}
                      >
                        {inlineEdit === "profileAlias" ? <Check size={15} /> : <Pencil size={14} />}
                      </button>
                    )}
                  </div>
                  <div className="editable-row profile-editable-row">
                    <span>Tags</span>
                    {inlineEdit === "profileTags" ? (
                      <input
                        {...noTextAssist}
                        autoFocus
                        value={profileTagsDraft}
                        placeholder="family, school, work"
                        onChange={(event) => setProfileTagsDraft(event.target.value)}
                        onKeyDown={(event) => {
                          if (event.key === "Enter") {
                            event.preventDefault();
                            saveFriendProfile();
                          }
                        }}
                      />
                    ) : (
                      <strong>{profileCard.user.tags?.length ? profileCard.user.tags.join(", ") : "None"}</strong>
                    )}
                    {profileCard.canDelete && (
                      <button
                        type="button"
                        onClick={() => {
                          if (inlineEdit === "profileTags") {
                            saveFriendProfile();
                          } else {
                            setProfileTagsDraft((profileCard.user.tags ?? []).join(", "));
                            setInlineEdit("profileTags");
                          }
                        }}
                        title={inlineEdit === "profileTags" ? "Save" : "Edit"}
                      >
                        {inlineEdit === "profileTags" ? <Check size={15} /> : <Pencil size={14} />}
                      </button>
                    )}
                  </div>
                </div>
                {profileCard.relation === "friend" && (
                  <div className="profile-actions">
                    <button type="button" onClick={messageFromProfile}>
                      Send Message
                    </button>
                  </div>
                )}
                {profileCard.relation === "stranger" && (
                  <div className="profile-actions">
                    <button type="button" onClick={() => requestFriend(profileCard.user.number)}>
                      Request Friend
                    </button>
                  </div>
                )}
                {profileStatus && <span className="profile-status">{profileStatus}</span>}
              </section>
            );
          })()}
        </div>
      )}

      {contactPickerMode && (
        <div className="contact-picker-backdrop" onClick={closeContactPicker}>
          <section className="contact-picker" onClick={(event) => event.stopPropagation()}>
            <div className="picker-left">
              <div className="picker-search">
                <Search size={18} />
                <input
                  {...noTextAssist}
                  autoFocus
                  value={contactPickerSearch}
                  placeholder="Search"
                  onChange={(event) => setContactPickerSearch(event.target.value)}
                />
              </div>
              <div className="picker-contact-list">
                {contactPickerGroups.map((group) => (
                  <div className="picker-group" key={group.key}>
                    <div className="picker-letter">{group.key}</div>
                    {group.people.map((person) => {
                      const fixed = contactPickerMode === "inviteGroup" && selectedGroupMemberNumbers.has(person.number);
                      const checked = fixed || pickedContacts.includes(person.number);
                      return (
                        <button
                          className={`picker-person ${checked ? "checked" : ""} ${fixed ? "fixed" : ""}`}
                          key={person.number}
                          type="button"
                          disabled={fixed}
                          onClick={() => togglePickedContact(person.number)}
                        >
                          <span className="picker-check">{checked && <Check size={16} />}</span>
                          <UserAvatar user={person} className="avatar picker-avatar" />
                          <strong>{displayName(person)}</strong>
                        </button>
                      );
                    })}
                  </div>
                ))}
              </div>
            </div>
            <div className="picker-right">
              <header>
                <h2>{contactPickerTitle}</h2>
                <span>{pickedContacts.length} contact(s) selected</span>
              </header>
              <div className="picked-list">
                {pickedUsers.map((person) => (
                  <button key={person.number} type="button" onClick={() => togglePickedContact(person.number)}>
                    <UserAvatar user={person} className="avatar picker-avatar" />
                    <strong>{displayName(person)}</strong>
                    <X size={15} />
                  </button>
                ))}
              </div>
              <footer>
                <button type="button" className="picker-cancel" onClick={closeContactPicker}>
                  Cancel
                </button>
                <button type="button" className="picker-finish" disabled={pickedContacts.length === 0} onClick={confirmContactPicker}>
                  {contactPickerAction}
                </button>
              </footer>
            </div>
          </section>
        </div>
      )}

      {settingsOpen && (
        <div className="settings-backdrop" onClick={() => setSettingsOpen(false)}>
          <section className="settings-panel" onClick={(event) => event.stopPropagation()}>
            <header>
              <h2>Settings</h2>
              <button onClick={() => setSettingsOpen(false)}>
                <X size={18} />
              </button>
            </header>
            <div className="settings-body">
              <nav className="settings-nav" aria-label="Settings sections">
                <button
                  className={settingsSection === "account" ? "selected" : ""}
                  type="button"
                  onClick={() => setSettingsSection("account")}
                >
                  Account
                </button>
                <button
                  className={settingsSection === "appearance" ? "selected" : ""}
                  type="button"
                  onClick={() => setSettingsSection("appearance")}
                >
                  Appearance
                </button>
              </nav>
              <div className="settings-content">
                {settingsSection === "account" ? (
                  <form className="account-settings" onSubmit={saveAccountSettings}>
                    <div className="account-avatar-row">
                      <UserAvatar user={me} className="profile-avatar" />
                      <div>
                        <strong>{displayName(me)}</strong>
                        <small>{me.number}</small>
                        <button type="button" onClick={() => avatarInputRef.current?.click()}>
                          Change Avatar
                        </button>
                        <input ref={avatarInputRef} className="file-input" type="file" accept="image/*" onChange={uploadAccountAvatar} />
                      </div>
                    </div>
                    <label>
                      Display Name
                      <input {...noTextAssist} value={accountNameDraft} onChange={(event) => setAccountNameDraft(event.target.value)} />
                    </label>
                    <div className="password-fields">
                      <label>
                        Current Password
                        <input
                          {...noTextAssist}
                          type="password"
                          value={currentPasswordDraft}
                          onChange={(event) => setCurrentPasswordDraft(event.target.value)}
                        />
                      </label>
                      <label>
                        New Password
                        <input
                          {...noTextAssist}
                          type="password"
                          value={newPasswordDraft}
                          onChange={(event) => setNewPasswordDraft(event.target.value)}
                        />
                      </label>
                      <label>
                        Confirm Password
                        <input
                          {...noTextAssist}
                          type="password"
                          value={confirmPasswordDraft}
                          onChange={(event) => setConfirmPasswordDraft(event.target.value)}
                        />
                      </label>
                    </div>
                    <button className="settings-save" type="submit">
                      Save Account
                    </button>
                    {(accountStatus || accountError) && (
                      <p className={`settings-note ${accountError ? "error" : ""}`}>{accountError || accountStatus}</p>
                    )}
                  </form>
                ) : (
                  <div className="settings-section">
                    <h3>Appearance</h3>
                    <div className="theme-options">
                      <button className={theme === "classic" ? "selected" : ""} onClick={() => applyTheme("classic")}>
                        <span className="theme-preview classic-preview" />
                        <strong>Classic Blue</strong>
                        <small>Original FeaChat blue and white</small>
                      </button>
                      <button className={theme === "dark" ? "selected" : ""} onClick={() => applyTheme("dark")}>
                        <span className="theme-preview dark-preview" />
                        <strong>Dark Sidebar</strong>
                        <small>Current WeChat-style dark rail</small>
                      </button>
                    </div>
                    <p className="settings-note">Saved locally for {displayName(me)}.</p>
                  </div>
                )}
              </div>
            </div>
          </section>
        </div>
      )}
    </main>
  );
}
