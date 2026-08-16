import { useEffect, useState } from "react";

import { closeWindow, minimizeWindow, toggleMaximizeWindow } from "../lib/window";

export function WindowControls() {
  const [focused, setFocused] = useState(() => document.hasFocus());

  useEffect(() => {
    const markFocused = () => setFocused(true);
    const markBlurred = () => setFocused(false);
    window.addEventListener("focus", markFocused);
    window.addEventListener("blur", markBlurred);
    return () => {
      window.removeEventListener("focus", markFocused);
      window.removeEventListener("blur", markBlurred);
    };
  }, []);

  return (
    <div className={`window-controls ${focused ? "focused" : "inactive"}`} aria-label="Window controls">
      <button className="window-control close" type="button" aria-label="Close" onClick={closeWindow} />
      <button className="window-control minimize" type="button" aria-label="Minimize" onClick={minimizeWindow} />
      <button className="window-control maximize" type="button" aria-label="Maximize" onClick={toggleMaximizeWindow} />
    </div>
  );
}
