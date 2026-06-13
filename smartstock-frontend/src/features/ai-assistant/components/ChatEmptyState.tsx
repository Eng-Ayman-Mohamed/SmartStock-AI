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
      <div className="flex items-center justify-center w-14 h-14 rounded-full bg-purple-50 mb-4">
        <Bot className="w-7 h-7 text-purple-600" />
      </div>
      <h3 className="text-section-heading text-ink mb-1">Ask anything about your inventory</h3>
      <p className="text-body text-ink-muted mb-6 max-w-sm">
        Query stock levels, supplier data, or get AI-powered insights from your documents.
      </p>
      <div className="flex flex-wrap justify-center gap-2">
        {suggestions.map((s) => (
          <button
            key={s}
            type="button"
            onClick={() => onSelectSuggestion(s)}
            className="px-3 py-1.5 rounded-full border border-hairline bg-canvas text-caption text-ink-muted hover:border-brand-600 hover:text-brand-600 transition-colors"
          >
            {s}
          </button>
        ))}
      </div>
    </div>
  );
}
