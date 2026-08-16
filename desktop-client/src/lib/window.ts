import { currentMonitor, getCurrentWindow, PhysicalPosition, PhysicalSize } from "@tauri-apps/api/window";
import type { MouseEvent } from "react";

type WindowBounds = {
  position: PhysicalPosition;
  size: PhysicalSize;
};

let restoreBounds: WindowBounds | null = null;

export function startWindowDrag(event: MouseEvent<HTMLElement>) {
  if (event.button !== 0) {
    return;
  }
  if (event.detail > 1) {
    return;
  }
  if ((event.target as HTMLElement).closest("button, input, textarea, a")) {
    return;
  }
  getCurrentWindow().startDragging().catch(() => undefined);
}

export function toggleMaximizeFromDragArea(event: MouseEvent<HTMLElement>) {
  if ((event.target as HTMLElement).closest("button, input, textarea, a")) {
    return;
  }
  toggleWindowZoom();
}

export async function toggleWindowZoom() {
  const window = getCurrentWindow();
  try {
    if (restoreBounds) {
      const { position, size } = restoreBounds;
      restoreBounds = null;
      await window.setSize(size);
      await window.setPosition(position);
      return;
    }

    const monitor = await currentMonitor();
    if (!monitor) {
      await window.toggleMaximize();
      return;
    }

    restoreBounds = {
      position: await window.outerPosition(),
      size: await window.outerSize()
    };

    await window.setSize(new PhysicalSize(monitor.workArea.size.width, monitor.workArea.size.height));
    await window.setPosition(new PhysicalPosition(monitor.workArea.position.x, monitor.workArea.position.y));
  } catch {
    restoreBounds = null;
    window.toggleMaximize().catch(() => undefined);
  }
}

export function minimizeWindow() {
  getCurrentWindow().minimize().catch(() => undefined);
}

export function toggleMaximizeWindow() {
  toggleWindowZoom();
}

export function closeWindow() {
  getCurrentWindow().close().catch(() => undefined);
}
