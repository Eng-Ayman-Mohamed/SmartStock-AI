import { useState } from 'react';
import {
  Eye,
  FileText,
  Loader2,
  Pencil,
  Plus,
  Trash2,
  Upload,
} from 'lucide-react';
import { useAuthStore } from '../../../store/authStore';
import { usePagination } from '../../../shared/hooks/usePagination';
import Card from '../../../shared/components/Card';
import Button from '../../../shared/components/Button';
import DataTable, { type Column, type PaginationConfig } from '../../../shared/components/DataTable';
import EmptyState from '../../../shared/components/EmptyState';
import DocumentDetailModal from '../components/DocumentDetailModal';
import DocumentEditModal from '../components/DocumentEditModal';
import DocumentUploadModal from '../components/DocumentUploadModal';
import { useDocuments, useDeleteDocument } from '../hooks/useDocuments';
import type { Document } from '../types';

const PAGE_SIZE = 20;

const DOC_TYPE_LABELS: Record<string, string> = {
  policy: 'Policy',
  contract: 'Contract',
  procedure: 'Procedure',
  specification: 'Specification',
};

function formatBytes(bytes: number) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
}

function formatDate(iso: string | null) {
  if (!iso) return '—';
  return new Date(iso).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
}

export default function DocumentsPage() {
  const [uploadOpen, setUploadOpen] = useState(false);
  const [deleteId, setDeleteId] = useState<number | null>(null);
  const [detailId, setDetailId] = useState<number | null>(null);
  const [editId, setEditId] = useState<number | null>(null);
  const [page, setPage] = useState(1);
  const [sortField, setSortField] = useState('');
  const [sortOrder, setSortOrder] = useState('');
  const user = useAuthStore((s) => s.user);
  const isAdmin = user?.role === 'admin' || user?.role === 'manager';

  function handleSort(key: string) {
    if (sortField === key && sortOrder === 'asc') {
      setSortOrder('desc');
    } else if (sortField === key && sortOrder === 'desc') {
      setSortField('');
      setSortOrder('');
    } else {
      setSortField(key);
      setSortOrder('asc');
    }
    setPage(1);
  }

  const { data, isLoading, error } = useDocuments(page, PAGE_SIZE, sortField || undefined, sortOrder || undefined);
  const documents = data?.results ?? [];
  const totalCount = data?.count ?? 0;
  const deleteDoc = useDeleteDocument();

  const columns: Column<Document>[] = [
    {
      key: 'original_filename',
      label: 'Filename',
      sortable: true,
      sortOrder: sortField === 'original_filename' ? (sortOrder as 'asc' | 'desc') : undefined,
      render: (row) => (
        <div className="flex items-center gap-2 min-w-0">
          <FileText className="w-4 h-4 shrink-0 text-brand-600" />
          <span className="truncate font-medium text-ink">{row.original_filename}</span>
        </div>
      ),
    },
    {
      key: 'doc_type',
      label: 'Type',
      sortable: true,
      sortOrder: sortField === 'doc_type' ? (sortOrder as 'asc' | 'desc') : undefined,
      render: (row) => (
        <span className="inline-flex items-center rounded-full bg-brand-50 px-2 py-0.5 text-eyebrow text-brand-700 dark:bg-brand-900/30 dark:text-brand-200">
          {DOC_TYPE_LABELS[row.doc_type] || row.doc_type}
        </span>
      ),
    },
    {
      key: 'file_size',
      label: 'Size',
      sortable: true,
      sortOrder: sortField === 'file_size' ? (sortOrder as 'asc' | 'desc') : undefined,
      render: (row) => <span className="tabular-nums text-ink-secondary">{formatBytes(row.file_size)}</span>,
    },
    {
      key: 'total_chunks',
      label: 'Chunks',
      sortable: true,
      sortOrder: sortField === 'total_chunks' ? (sortOrder as 'asc' | 'desc') : undefined,
      render: (row) => (
        <span className="tabular-nums text-ink-secondary">
          {row.total_chunks > 0 ? row.total_chunks : '—'}
        </span>
      ),
    },
    {
      key: 'uploaded_by_username',
      label: 'Uploaded By',
      sortable: true,
      sortOrder: sortField === 'uploaded_by_username' ? (sortOrder as 'asc' | 'desc') : undefined,
      render: (row) => <span className="text-ink-secondary">{row.uploaded_by_username || '—'}</span>,
    },
    {
      key: 'ingested_at',
      label: 'Ingested',
      sortable: true,
      sortOrder: sortField === 'ingested_at' ? (sortOrder as 'asc' | 'desc') : undefined,
      render: (row) => <span className="text-ink-secondary">{formatDate(row.ingested_at)}</span>,
    },
  ];

  function renderActions(row: Document) {
    if (!isAdmin) return null;
    return (
      <div className="flex items-center justify-end gap-1">
        <button
          onClick={() => setDetailId(row.id)}
          className="flex items-center justify-center w-7 h-7 rounded-md text-ink-faint hover:text-brand-600 hover:bg-brand-50 transition-colors dark:hover:bg-brand-900/20"
          aria-label={`View ${row.original_filename}`}
          title="View details"
        >
          <Eye className="w-4 h-4" />
        </button>
        <button
          onClick={() => setEditId(row.id)}
          className="flex items-center justify-center w-7 h-7 rounded-md text-ink-faint hover:text-ink-secondary hover:bg-canvas-soft transition-colors"
          aria-label={`Edit ${row.original_filename}`}
          title="Edit document"
        >
          <Pencil className="w-4 h-4" />
        </button>
        <button
          onClick={() => setDeleteId(row.id)}
          className="flex items-center justify-center w-7 h-7 rounded-md text-ink-faint hover:text-red-600 hover:bg-red-50 transition-colors dark:hover:bg-red-900/30"
          aria-label={`Delete ${row.original_filename}`}
          title="Delete document"
        >
          <Trash2 className="w-4 h-4" />
        </button>
      </div>
    );
  }

  const maxPage = Math.max(1, Math.ceil(totalCount / PAGE_SIZE));
  const currentPage = Math.min(page, maxPage);
  const pagination = usePagination({ total: totalCount, pageSize: PAGE_SIZE, currentPage });

  const paginationConfig: PaginationConfig = {
    currentPage,
    totalPages: pagination.totalPages,
    total: totalCount,
    startItem: pagination.startItem,
    endItem: pagination.endItem,
    hasPrev: pagination.hasPrev,
    hasNext: pagination.hasNext,
    pages: pagination.pages,
    onPageChange: (p) => setPage(p),
    itemLabel: 'documents',
  };

  return (
    <div className="space-y-6 animate-fadeIn flex-1 min-h-0 flex flex-col">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-page-heading text-ink">Documents</h1>
          <p className="text-body text-ink-muted mt-1">
            Manage PDF documents used by the AI assistant for RAG queries.
          </p>
        </div>
        <Button variant="primary" size="md" onClick={() => setUploadOpen(true)}>
          <Plus className="w-4 h-4" /> Upload Document
        </Button>
      </div>

      <Card noPadding>
        {isLoading ? (
          <div className="flex items-center justify-center py-16">
            <Loader2 className="w-6 h-6 text-brand-600 animate-spin" />
          </div>
        ) : error ? (
          <div className="rounded-md border border-red-200 bg-red-50 mx-6 my-4 px-4 py-3 text-body text-red-800 dark:border-red-800 dark:bg-red-900/30 dark:text-red-200">
            Failed to load documents. Please try again.
          </div>
        ) : (
          <DataTable
            columns={columns}
            data={documents}
            keyExtractor={(row) => String(row.id)}
            caption="RAG documents"
            onSort={handleSort}
            actionsLabel={isAdmin ? 'Actions' : undefined}
            renderActions={renderActions}
            pagination={documents.length > 0 ? paginationConfig : undefined}
            emptyState={
              <EmptyState
                icon={Upload}
                heading="No documents yet"
                body="Upload a PDF to get started. Documents are chunked, embedded, and made searchable for the AI assistant."
                actionLabel="Upload Document"
                onAction={() => setUploadOpen(true)}
              />
            }
          />
        )}
      </Card>

      <DocumentUploadModal open={uploadOpen} onClose={() => setUploadOpen(false)} />
      <DocumentDetailModal documentId={detailId} onClose={() => setDetailId(null)} />
      <DocumentEditModal documentId={editId} onClose={() => setEditId(null)} />

      {deleteId !== null && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div className="fixed inset-0 bg-black/40" onClick={() => setDeleteId(null)} aria-hidden="true" />
          <div className="relative z-10 w-full max-w-sm rounded-lg border border-hairline bg-canvas shadow-lg p-6 space-y-4">
            <h3 className="text-card-title text-ink">Delete Document</h3>
            <p className="text-body text-ink-muted">
              This will remove the document from the list and deactivate its chunks. The AI assistant will no longer search this document.
            </p>
            <div className="flex gap-3 border-t border-hairline pt-4">
              <Button variant="secondary" size="md" className="flex-1" onClick={() => setDeleteId(null)} disabled={deleteDoc.isPending}>
                Cancel
              </Button>
              <Button
                variant="danger"
                size="md"
                className="flex-1"
                onClick={() => {
                  if (deleteId !== null) {
                    deleteDoc.mutate(deleteId, { onSuccess: () => setDeleteId(null) });
                  }
                }}
                disabled={deleteDoc.isPending}
              >
                {deleteDoc.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Trash2 className="w-4 h-4" />}
                Delete
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
