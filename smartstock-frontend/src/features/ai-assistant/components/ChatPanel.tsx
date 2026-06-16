import { useState, useRef, useEffect } from 'react';
import { Send } from 'lucide-react';
import useChat from '../hooks/useChat';
import ModeSelector from './ModeSelector';
import MessageBubble from './MessageBubble';
import TypingIndicator from './TypingIndicator';
import ChatEmptyState from './ChatEmptyState';
import VoiceButton from './VoiceButton';

export default function ChatPanel() {
  const { messages, sendMessage, isLoading, mode, setMode } = useChat();
  const [input, setInput] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  const handleSend = (text?: string) => {
    const query = (text ?? input).trim();
    if (!query || isLoading) return;
    sendMessage(query);
    setInput('');
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleSelectSuggestion = (text: string) => {
    setInput(text);
    inputRef.current?.focus();
  };

  return (
    <div className="flex flex-col h-full">
      <div
        className="flex-1 overflow-y-auto px-6 py-4 space-y-4"
        role="log"
        aria-label="Chat messages"
        aria-live="polite"
      >
        {messages.length === 0 && !isLoading ? (
          <ChatEmptyState onSelectSuggestion={handleSelectSuggestion} />
        ) : (
          messages.map((msg) => <MessageBubble key={msg.id} message={msg} />)
        )}
        {isLoading && <TypingIndicator />}
        <div ref={messagesEndRef} />
      </div>

      <div className="px-6 py-3 border-t border-hairline">
        <div className="mb-2">
          <ModeSelector active={mode} onChange={setMode} />
        </div>
        <div className="flex items-center gap-2">
          <VoiceButton onTranscript={(text) => handleSend(text)} />
          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask about your inventory..."
            className="flex-1 h-9 px-4 rounded-full border border-hairline bg-canvas text-body text-ink placeholder:text-ink-faint hover:border-ink-muted focus:border-brand-600 focus:outline-none focus:ring-0 transition-colors"
            aria-label="Ask about your inventory"
            disabled={isLoading}
          />
          <button
            onClick={() => handleSend()}
            disabled={isLoading || !input.trim()}
            className="flex items-center justify-center w-9 h-9 rounded-full bg-brand-600 text-white hover:bg-brand-800 disabled:bg-canvas-soft disabled:text-ink-faint transition-colors shrink-0"
            aria-label="Send message"
          >
            <Send className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
}
