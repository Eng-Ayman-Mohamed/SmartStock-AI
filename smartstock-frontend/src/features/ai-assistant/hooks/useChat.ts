import { useState } from 'react';
import { sendChatMessage, type ChatRequest, type ChatResponse } from '../api';

export function useChat() {
  const [isThinking, setIsThinking] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const send = async (query: string, mode: ChatRequest['mode'] = 'auto'): Promise<ChatResponse> => {
    setIsThinking(true);
    setError(null);
    try {
      const result = await sendChatMessage({ query, mode });
      return result;
    } catch (e) {
      const msg = e instanceof Error ? e.message : 'Failed to get response';
      setError(msg);
      throw e;
    } finally {
      setIsThinking(false);
    }
  };

  return { send, isThinking, error };
}
