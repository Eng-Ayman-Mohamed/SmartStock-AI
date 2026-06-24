import { useState } from 'react';
import { Loader2, X } from 'lucide-react';
import Button from '../../../shared/components/Button';
import { useDocument, useUpdateDocument } from '../hooks/useDocuments';
import type { DocType } from '../types';

const DOC_TYPE_OPTIONS: { value: DocType; label: string }[] = [
  { value: 'policy', label: 'Policy' },
  { value: 'contract', label: 'Contract' },
  { value: 'procedure', label: 'Procedure' },
  { value: 'specification', label: 'Specification' },
];

interface DocumentEditModalProps {
  documentId: number | null;
  onClose: () => void;
}

export default function DocumentEditModal({ documentId, onClose }: DocumentEditModalProps) {
  const { data: doc, isLoading: docLoading } = useDocument(documentId);
  const updateDoc = useUpdateDocument();
  const [docType, setDocType] = useState<DocType>('policy');

  if (documentId === null) return null;

  function handleSave() {
    if (documentId === null) return;
    updateDoc.mutate(
      { id: documentId, payload: { doc_type: docType } },
      { onSuccess: onClose },
    );
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="fixed inset-0 bg-black/40" onClick={onClose} aria-hidden="true" />
      <div className="relative z-10 mx-4 w-full max-w-md rounded-lg border border-hairline bg-canvas shadow-lg p-6 space-y-5">
        <div className="flex items-center justify-between">
          <h2 className="text-card-title text-ink">Edit Document</h2>
          <button
            onClick={onClose}
            className="flex items-center justify-center w-7 h-7 rounded-md text-ink-faint hover:text-ink-secondary hover:bg-canvas-soft transition-colors"
            aria-label="Close"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {docLoading ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="w-6 h-6 text-brand-600 animate-spin" />
          </div>
        ) : doc ? (
          <>
            <p className="text-body text-ink-secondary truncate">{doc.original_filename}</p>

            <div>
              <label className="text-caption text-ink-muted mb-1 block" htmlFor="edit-doc-type">
                Document Type
              </label>
              <select
                id="edit-doc-type"
                defaultValue={doc.doc_type}
                onChange={(e) => setDocType(e.target.value as DocType)}
                className="h-9 w-full rounded-md border border-hairline bg-canvas px-3 text-body text-ink transition-colors hover:border-ink-muted focus:border-brand-600 focus:outline-none"
              >
                {DOC_TYPE_OPTIONS.map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
            </div>

            <div className="flex gap-3 border-t border-hairline pt-4">
              <Button variant="secondary" size="md" className="flex-1" onClick={onClose} disabled={updateDoc.isPending}>
                Cancel
              </Button>
              <Button
                variant="primary"
                size="md"
                className="flex-1"
                onClick={handleSave}
                disabled={updateDoc.isPending || docType === doc.doc_type}
              >
                {updateDoc.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : null}
                Save Changes
              </Button>
            </div>
          </>
        ) : (
          <p className="text-caption text-ink-muted py-4 text-center">Document not found.</p>
        )}
      </div>
    </div>
  );
}
