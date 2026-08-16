import { closeWindow, minimizeWindow, toggleMaximizeWindow } from "../lib/window";

export function WindowControls() {
  return (
    <div className="window-controls" aria-label="Window controls">
      <button className="window-control close" type="button" aria-label="Close" onClick={closeWindow} />
      <button className="window-control minimize" type="button" aria-label="Minimize" onClick={minimizeWindow} />
      <button className="window-control maximize" type="button" aria-label="Maximize" onClick={toggleMaximizeWindow} />
    </div>
  );
}
