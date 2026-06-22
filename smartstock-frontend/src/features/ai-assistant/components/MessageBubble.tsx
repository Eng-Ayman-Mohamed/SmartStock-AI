import type { ReactNode } from 'react';
import { Bot, User } from 'lucide-react';
import type { Message } from '../types';
import CitationTag from '../../../shared/atoms/CitationTag';

function parseAnswerText(text: string, sources: Message['sources']) {
  if (!sources || sources.length === 0) return text;

  const parts: (string | ReactNode)[] = [];
  const remaining = text;

  const pattern = /\[Source:\s*([^,]+),\s*Page:\s*(\d+)\]/g;
  let match;
  let lastIndex = 0;

  while ((match = pattern.exec(remaining)) !== null) {
    if (match.index > lastIndex) {
      parts.push(remaining.slice(lastIndex, match.index));
    }

    const doc = match[1].trim();
    const page = parseInt(match[2], 10);
    const source = sources.find((s) => s.document === doc && s.page === page);

    parts.push(
      <CitationTag
        key={`${doc}-${page}-${match.index}`}
        sourceDocument={doc}
        page={page}
        chunkText={source?.chunk_text}
      />,
    );

    lastIndex = match.index + match[0].length;
  }

  if (lastIndex < remaining.length) {
    parts.push(remaining.slice(lastIndex));
  }

  return parts.length > 0 ? parts : text;
}

interface MessageBubbleProps {
  message: Message;
}

export default function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === 'user';

  return (
    <div className={`flex gap-2.5 animate-fadeIn ${isUser ? 'flex-row-reverse' : ''}`}>
      <div
        className={`flex items-center justify-center w-7 h-7 rounded-full shrink-0 ${
          isUser
            ? 'bg-brand-600'
            : 'bg-purple-50 dark:bg-purple-900/30'
        }`}
      >
        {isUser ? (
          <User className="w-3.5 h-3.5 text-white" />
        ) : (
          <Bot className="w-3.5 h-3.5 text-purple-600 dark:text-purple-400" />
        )}
      </div>

      <div className={`max-w-[75%] min-w-0 ${isUser ? 'text-right' : ''}`}>
        <div
          className={`inline-block text-left ${
            isUser
              ? 'bg-brand-600 text-white rounded-2xl rounded-br-md px-4 py-2.5'
              : 'bg-canvas-soft text-ink rounded-2xl rounded-bl-md px-4 py-2.5 border border-hairline/50'
          }`}
        >
          <p className="text-body leading-relaxed whitespace-pre-wrap break-words">
            {isUser ? message.text : parseAnswerText(message.text, message.sources)}
          </p>
        </div>
      </div>
    </div>
  );
}
