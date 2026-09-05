// Small set of hand-drawn outline icons (no icon library, no emoji).

const base = {
  fill: "none",
  stroke: "currentColor",
  strokeWidth: 1.6,
  strokeLinecap: "round",
  strokeLinejoin: "round",
  viewBox: "0 0 24 24",
};

export function QueueIcon(props) {
  return (
    <svg {...base} {...props}>
      <rect x="3.5" y="3.5" width="7.5" height="7.5" rx="1.2" />
      <rect x="13" y="3.5" width="7.5" height="4.5" rx="1.2" />
      <rect x="13" y="10.5" width="7.5" height="10" rx="1.2" />
      <rect x="3.5" y="13.5" width="7.5" height="7" rx="1.2" />
    </svg>
  );
}

export function ApproverIcon(props) {
  return (
    <svg {...base} {...props}>
      <path d="M12 3.5 5 6v6c0 4.5 3 7.5 7 8.5 4-1 7-4 7-8.5V6z" />
      <path d="M9 12l2 2 4-4.5" />
    </svg>
  );
}

export function AuditIcon(props) {
  return (
    <svg {...base} {...props}>
      <circle cx="11" cy="11" r="7" />
      <path d="M16.2 16.2 21 21" />
      <path d="M8.5 11h5M11 8.5v5" />
    </svg>
  );
}

export function ProfileIcon(props) {
  return (
    <svg {...base} {...props}>
      <circle cx="12" cy="7.5" r="3.5" />
      <path d="M4.5 20c0-3.6 3.4-6 7.5-6s7.5 2.4 7.5 6" />
    </svg>
  );
}
