// frontend/widget/src/Mount.tsx
import React from "react";
import ReactDOM from "react-dom/client";
import RoomMatcherWidget, { RoomMatcherWidgetProps } from "./RoomMatcherWidget";

export function mount(selectorOrEl: string | Element, props?: RoomMatcherWidgetProps) {
  const el =
    typeof selectorOrEl === "string" ? document.querySelector(selectorOrEl) : selectorOrEl;
  if (!el) return;
  const root = ReactDOM.createRoot(el as Element);
  root.render(<RoomMatcherWidget {...props} />);
}

export type { RoomMatcherWidgetProps };

// provide global for <script> usage
declare global {
  interface Window {
    RoomMatcher: { mount: typeof mount };
  }
}

if (typeof window !== "undefined") {
  (window as any).RoomMatcher = { mount };
}
