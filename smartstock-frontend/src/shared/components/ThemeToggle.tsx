import { Sun, Moon, Monitor } from 'lucide-react';
import { useThemeStore, type ThemeMode } from '../../store/themeStore';

const icons: Record<ThemeMode, typeof Sun> = {
  light: Sun,
  dark: Moon,
  system: Monitor,
};

const labels: Record<ThemeMode, string> = {
  light: 'Switch to dark mode',
  dark: 'Switch to system mode',
  system: 'Switch to light mode',
};

export default function ThemeToggle() {
  const mode = useThemeStore((s) => s.mode);
  const toggle = useThemeStore((s) => s.toggle);
  const Icon = icons[mode];

  return (
    <button
      type="button"
      onClick={toggle}
      aria-label={labels[mode]}
      className="flex items-center justify-center w-7 h-7 rounded-md text-ink-muted hover:text-ink-secondary hover:bg-canvas-soft transition-colors"
    >
      <Icon className="w-4 h-4" aria-hidden="true" />
    </button>
  );
}
