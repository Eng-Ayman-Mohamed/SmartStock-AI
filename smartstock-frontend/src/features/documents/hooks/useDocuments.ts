import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import axios from 'axios';
import { useToastStore } from '../../../store/toastStore';
import * as documentsApi from '../api';
import type { UpdateDocumentPayload, UploadDocumentPayload } from '../types';

function errorMessage(err: unknown, fallback: string) {
  if (axios.isAxiosError(err)) {
    const data = err.response?.data as { message?: string; detail?: string; errors?: unknown } | undefined;
    return data?.message || data?.detail || fallback;
  }
  return fallback;
}

export function useDocuments() {
  return useQuery({
    queryKey: ['documents'],
    queryFn: documentsApi.listDocuments,
  });
}

export function useDocument(id: number | null) {
  return useQuery({
    queryKey: ['documents', id],
    queryFn: () => documentsApi.getDocument(id!),
    enabled: id !== null,
  });
}

export function useDocumentChunks(documentId: number | null) {
  return useQuery({
    queryKey: ['documents', documentId, 'chunks'],
    queryFn: () => documentsApi.getDocumentChunks(documentId!),
    enabled: documentId !== null,
  });
}

export function useUploadDocument() {
  const queryClient = useQueryClient();
  const addToast = useToastStore((s) => s.addToast);

  return useMutation({
    mutationFn: (payload: UploadDocumentPayload) => documentsApi.uploadDocument(payload),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['documents'] });
      addToast('Document uploaded and ingested successfully.', 'success');
    },
    onError: (err) => {
      addToast(errorMessage(err, 'Failed to upload document.'), 'error');
    },
  });
}

export function useUpdateDocument() {
  const queryClient = useQueryClient();
  const addToast = useToastStore((s) => s.addToast);

  return useMutation({
    mutationFn: ({ id, payload }: { id: number; payload: UpdateDocumentPayload }) =>
      documentsApi.updateDocument(id, payload),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['documents'] });
      addToast('Document updated.', 'success');
    },
    onError: (err) => {
      addToast(errorMessage(err, 'Failed to update document.'), 'error');
    },
  });
}

export function useDeleteDocument() {
  const queryClient = useQueryClient();
  const addToast = useToastStore((s) => s.addToast);

  return useMutation({
    mutationFn: (id: number) => documentsApi.deleteDocument(id),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['documents'] });
      addToast('Document deleted.', 'info');
    },
    onError: (err) => {
      addToast(errorMessage(err, 'Failed to delete document.'), 'error');
    },
  });
}
