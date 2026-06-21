import { useState, useCallback, useRef, useEffect } from 'react';
import type { ChatMode, ConversationDetail, Message } from '../types';
import { sendChatMessage } from '../api';

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
  const abortRef = useRef<AbortController | null>(null);
  const lastFailedText = useRef<string | null>(null);

  useEffect(() => {
    return () => abortRef.current?.abort();
  }, []);

  const loadFromConversation = useCallback((detail: ConversationDetail) => {
    setMessages(mapConversationMessages(detail));
    abortRef.current?.abort();
    abortRef.current = null;
    lastFailedText.current = null;
  }, []);

  const sendMessage = useCallback(
    async (text: string, conversationIdOverride?: string) => {
      const trimmed = text.trim();
      if (!trimmed || isLoading) return;

      abortRef.current?.abort();
      const controller = new AbortController();
      abortRef.current = controller;

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
      lastFailedText.current = null;

      const activeConvId = conversationIdOverride ?? conversationId;

      try {
        const response = await sendChatMessage(
          {
            query: trimmed,
            mode,
            conversation_id: activeConvId ?? undefined,
          },
          controller.signal,
        );
        if (controller.signal.aborted) return;

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
        if (controller.signal.aborted) return;

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
        lastFailedText.current = trimmed;
      } finally {
        if (!controller.signal.aborted) {
          setIsLoading(false);
        }
        if (abortRef.current === controller) {
          abortRef.current = null;
        }
      }
    },
    [mode, isLoading, conversationId],
  );

  const retryLastMessage = useCallback(async () => {
    const failedText = lastFailedText.current;
    if (!failedText || isLoading) return;

    setMessages((prev) => prev.slice(0, -1));
    lastFailedText.current = null;

    const userMessage: Message = {
      id: createId(),
      role: 'user',
      text: failedText,
      mode,
      timestamp: Date.now(),
    };

    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;

    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);
    setError(null);

    try {
      const response = await sendChatMessage(
        {
          query: failedText,
          mode,
          conversation_id: conversationId ?? undefined,
        },
        controller.signal,
      );
      if (controller.signal.aborted) return;

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
      if (controller.signal.aborted) return;

      const raw = err instanceof Error ? err.message : 'An error occurred';
      const isQuota = /quota|rate.?limit|429|too many requests/i.test(raw);
      const msg = isQuota
        ? 'AI service quota has been reached. Please try again shortly.'
        : 'Sorry, something went wrong. Please try again.';
      const errorMessage: Message = {
        id: createId(),
        role: 'ai',
        text: msg,
        timestamp: Date.now(),
      };
      setMessages((prev) => [...prev, errorMessage]);
      setError(msg);
      lastFailedText.current = failedText;
    } finally {
      if (!controller.signal.aborted) {
        setIsLoading(false);
      }
      if (abortRef.current === controller) {
        abortRef.current = null;
      }
    }
  }, [mode, isLoading, conversationId]);

  const clearMessages = useCallback(() => {
    setMessages([]);
    setError(null);
    lastFailedText.current = null;
  }, []);

  return {
    messages,
    sendMessage,
    retryLastMessage,
    isLoading,
    error,
    mode,
    setMode,
    loadFromConversation,
    clearMessages,
  };
}
