import api from '../../lib/axios';
import type { Document, DocumentChunk, UpdateDocumentPayload, UploadDocumentPayload } from './types';

type ApiEnvelope<T> = { status?: string; data?: T; message?: string; errors?: unknown };

function unwrap<T>(payload: T | ApiEnvelope<T>): T {
  if (payload && typeof payload === 'object' && 'data' in payload) {
    return (payload as ApiEnvelope<T>).data as T;
  }
  return payload as T;
}

export async function listDocuments(): Promise<Document[]> {
  const { data } = await api.get<ApiEnvelope<Document[]> | Document[]>('/ai/documents/');
  return unwrap(data);
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
