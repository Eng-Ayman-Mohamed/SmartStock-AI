import { useState, useCallback, useRef, useEffect } from 'react';
import type { ChatMode, ConversationDetail, Message } from '../types';
import { sendChatMessageStream } from '../api';

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
  const idCounter = useRef(0);

  function createId(): string {
    return `msg-${Date.now()}-${idCounter.current++}`;
  }

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

      const aiMessageId = createId();
      const aiMessage: Message = {
        id: aiMessageId,
        role: 'ai',
        text: '',
        mode,
        timestamp: Date.now(),
      };

      setMessages((prev) => [...prev, userMessage, aiMessage]);
      setIsLoading(true);
      setError(null);
      lastFailedText.current = null;

      const activeConvId = conversationIdOverride ?? conversationId;

      try {
        const stream = sendChatMessageStream(
          {
            query: trimmed,
            mode,
            conversation_id: activeConvId ?? undefined,
          },
          AbortSignal.any([controller.signal, AbortSignal.timeout(25000)]),
        );

        let fullText = '';
        let engine: Message['engine'] = undefined;
        let sources: Message['sources'] = undefined;

        for await (const event of stream) {
          if (controller.signal.aborted) return;

          if (event.type === 'metadata') {
            engine = event.engine as Message['engine'];
          } else if (event.type === 'token' && event.content) {
            fullText += event.content;
            const textCopy = fullText;
            setMessages((prev) =>
              prev.map((m) => (m.id === aiMessageId ? { ...m, text: textCopy } : m)),
            );
          } else if (event.type === 'done') {
            sources = event.sources;
          } else if (event.type === 'error') {
            throw new Error(event.message || 'Stream error');
          }
        }

        // Finalize message with sources and engine
        const finalText = fullText || 'No response received.';
        setMessages((prev) =>
          prev.map((m) =>
            m.id === aiMessageId ? { ...m, text: finalText, engine, sources } : m,
          ),
        );
      } catch (err) {
        if (controller.signal.aborted) return;

        const raw = err instanceof Error ? err.message : 'An error occurred';
        const isQuota = /quota|rate.?limit|429|too many requests/i.test(raw);
        const isTimeout = /timeout|AbortError/i.test(raw);
        const userMessage = isQuota
          ? 'AI service quota has been reached. Please try again shortly.'
          : isTimeout
            ? 'Request timed out. Please try a simpler question.'
            : 'Sorry, something went wrong. Please try again.';
        // Remove the empty AI message and add error message
        setMessages((prev) => {
          const filtered = prev.filter((m) => m.id !== aiMessageId);
          return [
            ...filtered,
            {
              id: createId(),
              role: 'ai' as const,
              text: userMessage,
              timestamp: Date.now(),
            },
          ];
        });
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

    const aiMessageId = createId();
    const aiMessage: Message = {
      id: aiMessageId,
      role: 'ai',
      text: '',
      mode,
      timestamp: Date.now(),
    };

    setMessages((prev) => [...prev, userMessage, aiMessage]);
    setIsLoading(true);
    setError(null);

    try {
      const stream = sendChatMessageStream(
        {
          query: failedText,
          mode,
          conversation_id: conversationId ?? undefined,
        },
        AbortSignal.any([controller.signal, AbortSignal.timeout(25000)]),
      );

      let fullText = '';
      let engine: Message['engine'] = undefined;
      let sources: Message['sources'] = undefined;

      for await (const event of stream) {
        if (controller.signal.aborted) return;

        if (event.type === 'metadata') {
          engine = event.engine as Message['engine'];
        } else if (event.type === 'token' && event.content) {
          fullText += event.content;
          const textCopy = fullText;
          setMessages((prev) =>
            prev.map((m) => (m.id === aiMessageId ? { ...m, text: textCopy } : m)),
          );
        } else if (event.type === 'done') {
          sources = event.sources;
        } else if (event.type === 'error') {
          throw new Error(event.message || 'Stream error');
        }
      }

      const finalText = fullText || 'No response received.';
      setMessages((prev) =>
        prev.map((m) =>
          m.id === aiMessageId ? { ...m, text: finalText, engine, sources } : m,
        ),
      );
    } catch (err) {
      if (controller.signal.aborted) return;

      const raw = err instanceof Error ? err.message : 'An error occurred';
      const isQuota = /quota|rate.?limit|429|too many requests/i.test(raw);
      const isTimeout = /timeout|AbortError/i.test(raw);
      const msg = isQuota
        ? 'AI service quota has been reached. Please try again shortly.'
        : isTimeout
          ? 'Request timed out. Please try a simpler question.'
          : 'Sorry, something went wrong. Please try again.';
      setMessages((prev) => {
        const filtered = prev.filter((m) => m.id !== aiMessageId);
        return [
          ...filtered,
          {
            id: createId(),
            role: 'ai' as const,
            text: msg,
            timestamp: Date.now(),
          },
        ];
      });
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
    setMode('auto');
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
