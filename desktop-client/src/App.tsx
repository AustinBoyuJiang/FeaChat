import { ChangeEvent, FormEvent, Fragment, MouseEvent, useEffect, useMemo, useRef, useState } from "react";
import {
  Aperture,
  Check,
  CircleUserRound,
  FileText,
  Image as ImageIcon,
  Menu,
  LogOut,
  MessageCircle,
  MessageSquare,
  Minus,
  MoreHorizontal,
  Paperclip,
  Pencil,
  Plus,
  Search,
  Send,
  Settings,
  UserPlus,
  X
} from "lucide-react";

import { api } from "./api";
import { getCurrentWindow } from "@tauri-apps/api/window";
import {
  clearCachedMessages,
  mergeCachedMessages,
  readCachedMessages,
  readTheme,
  writeCachedMessages,
  writeTheme,
  type Theme
} from "./cache";
import type { Conversation, FriendRequest, FriendRequestRecord, GroupInvite, Message, User } from "./types";

type AuthMode = "login" | "register";
type Section = "chats" | "contacts" | "newFriends" | "moments";
type ProfileRelation = "self" | "friend" | "stranger";
type ContactPickerMode = "createGroup" | "inviteGroup" | "kickGroup";
type InlineEditTarget = "profileAlias" | "profileTags" | "groupAlias" | "groupName";
type SettingsSection = "account" | "appearance";

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
const MESSAGE_TIME_GAP_SECONDS = 300;
const noTextAssist = {
  autoCapitalize: "none",
  autoCorrect: "off",
  spellCheck: false
} as const;

function displayName(user: User) {
  return user.display_name || user.alias || user.nickname || user.number;
}

function letterAvatarSrc(label: string, color = "#0076f6") {
  const letter = (label.trim().charAt(0) || "?").toUpperCase();
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="96" height="96" viewBox="0 0 96 96"><rect width="96" height="96" rx="12" fill="${color}"/><text x="48" y="58" text-anchor="middle" font-family="-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif" font-size="42" font-weight="700" fill="#fff">${letter}</text></svg>`;
  return `data:image/svg+xml;charset=utf-8,${encodeURIComponent(svg)}`;
}

function userAvatarSrc(user: User) {
  return user.avatar_url ? api.fileUrl(user.avatar_url) : letterAvatarSrc(displayName(user), user.avatar_color || "#0076f6");
}

function groupTitle(conversation: Conversation) {
  return conversation.title || conversation.members.map((member) => displayName(member)).join(", ") || "Group Chat";
}

function conversationTitle(conversation: Conversation) {
  return conversation.type === "group" ? groupTitle(conversation) : conversation.peer ? displayName(conversation.peer) : conversation.title;
}

function UserAvatar({ user, className = "avatar small" }: { user: User; className?: string }) {
  return <img className={className} src={userAvatarSrc(user)} alt="" draggable={false} />;
}

function GroupAvatar({ conversation, className = "avatar small group-avatar" }: { conversation: Conversation; className?: string }) {
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

function genderMarker(user: User) {
  if (user.gender === "female") {
    return { label: "Female", symbol: "♀", className: "female" };
  }
  if (user.gender === "male") {
    return { label: "Male", symbol: "♂", className: "male" };
  }
  return null;
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

function parseMessageTime(value: string) {
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

function formatMessageTimestamp(value: string) {
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

function shouldShowTimestamp(messages: Message[], index: number) {
  if (index === 0) {
    return true;
  }
  const current = parseMessageTime(messages[index].time).getTime();
  const previous = parseMessageTime(messages[index - 1].time).getTime();
  return current - previous >= MESSAGE_TIME_GAP_SECONDS * 1000;
}

function sortMessages(messages: Message[]) {
  return [...messages].sort((a, b) => {
    const byTime = parseMessageTime(a.time).getTime() - parseMessageTime(b.time).getTime();
    return byTime === 0 ? a.id - b.id : byTime;
  });
}

function formatBytes(size: number) {
  if (size < 1024) {
    return `${size} B`;
  }
  if (size < 1024 * 1024) {
    return `${(size / 1024).toFixed(1)} KB`;
  }
  return `${(size / 1024 / 1024).toFixed(1)} MB`;
}

function messagePreview(message: Message) {
  if (message.type === "group_invite") {
    return "[Group Invite]";
  }
  if (message.attachment) {
    return message.type === "image" ? `[Image] ${message.attachment.name}` : `[File] ${message.attachment.name}`;
  }
  return message.message || "[Message]";
}

function parseGroupInviteMessage(message: Message) {
  if (message.type !== "group_invite") {
    return null;
  }
  try {
    return JSON.parse(message.message) as { invite_id: number; conversation_id: string; title: string; inviter: string };
  } catch {
    return null;
  }
}

function contactGroupKey(user: User) {
  const first = displayName(user).trim().charAt(0).toUpperCase();
  return /^[A-Z]$/.test(first) ? first : "Others";
}

function readMutedPeers(number: string) {
  const raw = localStorage.getItem(`feachat.muted.${number}`);
  if (!raw) {
    return new Set<string>();
  }
  try {
    return new Set(JSON.parse(raw) as string[]);
  } catch {
    return new Set<string>();
  }
}

function writeMutedPeers(number: string, muted: Set<string>) {
  localStorage.setItem(`feachat.muted.${number}`, JSON.stringify([...muted]));
}

function isImageMessage(message: Message) {
  return message.type === "image" || message.attachment?.mime_type.startsWith("image/");
}

function startWindowDrag(event: MouseEvent<HTMLElement>) {
  if (event.button !== 0) {
    return;
  }
  if ((event.target as HTMLElement).closest("button, input, textarea, a")) {
    return;
  }
  getCurrentWindow().startDragging().catch(() => undefined);
}

function minimizeWindow() {
  getCurrentWindow().minimize().catch(() => undefined);
}

function toggleMaximizeWindow() {
  getCurrentWindow().toggleMaximize().catch(() => undefined);
}

function closeWindow() {
  getCurrentWindow().close().catch(() => undefined);
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
  const [chatSearchOpen, setChatSearchOpen] = useState(false);
  const [chatSearchQuery, setChatSearchQuery] = useState("");
  const [mutedPeers, setMutedPeers] = useState<Set<string>>(() => (me ? readMutedPeers(me.number) : new Set()));
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
  const wsRef = useRef<WebSocket | null>(null);
  const bottomRef = useRef<HTMLDivElement | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const avatarInputRef = useRef<HTMLInputElement | null>(null);
  const appMenuRef = useRef<HTMLDivElement | null>(null);
  const addMenuRef = useRef<HTMLDivElement | null>(null);

  const selectedNumber = selected?.number;
  const selectedGroupId = selectedGroup?.id;

  function clearTransientUi() {
    setStatus("");
    setQuery("");
    setAddFriendOpen(false);
    setAddMenuOpen(false);
    setAddQuery("");
    setAddSearchResults([]);
    setInlineEdit(null);
  }

  async function loadContacts(activeToken = token) {
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
    setMessages(readCachedMessages(me.number, peer.number));
    try {
      const response = await api.messages(token, peer.number);
      const nextMessages = uniqueMessages(response.messages);
      writeCachedMessages(me.number, peer.number, nextMessages);
      setMessages(readCachedMessages(me.number, peer.number));
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
    setGroupAliasDraft(group.my_alias ?? "");
    setGroupRenameDraft(groupTitle(group));
    setMessages(readCachedMessages(me.number, group.id));
    try {
      const response = await api.conversationMessages(token, group.id);
      const nextMessages = uniqueMessages(response.messages);
      writeCachedMessages(me.number, group.id, nextMessages);
      setMessages(readCachedMessages(me.number, group.id));
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
      await loadContacts(response.token);
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
    setMessages([]);
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
      setMessages([]);
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
    if ((!selected && !selectedGroup) || !me) {
      return;
    }
    clearCachedMessages(me.number, selectedGroup?.id ?? selected!.number);
    setMessages([]);
    setConversationMenuOpen(false);
    setChatSearchQuery("");
    setChatSearchOpen(false);
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

  async function sendMessage(event: FormEvent) {
    event.preventDefault();
    if (!token || (!selected && !selectedGroup) || uploading || (!draft.trim() && pendingFiles.length === 0)) {
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
      setMessages((current) => {
        const nextMessages = uniqueMessages([...current, response.message]);
        if (me) {
          writeCachedMessages(me.number, selectedGroup?.id ?? selected!.number, nextMessages);
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
        setMessages((current) => {
          const nextMessages = uniqueMessages([...current, response.message]);
          if (me) {
            writeCachedMessages(me.number, selectedGroup?.id ?? selected!.number, nextMessages);
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

  useEffect(() => {
    if (!token) {
      return;
    }
    loadContacts().catch((error) => {
      if (error instanceof Error && error.message === "Not authenticated") {
        logout();
        return;
      }
      setStatus(error instanceof Error ? error.message : "Failed to load contacts");
    });
  }, [token]);

  useEffect(() => {
    if (!token) {
      return;
    }
    const interval = window.setInterval(() => {
      loadContacts(token).catch(() => undefined);
    }, 5000);
    return () => window.clearInterval(interval);
  }, [token]);

  useEffect(() => {
    if (!me) {
      return;
    }
    setTheme(readTheme(me.number));
    setMutedPeers(readMutedPeers(me.number));
  }, [me?.number]);

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
        if (me?.number) {
          mergeCachedMessages(me.number, peer, [message]);
        }
        setMessages((current) => {
          if (groupId ? groupId !== selectedGroupId : peer !== selectedNumber) {
            return current;
          }
          return uniqueMessages([...current, message]);
        });
        loadContacts().catch(() => undefined);
      }
    };
    return () => {
      socket.close();
    };
  }, [token, me?.number, selectedNumber, selectedGroupId]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages]);

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
  const conversationPreviews = useMemo(() => {
    if (!me) {
      return {};
    }
    return Object.fromEntries(
      [
        ...friends.map((friend) => {
        const source = selected?.number === friend.number ? orderedMessages : sortMessages(readCachedMessages(me.number, friend.number));
        const last = source.at(-1);
        return [
          friend.number,
          last
            ? {
                text: messagePreview(last),
                time: formatMessageTimestamp(last.time)
              }
            : { text: "No messages yet" }
        ];
        }),
        ...groupConversations.map((conversation) => {
          const source =
            selectedGroup?.id === conversation.id
              ? orderedMessages
              : sortMessages(readCachedMessages(me.number, conversation.id));
          const last = source.at(-1) ?? conversation.last_message;
          return [
            conversation.id,
            last
              ? {
                  text: messagePreview(last),
                  time: formatMessageTimestamp(last.time)
                }
              : { text: "No messages yet" }
          ];
        })
      ]
    );
  }, [friends, groupConversations, me?.number, orderedMessages, selected?.number, selectedGroup?.id]);
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

  if (!token || !me) {
    return (
      <main className="auth-shell">
        <div className="window-controls" aria-label="Window controls">
          <button className="window-control close" type="button" aria-label="Close" onClick={closeWindow} />
          <button className="window-control minimize" type="button" aria-label="Minimize" onClick={minimizeWindow} />
          <button className="window-control maximize" type="button" aria-label="Maximize" onClick={toggleMaximizeWindow} />
        </div>
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
    <main className={`app-shell theme-${theme}`}>
      <div className="window-controls" aria-label="Window controls">
        <button className="window-control close" type="button" aria-label="Close" onClick={closeWindow} />
        <button className="window-control minimize" type="button" aria-label="Minimize" onClick={minimizeWindow} />
        <button className="window-control maximize" type="button" aria-label="Maximize" onClick={toggleMaximizeWindow} />
      </div>
      <aside className="rail" onMouseDown={startWindowDrag}>
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
        </button>
        <button
          title="Contacts"
          className={`rail-button ${activeSection === "contacts" || activeSection === "newFriends" ? "active" : ""}`}
          onClick={() => {
            setActiveSection("contacts");
            setSelected(null);
            setSelectedGroup(null);
            setMessages([]);
            clearTransientUi();
          }}
        >
          <CircleUserRound size={21} />
        </button>
        <button
          title="Moments"
          className={`rail-button ${activeSection === "moments" ? "active" : ""}`}
          onClick={() => {
            setActiveSection("moments");
            setSelected(null);
            setSelectedGroup(null);
            setMessages([]);
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
        <div className="search-row" onMouseDown={startWindowDrag}>
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
                        setMessages([]);
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
                    {contactGroups.map((group) => (
                      <div className="contact-group" key={group.key}>
                        <div className="contact-letter">{group.key}</div>
                        {group.people.map((friend) => (
                          <button
                            key={friend.number}
                            className={`person-row contact-row ${selected?.number === friend.number ? "selected" : ""}`}
                            onClick={() => loadMessages(friend)}
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
                    {groupConversations.map((conversation) => (
                      <button
                        key={conversation.id}
                        className={`person-row ${selectedGroup?.id === conversation.id ? "selected" : ""}`}
                        onClick={() => loadGroupMessages(conversation)}
                      >
                        <GroupAvatar conversation={conversation} />
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
                    ))}
                    {filteredFriends.map((friend) => (
                      <button
                        key={friend.number}
                        className={`person-row ${selected?.number === friend.number ? "selected" : ""}`}
                        onClick={() => loadMessages(friend)}
                      >
                        <UserAvatar user={friend} />
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
                    ))}
                  </>
                )}
              </div>
            </div>
          </>
        )}
      </section>

      <section className="conversation">
        <header className="conversation-header" onMouseDown={startWindowDrag}>
          {selected || selectedGroup ? (
            <>
              <h2>{selectedGroup ? groupTitle(selectedGroup) : displayName(selected!)}</h2>
              <div className="conversation-tools">
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
                      <div className={`bubble ${message.attachment ? "with-attachment" : ""} ${inviteCard ? "invite-bubble" : ""}`}>
                        {inviteCard ? (
                          <div className="group-invite-card">
                            <strong>{inviteCard.title}</strong>
                            <small>Group invitation from {inviteCard.inviter}</small>
                            {invitePending ? (
                              <button type="button" onClick={() => acceptInvite(inviteCard.invite_id)}>
                                Accept Invite
                              </button>
                            ) : (
                              <span className="invite-state">{inviteJoined ? "Joined" : "Invite Used"}</span>
                            )}
                          </div>
                        ) : message.attachment ? (
                          isImageMessage(message) ? (
                            <a className="image-message" href={api.fileUrl(message.attachment.url)} target="_blank">
                              <img src={api.fileUrl(message.attachment.url)} alt={message.attachment.name} />
                              <span>{message.attachment.name}</span>
                            </a>
                          ) : (
                            <a className="file-message" href={api.fileUrl(message.attachment.url, true)} target="_blank">
                              <FileText size={22} />
                              <span>
                                <strong>{message.attachment.name}</strong>
                                <small>{formatBytes(message.attachment.size)}</small>
                              </span>
                            </a>
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
              <div className="composer-actions">
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
                <button className="send-button" type="submit" disabled={uploading || (!draft.trim() && pendingFiles.length === 0)}>
                  <Send size={16} />
                  Send
                </button>
              </div>
              {(uploadStatus || uploadError) && (
                <p className={`conversation-status ${uploadError ? "error" : ""}`}>{uploadStatus || uploadError}</p>
              )}
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
                  {profileCard.canDelete && (
                    <>
                      <button className="profile-more" type="button" onClick={() => setProfileMenuOpen((open) => !open)}>
                        <MoreHorizontal size={22} />
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
                </div>
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
