import { create } from 'zustand';

export type ThemeMode = 'light' | 'dark' | 'system';

interface ThemeState {
  mode: ThemeMode;
  resolved: 'light' | 'dark';
  setMode: (mode: ThemeMode) => void;
  toggle: () => void;
}

function getSystemPreference(): 'light' | 'dark' {
  if (typeof window === 'undefined') return 'light';
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
}

function resolveMode(mode: ThemeMode): 'light' | 'dark' {
  if (mode === 'system') return getSystemPreference();
  return mode;
}

function applyTheme(mode: ThemeMode) {
  const resolved = resolveMode(mode);
  if (resolved === 'dark') {
    document.documentElement.classList.add('dark');
  } else {
    document.documentElement.classList.remove('dark');
  }
  return resolved;
}

function getInitialMode(): ThemeMode {
  if (typeof window === 'undefined') return 'system';
  const stored = localStorage.getItem('theme-mode') as ThemeMode | null;
  if (stored && ['light', 'dark', 'system'].includes(stored)) return stored;
  return 'system';
}

let mediaQuery: MediaQueryList | null = null;
let mediaHandler: (() => void) | null = null;

function subscribeToOSChanges(mode: ThemeMode, setResolved: (r: 'light' | 'dark') => void) {
  if (mediaHandler) {
    mediaQuery?.removeEventListener('change', mediaHandler);
    mediaHandler = null;
  }
  if (mode !== 'system') return;
  mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
  mediaHandler = () => {
    const next = getSystemPreference();
    applyTheme('system');
    setResolved(next);
  };
  mediaQuery.addEventListener('change', mediaHandler);
}

export const useThemeStore = create<ThemeState>((set) => {
  const mode = getInitialMode();
  const resolved = applyTheme(mode);

  setTimeout(() => {
    subscribeToOSChanges(mode, (r) => set({ resolved: r }));
  }, 0);

  return {
    mode,
    resolved,
    setMode: (next) => {
      localStorage.setItem('theme-mode', next);
      const resolvedVal = applyTheme(next);
      subscribeToOSChanges(next, (r) => set({ resolved: r }));
      set({ mode: next, resolved: resolvedVal });
    },
    toggle: () => {
      const sequence: ThemeMode[] = ['light', 'dark', 'system'];
      const current = useThemeStore.getState().mode;
      const idx = sequence.indexOf(current);
      const next = sequence[(idx + 1) % sequence.length];
      useThemeStore.getState().setMode(next);
    },
  };
});
