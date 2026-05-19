import type { JSX } from 'react';

type IconName =
  | 'flask' | 'shield' | 'plus' | 'send' | 'sparkles' | 'chevron'
  | 'external' | 'alert' | 'info' | 'ban' | 'siren' | 'question'
  | 'history' | 'menu' | 'settings' | 'book' | 'droplet' | 'fire';

interface IconProps {
  name: IconName;
  size?: number;
  stroke?: number;
}

const PATHS: Record<IconName, JSX.Element> = {
  flask: <g><path d="M9 3h6"/><path d="M10 3v6L4 19a2 2 0 0 0 1.8 3h12.4A2 2 0 0 0 20 19L14 9V3"/><path d="M7 14h10"/></g>,
  shield: <path d="M12 3l8 3v6c0 5-3.5 8.5-8 9-4.5-.5-8-4-8-9V6l8-3z"/>,
  plus: <g><path d="M12 5v14"/><path d="M5 12h14"/></g>,
  send: <g><path d="M22 2L11 13"/><path d="M22 2l-7 20-4-9-9-4 20-7z"/></g>,
  sparkles: <g><path d="M12 3v4"/><path d="M12 17v4"/><path d="M3 12h4"/><path d="M17 12h4"/><path d="M5.6 5.6l2.8 2.8"/><path d="M15.6 15.6l2.8 2.8"/><path d="M5.6 18.4l2.8-2.8"/><path d="M15.6 8.4l2.8-2.8"/></g>,
  chevron: <path d="M9 6l6 6-6 6"/>,
  external: <g><path d="M15 3h6v6"/><path d="M10 14L21 3"/><path d="M21 14v5a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5"/></g>,
  alert: <g><path d="M12 9v4"/><path d="M12 17h.01"/><path d="M10.3 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/></g>,
  info: <g><circle cx="12" cy="12" r="9"/><path d="M12 8h.01"/><path d="M11 12h1v5h1"/></g>,
  ban: <g><circle cx="12" cy="12" r="9"/><path d="M5.6 5.6l12.8 12.8"/></g>,
  siren: <g><path d="M7 12V8a5 5 0 0 1 10 0v4"/><rect x="4" y="12" width="16" height="8" rx="2"/><path d="M12 16v.01"/></g>,
  question: <g><circle cx="12" cy="12" r="9"/><path d="M9.1 9a3 3 0 1 1 5.8 1c0 2-3 2-3 4"/><path d="M12 17h.01"/></g>,
  history: <g><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></g>,
  menu: <g><path d="M4 6h16"/><path d="M4 12h16"/><path d="M4 18h16"/></g>,
  settings: <g><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.7 1.7 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-1.8-.3 1.7 1.7 0 0 0-1 1.5V21a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 0-1.1-1.5 1.7 1.7 0 0 0-1.8.3l-.1.1A2 2 0 1 1 4.3 17l.1-.1a1.7 1.7 0 0 0 .3-1.8 1.7 1.7 0 0 0-1.5-1H3a2 2 0 1 1 0-4h.1a1.7 1.7 0 0 0 1.5-1.1 1.7 1.7 0 0 0-.3-1.8l-.1-.1A2 2 0 1 1 7 4.3l.1.1a1.7 1.7 0 0 0 1.8.3H9a1.7 1.7 0 0 0 1-1.5V3a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.8-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0-.3 1.8V9a1.7 1.7 0 0 0 1.5 1H21a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1.5 1z"/></g>,
  book: <g><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/></g>,
  droplet: <path d="M12 2.7s7 7 7 12a7 7 0 0 1-14 0c0-5 7-12 7-12z"/>,
  fire: <path d="M12 2s4 4 4 8a4 4 0 0 1-8 0c0-2 2-3 2-5 0-2-2-3-2-3s4 0 4 0zM6 14a6 6 0 0 0 12 0c0-3-3-6-3-6"/>,
};

export default function Icon({ name, size = 16, stroke = 1.8 }: IconProps) {
  return (
    <svg
      viewBox="0 0 24 24"
      width={size}
      height={size}
      fill="none"
      stroke="currentColor"
      strokeWidth={stroke}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      {PATHS[name]}
    </svg>
  );
}

export type { IconName };
