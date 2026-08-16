export type User = {
  number: string;
  nickname: string;
  gender?: "male" | "female" | "unknown";
  alias?: string;
  tags?: string[];
  display_name?: string;
  avatar: number | null;
  avatar_color: string;
  avatar_url?: string | null;
  background: number | null;
  motto: string;
};

export type Message = {
  id: number;
  conversation_id?: string | null;
  sender: string;
  receiver: string;
  time: string;
  type: string;
  message: string;
  attachment: {
    name: string;
    url: string;
    mime_type: string;
    size: number;
  } | null;
};

export type FriendRequest = User & {
  created_at: string;
};

export type FriendRequestRecord = User & {
  requester: string;
  receiver: string;
  direction: "incoming" | "outgoing";
  status: "pending" | "accepted" | "rejected";
  created_at: string;
  updated_at: string;
};

export type ConversationMember = User & {
  role: "owner" | "member";
  group_alias: string;
  joined_at?: string;
};

export type Conversation = {
  id: string;
  type: "direct" | "group";
  title: string;
  peer: User | null;
  members: ConversationMember[];
  owner: string | null;
  my_alias: string;
  status?: "active" | "inactive" | "dissolved";
  my_status?: "active" | "left";
  last_message: Message | null;
};

export type GroupInvite = {
  id: number;
  conversation_id: string;
  inviter: string;
  invitee: string;
  status: "pending" | "accepted" | "rejected";
  created_at: string;
  updated_at: string;
  conversation: {
    id: string;
    title: string;
    owner: string;
    members: ConversationMember[];
  };
};

export type MomentImage = {
  id: number;
  name: string;
  url: string;
  mime_type: string;
  size: number;
};

export type MomentComment = {
  id: number;
  post_id: number;
  author: User;
  body: string;
  created_at: string;
};

export type MomentPost = {
  id: number;
  author: User;
  body: string;
  images: MomentImage[];
  likes: User[];
  liked_by_me: boolean;
  comments: MomentComment[];
  created_at: string;
  updated_at: string;
};

export type MomentNotification = {
  id: number;
  post_id: number;
  type: "like" | "comment";
  is_read: boolean;
  created_at: string;
  actor: User;
  comment_body: string;
  post_body: string;
  post_image: {
    name: string;
    url: string;
    mime_type: string;
    size: number;
  } | null;
};

export type MomentProfileSummary = {
  user: User;
  images: MomentImage[];
};
