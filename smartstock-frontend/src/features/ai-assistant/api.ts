import api from '../../lib/axios';
import { getApiBaseUrl } from '../../lib/config';
import { useAuthStore } from '../../store/authStore';
import type { ChatResponse, Conversation, ConversationDetail } from './types';

export { type ChatMode, type ChatResponse, type Conversation, type ConversationDetail } from './types';

export interface ChatRequest {
  query: string;
  mode?: 'auto' | 'nl_query' | 'rag';
  conversation_id?: string;
}

export async function sendChatMessage(request: ChatRequest, signal?: AbortSignal): Promise<ChatResponse> {
  const { data } = await api.post<ChatResponse>('/ai/chat/', request, { signal });
  return data;
}

export interface StreamEvent {
  type: 'metadata' | 'token' | 'done' | 'error';
  content?: string;
  engine?: string;
  mode?: string;
  conversation_id?: string;
  sources?: ChatResponse['sources'];
  action?: Record<string, unknown>;
  message?: string;
}

export async function* sendChatMessageStream(
  request: ChatRequest,
  signal?: AbortSignal,
): AsyncGenerator<StreamEvent> {
  const baseUrl = getApiBaseUrl();

  const token = useAuthStore.getState().token;
  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
  if (token) headers['Authorization'] = `Bearer ${token}`;

  const response = await fetch(`${baseUrl}/ai/chat/stream/`, {
    method: 'POST',
    headers,
    body: JSON.stringify(request),
    signal,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.message || `HTTP ${response.status}`);
  }

  const reader = response.body!.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  const TOKEN_TIMEOUT_MS = 20000;

  while (true) {
    const readPromise = reader.read();
    const timeoutPromise = new Promise<never>((_, reject) =>
      setTimeout(() => reject(new Error('Stream timeout')), TOKEN_TIMEOUT_MS),
    );

    let result: { done: boolean; value?: Uint8Array };
    try {
      result = await Promise.race([readPromise, timeoutPromise]);
    } catch {
      yield { type: 'error', message: 'Stream timed out waiting for response.' };
      break;
    }

    if (result.done) break;

    buffer += decoder.decode(result.value, { stream: true });
    const lines = buffer.split('\n');
    buffer = lines.pop() || '';

    let eventType = '';
    for (const line of lines) {
      if (line.startsWith('event: ')) {
        eventType = line.slice(7).trim();
      } else if (line.startsWith('data: ')) {
        const dataStr = line.slice(6);
        try {
          const data = JSON.parse(dataStr);
          yield { type: eventType as StreamEvent['type'], ...data };
        } catch {
          // Skip malformed JSON
        }
      }
    }
  }
}

export interface NLQueryResponse {
  answer: string;
  action: { type: string; filters: Record<string, unknown> };
  raw_data: Array<Record<string, unknown>>;
}

export async function sendNLQuery(query: string): Promise<NLQueryResponse> {
  const { data } = await api.post('/ai/nlquery/', { query });
  const unwrapped = data?.data ?? data;
  return unwrapped;
}

export async function transcribeAudio(audioBlob: Blob): Promise<string> {
  const formData = new FormData();
  formData.append('audio', audioBlob, 'recording.webm');
  const { data } = await api.post('/ai/transcribe/', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return data.text;
}

export async function listConversations(): Promise<Conversation[]> {
  const { data } = await api.get('/ai/conversations/');
  return Array.isArray(data) ? data : (data?.data ?? []);
}

export async function createConversation(title?: string): Promise<ConversationDetail> {
  const { data } = await api.post('/ai/conversations/', { title: title ?? 'New Conversation' });
  return data?.data ?? data;
}

export async function getConversation(id: string): Promise<ConversationDetail> {
  const { data } = await api.get(`/ai/conversations/${id}/`);
  return data?.data ?? data;
}

export async function getConversationMessages(id: string): Promise<ConversationDetail['messages']> {
  const { data } = await api.get(`/ai/conversations/${id}/messages/`);
  const unwrapped = data?.data ?? data;
  // Handle paginated response from PageNumberPagination
  const items = unwrapped?.results ?? unwrapped;
  return Array.isArray(items) ? items : [];
}

export async function deleteConversation(id: string): Promise<void> {
  await api.delete(`/ai/conversations/${id}/`);
}

