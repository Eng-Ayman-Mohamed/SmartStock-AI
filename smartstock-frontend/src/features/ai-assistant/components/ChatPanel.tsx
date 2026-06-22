import { useState, useRef, useEffect, useCallback } from 'react';
import { Send, PanelLeftOpen, PanelLeftClose, X, RefreshCw } from 'lucide-react';
import useChat from '../hooks/useChat';
import useConversations from '../hooks/useConversations';
import ModeSelector from './ModeSelector';
import MessageBubble from './MessageBubble';
import TypingIndicator from './TypingIndicator';
import ChatEmptyState from './ChatEmptyState';
import VoiceButton from './VoiceButton';
import ConversationSidebar from './ConversationSidebar';

export default function ChatPanel() {
  const {
    conversations,
    activeConversation,
    isLoading: convLoading,
    error: convError,
    selectConversation,
    startNewConversation,
    removeConversation,
    clearActive,
  } = useConversations();

  const [visibleError, setVisibleError] = useState<string | null>(null);

  useEffect(() => {
    if (convError) {
      setVisibleError(convError); // eslint-disable-line react-hooks/set-state-in-effect
      const timer = setTimeout(() => setVisibleError(null), 4000);
      return () => clearTimeout(timer);
    }
  }, [convError]);

  const {
    messages,
    sendMessage,
    retryLastMessage,
    isLoading,
    error: chatError,
    mode,
    setMode,
    loadFromConversation,
    clearMessages,
  } = useChat(activeConversation?.id);

  const [input, setInput] = useState('');
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  useEffect(() => {
    if (activeConversation) {
      loadFromConversation(activeConversation);
    }
  }, [activeConversation, loadFromConversation]);

  const handleSend = useCallback(
    async (text?: string) => {
      const query = (text ?? input).trim();
      if (!query || isLoading) return;

      if (!activeConversation?.id) {
        const newConv = await startNewConversation();
        if (!newConv) return;
        setInput('');
        await sendMessage(query, newConv.id);
        await selectConversation(newConv.id);
        return;
      }

      setInput('');
      await sendMessage(query);
    },
    [input, isLoading, activeConversation, startNewConversation, sendMessage, selectConversation],
  );

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleInput = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value);
    const ta = e.target;
    ta.style.height = 'auto';
    ta.style.height = `${Math.min(ta.scrollHeight, 160)}px`;
  };

  const handleSelectSuggestion = (text: string) => {
    setInput(text);
    inputRef.current?.focus();
  };

  const handleNewChat = async () => {
    clearMessages();
    clearActive();
  };

  const handleSelectConversation = async (id: string) => {
    await selectConversation(id);
  };

  return (
    <div className="flex h-full">
      {sidebarOpen && (
        <div className="w-64 shrink-0 h-full">
          <ConversationSidebar
            conversations={conversations}
            activeId={activeConversation?.id ?? null}
            onSelect={handleSelectConversation}
            onNew={handleNewChat}
            onDelete={removeConversation}
            isLoading={convLoading}
          />
        </div>
      )}

      <div className="flex flex-col flex-1 h-full min-w-0">
        <div className="flex items-center gap-2 px-4 py-2 border-b border-hairline">
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="p-1.5 rounded text-ink-faint hover:text-ink hover:bg-canvas-soft transition-colors"
            aria-label={sidebarOpen ? 'Close sidebar' : 'Open sidebar'}
          >
            {sidebarOpen ? (
              <PanelLeftClose className="w-4 h-4" />
            ) : (
              <PanelLeftOpen className="w-4 h-4" />
            )}
          </button>
          {activeConversation && (
            <h2 className="text-sm font-medium text-ink truncate">
              {activeConversation.title}
            </h2>
          )}
        </div>

        {visibleError && (
          <div className="flex items-center gap-2 px-4 py-2 bg-red-50 border-b border-red-200 text-sm text-red-700">
            <span className="flex-1">{visibleError}</span>
            <button onClick={() => setVisibleError(null)} className="p-0.5 rounded hover:bg-red-100">
              <X className="w-4 h-4" />
            </button>
          </div>
        )}

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
          {!isLoading && chatError && (
            <div className="flex justify-center">
              <button
                onClick={retryLastMessage}
                className="flex items-center gap-1.5 text-sm text-ink-muted hover:text-brand-600 transition-colors"
              >
                <RefreshCw className="w-4 h-4" />
                Retry
              </button>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        <div className="px-6 py-3 border-t border-hairline">
          <div className="mb-2">
            <ModeSelector active={mode} onChange={setMode} />
          </div>
          <div className="flex items-end gap-2">
            <VoiceButton
              onTranscript={(text) => {
                setInput(text);
                setTimeout(() => {
                  if (inputRef.current) {
                    inputRef.current.focus();
                    inputRef.current.style.height = 'auto';
                    inputRef.current.style.height = `${Math.min(inputRef.current.scrollHeight, 160)}px`;
                  }
                }, 50);
              }}
            />
            <textarea
              ref={inputRef}
              value={input}
              onChange={handleInput}
              onKeyDown={handleKeyDown}
              rows={1}
              placeholder="Ask about your inventory..."
              className="flex-1 resize-none px-4 py-2 rounded-2xl border border-hairline bg-canvas text-body text-ink placeholder:text-ink-faint hover:border-ink-muted focus:border-brand-600 focus:outline-none focus:ring-0 transition-colors max-h-40"
              aria-label="Ask about your inventory"
              disabled={isLoading}
            />
            <button
              onClick={() => handleSend()}
              disabled={isLoading || !input.trim()}
              className="flex items-center justify-center w-9 h-9 rounded-full bg-brand-600 text-white hover:bg-brand-800 disabled:bg-canvas-soft disabled:text-ink-faint transition-colors shrink-0 mb-0.5"
              aria-label="Send message"
            >
              <Send className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
