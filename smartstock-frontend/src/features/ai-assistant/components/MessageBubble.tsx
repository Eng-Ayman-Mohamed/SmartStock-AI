import type { ReactNode } from 'react';
import { Bot, User } from 'lucide-react';
import type { Message } from '../types';
import CitationTag from '../../../shared/atoms/CitationTag';

const engineLabels: Record<string, string> = {
  nl_query: 'NL Query',
  rag: 'RAG',
  auto: 'Auto',
};

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
    <div className={`flex gap-3 ${isUser ? 'flex-row-reverse' : ''}`}>
      <div
        className={`flex items-center justify-center w-7 h-7 rounded-full shrink-0 ${
          isUser ? 'bg-brand-600' : 'bg-purple-50'
        }`}
      >
        {isUser ? (
          <User className="w-4 h-4 text-white" />
        ) : (
          <Bot className="w-4 h-4 text-purple-600" />
        )}
      </div>

      <div className={`max-w-[80%] ${isUser ? 'text-right' : ''}`}>
        <div
          className={`inline-block text-left ${
            isUser
              ? 'bg-brand-600 text-white rounded-lg rounded-br-sm px-4 py-2.5'
              : 'bg-canvas-soft text-ink rounded-lg rounded-bl-sm px-4 py-2.5'
          }`}
        >
          <p className="text-body leading-relaxed whitespace-pre-wrap">
            {isUser ? message.text : parseAnswerText(message.text, message.sources)}
          </p>
        </div>

        {!isUser && message.engine && (
          <span className="inline-block mt-1 ml-1 px-1.5 py-0.5 rounded text-[10px] font-medium bg-canvas-soft text-ink-faint">
            {engineLabels[message.engine] || message.engine}
          </span>
        )}
      </div>
    </div>
  );
}
