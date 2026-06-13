import type { ChatMode } from '../types';

const modes: { key: ChatMode; label: string }[] = [
  { key: 'auto', label: 'Ask AI' },
  { key: 'nl_query', label: 'NL Query' },
  { key: 'rag', label: 'Search Documents' },
];

interface ModeSelectorProps {
  active: ChatMode;
  onChange: (mode: ChatMode) => void;
}

export default function ModeSelector({ active, onChange }: ModeSelectorProps) {
  return (
    <div className="flex items-center gap-1 px-1 py-1 bg-canvas-soft rounded-lg" role="radiogroup" aria-label="Chat mode">
      {modes.map((m) => (
        <button
          key={m.key}
          type="button"
          role="radio"
          aria-checked={active === m.key}
          onClick={() => onChange(m.key)}
          className={`px-3 py-1.5 rounded-md text-caption font-medium transition-all ${
            active === m.key
              ? 'bg-brand-600 text-white shadow-sm'
              : 'text-ink-muted hover:text-ink hover:bg-canvas'
          }`}
        >
          {m.label}
        </button>
      ))}
    </div>
  );
}
