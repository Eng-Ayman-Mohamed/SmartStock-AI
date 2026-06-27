import { useState } from 'react';
import DocumentDetailModal from '../../features/documents/components/DocumentDetailModal';

interface CitationTagProps {
  sourceDocument: string;
  page: number;
  documentId?: number | null;
  chunkText?: string;
}

export default function CitationTag({ sourceDocument, page, documentId, chunkText }: CitationTagProps) {
  const [open, setOpen] = useState(false);

  return (
    <span className="relative inline-block">
      <button
        type="button"
        onClick={() => documentId && setOpen(true)}
        className="inline-flex items-center gap-1 px-2.5 py-1.5 rounded-full bg-purple-50 text-purple-800 hover:bg-purple-100 dark:bg-purple-900/30 dark:text-purple-200 dark:hover:bg-purple-900/50 transition-colors cursor-pointer align-middle min-h-[44px]"
        style={{ fontSize: '11px', lineHeight: '16px' }}
        aria-label={`Source: ${sourceDocument}, Page: ${page}`}
      >
        <span className="font-medium">Source:</span> {sourceDocument}, Page: {page}
      </button>
      {open && documentId && (
        <DocumentDetailModal
          documentId={documentId}
          citedPage={page}
          chunkText={chunkText}
          onClose={() => setOpen(false)}
        />
      )}
    </span>
  );
}
