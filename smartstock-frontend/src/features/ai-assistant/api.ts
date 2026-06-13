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
