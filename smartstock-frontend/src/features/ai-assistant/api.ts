import api from '../../lib/axios';
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

export async function deleteConversation(id: string): Promise<void> {
  await api.delete(`/ai/conversations/${id}/`);
}

export async function renameConversation(id: string, title: string): Promise<ConversationDetail> {
  const { data } = await api.patch(`/ai/conversations/${id}/`, { title });
  return data?.data ?? data;
}

export interface StockSnapshot {
  sku_code: string;
  product_name: string;
  quantity: number;
  reorder_point: number;
}

export async function fetchStockSnapshot(): Promise<StockSnapshot[]> {
  const { data } = await api.get<Record<string, unknown>[]>('/inventory/stock-levels/', {
    params: { page_size: 5 },
  });
  const items = data ?? [];
  return items.map((item) => ({
    sku_code: item.sku_code as string,
    product_name: item.product_name as string,
    quantity: (item.quantity as number) ?? 0,
    reorder_point: (item.reorder_point as number) ?? 0,
  }));
}
