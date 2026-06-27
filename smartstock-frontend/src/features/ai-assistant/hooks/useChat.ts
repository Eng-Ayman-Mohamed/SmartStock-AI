import { useState, useCallback, useRef, useEffect } from 'react';
import type { ChatMode, ConversationDetail, Message } from '../types';
import { sendChatMessageStream, sendNLQuery } from '../api';

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

/**
 * Shared streaming helper consumed by sendMessage and retryLastMessage.
 * Processes an SSE stream, updates the AI message token-by-token,
 * and finalises with engine metadata + sources.
 */
async function executeStreamQuery(
  text: string,
  convId: string | undefined,
  chatMode: ChatMode,
  controller: AbortController,
  setMessages: React.Dispatch<React.SetStateAction<Message[]>>,
  aiMessageId: string,
): Promise<void> {
  const stream = sendChatMessageStream(
    { query: text, mode: chatMode, conversation_id: convId },
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
}

export default function useChat(conversationId?: string | null) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [mode, setMode] = useState<ChatMode>('rag');
  const abortRef = useRef<AbortController | null>(null);
  const lastFailedText = useRef<string | null>(null);
  const idCounter = useRef(0);
  const isLoadingRef = useRef(false);
  const sendingRef = useRef(false);

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
    isLoadingRef.current = false;
    sendingRef.current = false;
    setIsLoading(false);
  }, []);

  const sendMessage = useCallback(
    async (text: string, conversationIdOverride?: string) => {
      const trimmed = text.trim();
      if (!trimmed || isLoading || sendingRef.current) return;
      sendingRef.current = true;

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
      isLoadingRef.current = true;
      setIsLoading(true);
      setError(null);
      lastFailedText.current = null;

      const activeConvId = conversationIdOverride ?? conversationId;

      try {
        if (mode === 'nl_query' && !conversationId) {
          const nlResult = await sendNLQuery(trimmed);
          let aiText = nlResult.answer;
          if (nlResult.action) {
            const actionInfo = `\n\n[Action: ${nlResult.action.type}]`;
            aiText = aiText + actionInfo;
          }

          setMessages((prev) =>
            prev.map((m) =>
              m.id === aiMessageId ? { ...m, text: aiText, engine: 'nl_query' } : m,
            ),
          );
        } else {
          await executeStreamQuery(
            trimmed,
            activeConvId ?? undefined,
            mode,
            controller,
            setMessages,
            aiMessageId,
          );
        }
      } catch (err) {
        if (controller.signal.aborted) return;

        const raw = err instanceof Error ? err.message : 'An error occurred';
        const isQuota = /quota|rate.?limit|429|too many requests/i.test(raw);
        const isTimeout = /timeout|AbortError/i.test(raw);
        const userMessage = isQuota
          ? 'AI service quota has been reached. Please try again shortly.'
          : isTimeout
            ? 'Request timed out. Please try a simpler question.'
            : "Sorry, something went wrong. You can try rephrasing your question or ask me about inventory, sales, suppliers, forecasting, or inventory value.";
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
        sendingRef.current = false;
        isLoadingRef.current = false;
        setIsLoading(false);
        if (abortRef.current === controller) {
          abortRef.current = null;
        }
      }
    },
    [mode, isLoading, conversationId],
  );

  const retryLastMessage = useCallback(async () => {
    const failedText = lastFailedText.current;
    if (!failedText || isLoadingRef.current) return;

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
    isLoadingRef.current = true;
    setIsLoading(true);
    setError(null);

    try {
      await executeStreamQuery(
        failedText,
        conversationId ?? undefined,
        mode,
        controller,
        setMessages,
        aiMessageId,
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
          : "Sorry, something went wrong. You can try rephrasing your question or ask me about inventory, sales, suppliers, forecasting, or inventory value.";
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
      isLoadingRef.current = false;
      setIsLoading(false);
      if (abortRef.current === controller) {
        abortRef.current = null;
      }
    }
  }, [mode, conversationId]);

  const clearMessages = useCallback(() => {
    setMessages([]);
    setError(null);
    setMode('rag');
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
