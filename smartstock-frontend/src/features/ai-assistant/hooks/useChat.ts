import { useState, useCallback } from 'react';
import type { ChatMode, ConversationDetail, Message } from '../types';
import { sendChatMessage, sendNLQuery } from '../api';

let nextId = 0;
function createId(): string {
  return `msg-${Date.now()}-${nextId++}`;
}

function mapConversationMessages(detail: ConversationDetail): Message[] {
  return detail.messages.map((m) => ({
    id: m.id,
    role: m.role === 'assistant' ? 'ai' : m.role,
    text: m.content,
    mode: m.mode as ChatMode,
    engine: m.engine as Message['engine'],
    sources: m.sources,
    timestamp: new Date(m.created_at).getTime(),
  }));
}

export default function useChat(conversationId?: string | null) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [mode, setMode] = useState<ChatMode>('auto');

  const loadFromConversation = useCallback((detail: ConversationDetail) => {
    setMessages(mapConversationMessages(detail));
  }, []);

  const sendMessage = useCallback(
    async (text: string) => {
      const trimmed = text.trim();
      if (!trimmed || isLoading) return;

      const userMessage: Message = {
        id: createId(),
        role: 'user',
        text: trimmed,
        mode,
        timestamp: Date.now(),
      };

      setMessages((prev) => [...prev, userMessage]);
      setIsLoading(true);
      setError(null);

      try {
        let aiText: string;
        let engine: Message['engine'] = 'nl_query';
        let sources: Message['sources'];

        if (mode === 'nl_query' && !conversationId) {
          const nlResult = await sendNLQuery(trimmed);
          aiText = nlResult.answer;
          if (nlResult.action) {
            const actionInfo = `\n\n[Action: ${nlResult.action.type}]`;
            aiText = aiText + actionInfo;
          }
        } else {
          const response = await sendChatMessage({
            query: trimmed,
            mode,
            conversation_id: conversationId ?? undefined,
          });
          aiText = response.answer;
          engine = response.engine;
          sources = response.sources;
        }

        const aiMessage: Message = {
          id: createId(),
          role: 'ai',
          text: aiText,
          engine,
          sources,
          timestamp: Date.now(),
        };
        setMessages((prev) => [...prev, aiMessage]);
      } catch (err) {
        const raw = err instanceof Error ? err.message : 'An error occurred';
        const isQuota = /quota|rate.?limit|429|too many requests/i.test(raw);
        const userMessage = isQuota
          ? 'AI service quota has been reached. Please try again shortly.'
          : 'Sorry, something went wrong. Please try again.';
        const errorMessage: Message = {
          id: createId(),
          role: 'ai',
          text: userMessage,
          timestamp: Date.now(),
        };
        setMessages((prev) => [...prev, errorMessage]);
        setError(userMessage);
      } finally {
        setIsLoading(false);
      }
    },
    [mode, isLoading, conversationId],
  );

  const clearMessages = useCallback(() => {
    setMessages([]);
    setError(null);
  }, []);

  return {
    messages,
    sendMessage,
    isLoading,
    error,
    mode,
    setMode,
    loadFromConversation,
    clearMessages,
  };
}
