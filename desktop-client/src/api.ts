import * as account from "./api/account";
import * as auth from "./api/auth";
import * as conversations from "./api/conversations";
import * as friends from "./api/friends";
import { API_URL, fileUrl, wsUrl } from "./api/client";

export const api = {
  apiUrl: API_URL,
  fileUrl,
  wsUrl,
  ...account,
  ...auth,
  ...conversations,
  ...friends
};
