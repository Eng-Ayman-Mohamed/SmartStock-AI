import { useRef, useState } from 'react';
import { FileText, Loader2, Upload, X } from 'lucide-react';
import Button from '../../../shared/components/Button';
import Select from '../../../shared/components/Select';
import { useUploadDocument } from '../hooks/useDocuments';
import type { DocType } from '../types';

const MAX_FILE_SIZE = 10 * 1024 * 1024;

const DOC_TYPE_OPTIONS: { value: DocType; label: string }[] = [
  { value: 'policy', label: 'Policy' },
  { value: 'contract', label: 'Contract' },
  { value: 'procedure', label: 'Procedure' },
  { value: 'specification', label: 'Specification' },
];

function formatBytes(bytes: number) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
}

function validateFile(file: File) {
  if (file.type !== 'application/pdf') {
    return 'Only PDF files are accepted.';
  }
  if (file.size > MAX_FILE_SIZE) {
    return 'File size must be less than 10 MB.';
  }
  return '';
}

interface DocumentUploadModalProps {
  open: boolean;
  onClose: () => void;
}

export default function DocumentUploadModal({ open, onClose }: DocumentUploadModalProps) {
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [docType, setDocType] = useState<DocType>('policy');
  const [dragActive, setDragActive] = useState(false);
  const [fileError, setFileError] = useState('');
  const upload = useUploadDocument();

  function reset() {
    setSelectedFile(null);
    setDocType('policy');
    setFileError('');
    setDragActive(false);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  }

  function handleClose() {
    reset();
    onClose();
  }

  function selectFile(file: File) {
    const error = validateFile(file);
    setFileError(error);
    if (error) {
      setSelectedFile(null);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
      return;
    }
    setSelectedFile(file);
  }

  function handleFiles(files: FileList | null) {
    const file = files?.[0];
    if (!file) return;
    selectFile(file);
  }

  async function handleUpload() {
    if (!selectedFile) return;
    try {
      await upload.mutateAsync({ file: selectedFile, doc_type: docType });
      handleClose();
    } catch {
      // toast handled by hook
    }
  }

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="fixed inset-0 bg-black/40" onClick={onClose} aria-hidden="true" />
      <div className="relative z-10 mx-4 w-full max-w-lg rounded-lg border border-hairline bg-canvas shadow-lg p-6 space-y-5">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-card-title text-ink">Upload Document</h2>
            <p className="text-caption text-ink-muted mt-0.5">PDF only, max 10 MB. Will be chunked and embedded for RAG.</p>
          </div>
          <button
            onClick={onClose}
            className="flex items-center justify-center w-11 h-11 rounded-md text-ink-faint hover:text-ink-secondary hover:bg-canvas-soft transition-colors"
            aria-label="Close"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <div>
          <label className="text-caption text-ink-muted mb-1 block" htmlFor="doc-type">
            Document Type
          </label>
          <Select
            id="doc-type"
            value={docType}
            onChange={(e) => setDocType(e.target.value as DocType)}
          >
            {DOC_TYPE_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </Select>
        </div>

        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,application/pdf"
          className="sr-only"
          onChange={(event) => handleFiles(event.target.files)}
        />

        <button
          type="button"
          className={`flex w-full flex-col items-center justify-center rounded-lg border-2 border-dashed px-6 py-10 text-center transition-colors ${
            dragActive ? 'border-brand-600 bg-brand-50' : 'border-hairline bg-canvas hover:border-brand-200 hover:bg-brand-50/30'
          }`}
          onClick={() => fileInputRef.current?.click()}
          onDragEnter={(e) => { e.preventDefault(); setDragActive(true); }}
          onDragOver={(e) => e.preventDefault()}
          onDragLeave={(e) => { e.preventDefault(); setDragActive(false); }}
          onDrop={(e) => { e.preventDefault(); setDragActive(false); handleFiles(e.dataTransfer.files); }}
          disabled={upload.isPending}
        >
          {upload.isPending ? (
            <Loader2 className="w-10 h-10 text-brand-600 mb-3 animate-spin" />
          ) : (
            <Upload className="w-10 h-10 text-ink-faint mb-3" />
          )}
          <span className="text-body text-ink-secondary font-medium">
            {selectedFile ? selectedFile.name : 'Drop PDF here or click to browse'}
          </span>
          {selectedFile && (
            <span className="text-caption text-ink-muted mt-1">{formatBytes(selectedFile.size)}</span>
          )}
        </button>

        {fileError && (
          <div className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-caption text-red-800 dark:border-red-800 dark:bg-red-900/30 dark:text-red-200">
            {fileError}
          </div>
        )}

        {selectedFile && !fileError && (
          <div className="flex items-center gap-3 rounded-md border border-hairline bg-canvas-soft px-3 py-2">
            <FileText className="w-5 h-5 shrink-0 text-brand-600" />
            <div className="min-w-0">
              <p className="truncate text-body font-medium text-ink">{selectedFile.name}</p>
              <p className="text-caption text-ink-muted">{formatBytes(selectedFile.size)}</p>
            </div>
          </div>
        )}

        <div className="flex gap-3 border-t border-hairline pt-4">
          <Button variant="secondary" size="md" className="flex-1" onClick={onClose} disabled={upload.isPending}>
            Cancel
          </Button>
          <Button
            variant="primary"
            size="md"
            className="flex-1"
            onClick={handleUpload}
            disabled={!selectedFile || !!fileError || upload.isPending}
          >
            {upload.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Upload className="w-4 h-4" />}
            Upload &amp; Ingest
          </Button>
        </div>
      </div>
    </div>
  );
}
