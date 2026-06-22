import { Bot } from 'lucide-react';

const suggestions = [
  'What products are low on stock?',
  'Show me supplier performance this month',
  'Which items need reordering?',
];

interface ChatEmptyStateProps {
  onSelectSuggestion: (text: string) => void;
}

export default function ChatEmptyState({ onSelectSuggestion }: ChatEmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center h-full text-center px-6">
      <div className="flex items-center justify-center w-16 h-16 rounded-full bg-purple-50 dark:bg-purple-900/30 mb-5">
        <Bot className="w-8 h-8 text-purple-600 dark:text-purple-400" />
      </div>
      <h3 className="text-section-heading text-ink mb-2">Ask anything about your inventory</h3>
      <p className="text-body text-ink-muted mb-8 max-w-sm leading-relaxed">
        Query stock levels, supplier data, or get AI-powered insights from your documents.
      </p>
      <div className="flex flex-wrap justify-center gap-2">
        {suggestions.map((s) => (
          <button
            key={s}
            type="button"
            onClick={() => onSelectSuggestion(s)}
            className="px-4 py-2 rounded-xl border border-hairline bg-canvas text-caption text-ink-muted hover:border-brand-600 hover:text-brand-600 hover:bg-brand-50 dark:hover:bg-brand-900/20 transition-all"
          >
            {s}
          </button>
        ))}
      </div>
    </div>
  );
}
