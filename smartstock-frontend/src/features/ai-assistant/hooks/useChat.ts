import { useState, useCallback } from 'react';
import type { ChatMode, Message } from '../types';
import { sendChat } from '../api';

let nextId = 0;
function createId(): string {
  return `msg-${Date.now()}-${nextId++}`;
}

export default function useChat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [mode, setMode] = useState<ChatMode>('auto');

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
        const response = await sendChat(trimmed, mode);
        const aiMessage: Message = {
          id: createId(),
          role: 'ai',
          text: response.answer,
          engine: response.engine,
          sources: response.sources,
          timestamp: Date.now(),
        };
        setMessages((prev) => [...prev, aiMessage]);
      } catch (err) {
        const errorMessage: Message = {
          id: createId(),
          role: 'ai',
          text: 'Sorry, something went wrong. Please try again.',
          timestamp: Date.now(),
        };
        setMessages((prev) => [...prev, errorMessage]);
        setError(err instanceof Error ? err.message : 'An error occurred');
      } finally {
        setIsLoading(false);
      }
    },
    [mode, isLoading],
  );

  return { messages, sendMessage, isLoading, error, mode, setMode };
}
