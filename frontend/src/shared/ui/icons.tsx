import type { SVGProps } from "react";

/** Footer va ulashish tugmalari uchun kichik SVG ikonkalar (tashqi kutubxonasiz, currentColor bilan). */
type IconProps = SVGProps<SVGSVGElement>;
const base = { viewBox: "0 0 24 24", "aria-hidden": true, focusable: false } as const;
const stroke = { fill: "none", stroke: "currentColor", strokeWidth: 2, strokeLinecap: "round", strokeLinejoin: "round" } as const;

export function TelegramIcon(props: IconProps) {
  return <svg {...base} {...props}><path fill="currentColor" d="M21.9 4.3 18.6 20c-.2 1.1-.9 1.4-1.8.9l-5-3.7-2.4 2.3c-.3.3-.5.5-1 .5l.4-5.1 9.2-8.3c.4-.4-.1-.6-.6-.2L6 13.5 1.1 12c-1.1-.3-1.1-1.1.2-1.6L20.4 3c.9-.3 1.7.2 1.5 1.3z" /></svg>;
}

export function InstagramIcon(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <rect x="3" y="3" width="18" height="18" rx="5" {...stroke} />
      <circle cx="12" cy="12" r="4" {...stroke} />
      <circle cx="17.5" cy="6.5" r="1.2" fill="currentColor" />
    </svg>
  );
}

export function YoutubeIcon(props: IconProps) {
  return <svg {...base} {...props}><path fill="currentColor" d="M23 7.2a3 3 0 0 0-2.1-2.1C19 4.6 12 4.6 12 4.6s-7 0-8.9.5A3 3 0 0 0 1 7.2 31 31 0 0 0 .5 12 31 31 0 0 0 1 16.8a3 3 0 0 0 2.1 2.1c1.9.5 8.9.5 8.9.5s7 0 8.9-.5a3 3 0 0 0 2.1-2.1 31 31 0 0 0 .5-4.8 31 31 0 0 0-.5-4.8zM9.7 15V9l5.8 3-5.8 3z" /></svg>;
}

export function FacebookIcon(props: IconProps) {
  return <svg {...base} {...props}><path fill="currentColor" d="M14 8V6.2c0-.8.2-1.2 1.4-1.2H17V2h-2.6C11.3 2 10 3.6 10 6.2V8H8v3h2v11h4V11h2.7l.3-3h-3z" /></svg>;
}

export function ShareIcon(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <circle cx="18" cy="5" r="3" {...stroke} /><circle cx="6" cy="12" r="3" {...stroke} /><circle cx="18" cy="19" r="3" {...stroke} />
      <path d="m8.6 13.5 6.8 4M15.4 6.5l-6.8 4" {...stroke} />
    </svg>
  );
}

export function PhoneIcon(props: IconProps) {
  return <svg {...base} {...props}><path {...stroke} d="M22 16.9v3a2 2 0 0 1-2.2 2 19.8 19.8 0 0 1-8.6-3.1 19.5 19.5 0 0 1-6-6A19.8 19.8 0 0 1 2.1 4.2 2 2 0 0 1 4.1 2h3a2 2 0 0 1 2 1.7c.1 1 .4 1.9.7 2.8a2 2 0 0 1-.5 2.1L8 9.9a16 16 0 0 0 6 6l1.3-1.3a2 2 0 0 1 2.1-.4c.9.3 1.8.6 2.8.7a2 2 0 0 1 1.7 2z" /></svg>;
}

export function MailIcon(props: IconProps) {
  return <svg {...base} {...props}><rect x="2" y="4" width="20" height="16" rx="2" {...stroke} /><path d="m22 6-10 7L2 6" {...stroke} /></svg>;
}

export function ClockIcon(props: IconProps) {
  return <svg {...base} {...props}><circle cx="12" cy="12" r="10" {...stroke} /><path d="M12 7v5l3 2" {...stroke} /></svg>;
}

export const SOCIAL_ICONS = { telegram: TelegramIcon, instagram: InstagramIcon, youtube: YoutubeIcon } as const;
