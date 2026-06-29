import { Loader2, X, FileText, Hash, Calendar, User, ExternalLink } from 'lucide-react';
import Button from '../../../shared/components/Button';
import { useDocument, useDocumentChunks } from '../hooks/useDocuments';
import type { DocType } from '../types';

const DOC_TYPE_LABELS: Record<DocType, string> = {
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
    hour: '2-digit',
    minute: '2-digit',
  });
}

interface DocumentDetailModalProps {
  documentId: number | null;
  onClose: () => void;
  citedPage?: number;
  chunkText?: string;
}

export default function DocumentDetailModal({ documentId, onClose, citedPage, chunkText }: DocumentDetailModalProps) {
  const { data: doc, isLoading: docLoading } = useDocument(documentId);
  const { data: allChunks, isLoading: chunksLoading } = useDocumentChunks(documentId);

  const chunks = citedPage != null
    ? (allChunks ?? []).filter((c) => c.page_number === citedPage)
    : allChunks;

  if (documentId === null) return null;

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center">
      <div className="fixed inset-0 bg-black/40" onClick={onClose} aria-hidden="true" />
      <div className="relative z-10 mx-4 w-full max-w-2xl max-h-[85vh] rounded-lg border border-hairline bg-canvas shadow-lg flex flex-col">
        <div className="flex items-center justify-between px-6 py-4 border-b border-hairline">
          <h2 className="text-card-title text-ink">Document Details</h2>
          <button
            onClick={onClose}
            className="flex items-center justify-center w-11 h-11 rounded-md text-ink-faint hover:text-ink-secondary hover:bg-canvas-soft transition-colors"
            aria-label="Close"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto px-6 py-4 space-y-6">
          {docLoading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="w-6 h-6 text-brand-600 animate-spin" />
            </div>
          ) : doc ? (
            <>
              <div className="flex items-start gap-3">
                <div className="flex items-center justify-center w-10 h-10 rounded-lg bg-brand-50 dark:bg-brand-900/20 shrink-0">
                  <FileText className="w-5 h-5 text-brand-600" />
                </div>
                <div className="min-w-0">
                  <p className="text-body font-medium text-ink truncate">{doc.original_filename}</p>
                  <p className="text-caption text-ink-muted mt-0.5">
                    {DOC_TYPE_LABELS[doc.doc_type]} &middot; {formatBytes(doc.file_size)}
                  </p>
                </div>
                {doc.cloudinary_url && (
                  <a
                    href={doc.cloudinary_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="shrink-0 p-2.5 min-w-[44px] min-h-[44px] rounded-md text-ink-faint hover:text-brand-600 hover:bg-brand-50 transition-colors dark:hover:bg-brand-900/20"
                    title="Open original file"
                  >
                    <ExternalLink className="w-4 h-4" />
                  </a>
                )}
              </div>

              {citedPage != null && chunkText && (
                <div className="rounded-lg border border-purple-200 dark:border-purple-800 bg-purple-50 dark:bg-purple-900/20 p-4">
                  <h3 className="text-eyebrow uppercase text-purple-600 dark:text-purple-400 mb-2">
                    Cited Content — Page {citedPage}
                  </h3>
                  <p className="text-caption text-ink-secondary leading-relaxed whitespace-pre-wrap">
                    {chunkText}
                  </p>
                </div>
              )}

              <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 sm:gap-4">
                <div className="flex items-center gap-2 text-body text-ink-secondary">
                  <Hash className="w-4 h-4 text-ink-faint" />
                  <span>{doc.total_chunks} chunks</span>
                </div>
                <div className="flex items-center gap-2 text-body text-ink-secondary">
                  <User className="w-4 h-4 text-ink-faint" />
                  <span>{doc.uploaded_by_username || 'Unknown'}</span>
                </div>
                <div className="flex items-center gap-2 text-body text-ink-secondary">
                  <Calendar className="w-4 h-4 text-ink-faint" />
                  <span>Created {formatDate(doc.created_at)}</span>
                </div>
                <div className="flex items-center gap-2 text-body text-ink-secondary">
                  <Calendar className="w-4 h-4 text-ink-faint" />
                  <span>Ingested {formatDate(doc.ingested_at)}</span>
                </div>
              </div>

              <div>
                <h3 className="text-eyebrow uppercase text-ink-muted mb-2">
                  {citedPage != null ? `Chunks on Page ${citedPage}` : 'Chunks'}
                </h3>
                {chunksLoading ? (
                  <div className="flex items-center justify-center py-6">
                    <Loader2 className="w-5 h-5 text-brand-600 animate-spin" />
                  </div>
                ) : chunks && chunks.length > 0 ? (
                  <div className="space-y-2 max-h-64 overflow-y-auto">
                    {chunks.map((chunk) => (
                      <div
                        key={chunk.id}
                        className="rounded-md border border-hairline bg-canvas-soft p-3"
                      >
                        <div className="flex items-center gap-2 mb-1">
                          <span className="text-eyebrow text-ink-faint">
                            Page {chunk.page_number ?? '?'}
                          </span>
                          <span className="text-eyebrow text-ink-faint">&middot;</span>
                          <span className="text-eyebrow text-ink-faint">Chunk {chunk.id}</span>
                        </div>
                        <p className="text-caption text-ink-secondary line-clamp-3">
                          {chunk.chunk_text}
                        </p>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-caption text-ink-muted py-4 text-center">
                    {citedPage != null
                      ? `No chunks found for page ${citedPage}.`
                      : 'No chunks found.'}
                  </p>
                )}
              </div>
            </>
          ) : (
            <p className="text-caption text-ink-muted py-8 text-center">Document not found.</p>
          )}
        </div>

        <div className="flex justify-end px-6 py-3 border-t border-hairline">
          <Button variant="secondary" size="md" onClick={onClose}>
            Close
          </Button>
        </div>
      </div>
    </div>
  );
}
