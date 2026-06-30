import api from '../../lib/axios';
import type { Document, DocumentChunk, UpdateDocumentPayload, UploadDocumentPayload } from './types';

type ApiEnvelope<T> = { status?: string; data?: T; message?: string; errors?: unknown };

export interface PaginatedDocuments {
  results: Document[];
  count: number;
}

function unwrap<T>(payload: T | ApiEnvelope<T>): T {
  if (payload && typeof payload === 'object' && 'data' in payload) {
    return (payload as ApiEnvelope<T>).data as T;
  }
  return payload as T;
}

export async function listDocuments(
  page: number = 1,
  pageSize: number = 20,
  ordering?: string,
  searchQuery?: string,
): Promise<PaginatedDocuments> {
  const params: Record<string, string | number | undefined> = {
    page,
    page_size: pageSize,
    ordering: ordering || undefined,
    search: searchQuery || undefined,
  };
  const { data } = await api.get('/ai/documents/', { params });
  const envelope = data as ApiEnvelope<Document[]> & { meta?: { total?: number } };
  const results = unwrap<Document[]>(envelope);
  return {
    results: Array.isArray(results) ? results : [],
    count: envelope?.meta?.total ?? (Array.isArray(results) ? results.length : 0),
  };
}

export async function getDocument(id: number): Promise<Document> {
  const { data } = await api.get<ApiEnvelope<Document> | Document>(`/ai/documents/${id}/`);
  return unwrap(data);
}

export async function uploadDocument(payload: UploadDocumentPayload): Promise<Document> {
  const formData = new FormData();
  formData.append('file', payload.file);
  formData.append('doc_type', payload.doc_type);

  const { data } = await api.post<ApiEnvelope<Document> | Document>(
    '/ai/documents/',
    formData,
    { headers: { 'Content-Type': 'multipart/form-data' } },
  );
  return unwrap(data);
}

export async function updateDocument(id: number, payload: UpdateDocumentPayload): Promise<Document> {
  const { data } = await api.patch<ApiEnvelope<Document> | Document>(
    `/ai/documents/${id}/`,
    payload,
  );
  return unwrap(data);
}

export async function deleteDocument(id: number): Promise<void> {
  await api.delete(`/ai/documents/${id}/`);
}

export async function getDocumentChunks(documentId: number): Promise<DocumentChunk[]> {
  const { data } = await api.get<ApiEnvelope<DocumentChunk[]> | DocumentChunk[]>(
    `/ai/documents/${documentId}/chunks/`,
  );
  return unwrap(data);
}
