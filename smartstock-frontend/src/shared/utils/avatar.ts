const AVATAR_COLORS = [
  'bg-brand-600',
  'bg-green-600',
  'bg-purple-600',
  'bg-amber-600',
  'bg-red-600',
  'bg-blue-600',
];

function hashName(name: string): number {
  let hash = 0;
  for (let i = 0; i < name.length; i++) {
    hash = name.charCodeAt(i) + ((hash << 5) - hash);
  }
  return Math.abs(hash);
}

export function getAvatarColor(name: string): string {
  return AVATAR_COLORS[hashName(name) % AVATAR_COLORS.length];
}
