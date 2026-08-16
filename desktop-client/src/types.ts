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
};

export type Conversation = {
  id: string;
  type: "direct" | "group";
  title: string;
  peer: User | null;
  members: ConversationMember[];
  owner: string | null;
  my_alias: string;
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
