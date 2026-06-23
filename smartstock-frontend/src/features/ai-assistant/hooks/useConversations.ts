import { useState, useCallback, useRef, useEffect } from 'react';
import type { Conversation, ConversationDetail } from '../types';
import {
  listConversations,
  createConversation,
  getConversation,
  getConversationMessages,
  deleteConversation,
} from '../api';

export default function useConversations() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeConversation, setActiveConversation] = useState<ConversationDetail | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const loadedRef = useRef(false);

  const loadConversations = useCallback(async () => {
    try {
      setError(null);
      setIsLoading(true);
      const data = await listConversations();
      setConversations(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load conversations');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!loadedRef.current) {
      loadedRef.current = true;
      loadConversations();
    }
  }, [loadConversations]);

  const selectConversation = useCallback(async (id: string) => {
    try {
      setError(null);
      setIsLoading(true);
      const data = await getConversation(id);
      setActiveConversation(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load conversation');
    } finally {
      setIsLoading(false);
    }
  }, []);

  const loadConversationMessages = useCallback(async (id: string) => {
    try {
      const messages = await getConversationMessages(id);
      setActiveConversation((prev) => {
        if (prev && prev.id === id) {
          return { ...prev, messages };
        }
        return prev;
      });
      return messages;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load messages');
      return [];
    }
  }, []);

  const startNewConversation = useCallback(async (title?: string) => {
    try {
      setError(null);
      setIsLoading(true);
      const data = await createConversation(title);
      setActiveConversation(data);
      await loadConversations();
      return data;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create conversation');
      return null;
    } finally {
      setIsLoading(false);
    }
  }, [loadConversations]);

  const removeConversation = useCallback(async (id: string) => {
    try {
      setError(null);
      setConversations((prev) => prev.filter((c) => c.id !== id));
      if (activeConversation?.id === id) {
        setActiveConversation(null);
      }
      await deleteConversation(id);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete conversation');
      await loadConversations();
    }
  }, [activeConversation, loadConversations]);

  const clearActive = useCallback(() => {
    setActiveConversation(null);
  }, []);

  return {
    conversations,
    activeConversation,
    isLoading,
    error,
    loadConversations,
    selectConversation,
    loadConversationMessages,
    startNewConversation,
    removeConversation,
    clearActive,
  };
}
