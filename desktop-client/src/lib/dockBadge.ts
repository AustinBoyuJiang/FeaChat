import { getCurrentWindow } from "@tauri-apps/api/window";

export function setDockUnreadBadge(count: number) {
  getCurrentWindow()
    .setBadgeCount(count > 0 ? count : undefined)
    .catch(() => undefined);
}
