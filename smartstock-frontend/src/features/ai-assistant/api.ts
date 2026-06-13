import api from '../../lib/axios';
import type { ChatMode, ChatResponse } from './types';

export { type ChatMode, type ChatResponse } from './types';

export interface ChatRequest {
  query: string;
  mode?: 'auto' | 'nl' | 'rag';
}

export async function sendChatMessage(request: ChatRequest): Promise<ChatResponse> {
  const { data } = await api.post<{ status: string; data: ChatResponse }>(
    '/ai/chat/',
    request
  );
  return data.data;
}

export async function sendRAGQuery(query: string): Promise<{ answer: string; sources: Array<{ document: string; page: number }> }> {
  const { data } = await api.post('/ai/rag-query/', { query });
  return data;
}

export async function sendChat(query: string, mode: ChatMode): Promise<ChatResponse> {
  const { data } = await api.post<ChatResponse>('/ai/chat/', { query, mode });
  return data;
}

export async function transcribeAudio(audioBlob: Blob): Promise<string> {
  const formData = new FormData();
  formData.append('audio', audioBlob, 'recording.webm');
  const { data } = await api.post('/ai/transcribe/', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return data.text;
}