import { Bot } from 'lucide-react';

export default function TypingIndicator() {
  return (
    <div className="flex gap-2.5">
      <div className="flex items-center justify-center w-7 h-7 rounded-full bg-purple-50 dark:bg-purple-900/30 shrink-0">
        <Bot className="w-3.5 h-3.5 text-purple-600 dark:text-purple-400" />
      </div>
      <div className="bg-canvas-soft rounded-2xl rounded-bl-md px-4 py-3 border border-hairline/50">
        <span className="flex gap-1.5 items-center">
          <span className="w-1.5 h-1.5 bg-ink-faint rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
          <span className="w-1.5 h-1.5 bg-ink-faint rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
          <span className="w-1.5 h-1.5 bg-ink-faint rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
        </span>
      </div>
    </div>
  );
}
