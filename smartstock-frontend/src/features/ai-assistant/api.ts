import api from '../../lib/axios';

export interface ChatRequest {
  query: string;
  mode?: 'auto' | 'nl' | 'rag';
}

export interface ChatResponse {
  engine: string;
  mode: string;
  answer: string;
  sources?: Array<{ document: string; page?: number }> | null;
  action?: { type: string; filters: Record<string, unknown> } | null;
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

export async function transcribeAudio(audioBlob: Blob): Promise<string> {
  const formData = new FormData();
  formData.append('audio', audioBlob, 'recording.webm');
  const { data } = await api.post('/ai/transcribe/', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return data.text;
}
