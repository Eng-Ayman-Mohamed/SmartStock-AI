import api from '../../lib/axios';
import type { ChatResponse } from './types';

export { type ChatMode, type ChatResponse } from './types';

export interface ChatRequest {
  query: string;
  mode?: 'auto' | 'nl_query' | 'rag';
}

export async function sendChatMessage(request: ChatRequest): Promise<ChatResponse> {
  const { data } = await api.post<ChatResponse>('/ai/chat/', request);
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