import type { ChatMode } from '../types';

const modes: { key: ChatMode; label: string }[] = [
  { key: 'nl_query', label: 'Search Stock' },
  { key: 'rag', label: 'Search Documents' },
];

interface ModeSelectorProps {
  active: ChatMode;
  onChange: (mode: ChatMode) => void;
}

export default function ModeSelector({ active, onChange }: ModeSelectorProps) {
  return (
    <div className="flex flex-wrap items-center gap-1 px-1 py-1 bg-canvas-soft rounded-lg" role="radiogroup" aria-label="Chat mode">
      {modes.map((m) => (
        <button
          key={m.key}
          type="button"
          role="radio"
          aria-checked={active === m.key}
          onClick={() => onChange(m.key)}
          className={`px-2.5 py-1.5 min-h-[36px] rounded-md text-caption font-medium transition-all ${
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
