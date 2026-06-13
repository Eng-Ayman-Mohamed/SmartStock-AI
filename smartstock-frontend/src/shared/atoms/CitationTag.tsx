import { useState, useRef, useEffect } from 'react';

interface CitationTagProps {
  sourceDocument: string;
  page: number;
  chunkText?: string;
}

export default function CitationTag({ sourceDocument, page, chunkText }: CitationTagProps) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLButtonElement>(null);
  const tooltipRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    function handleClick(e: MouseEvent) {
      if (
        ref.current && !ref.current.contains(e.target as Node) &&
        tooltipRef.current && !tooltipRef.current.contains(e.target as Node)
      ) {
        setOpen(false);
      }
    }
    function handleKeyDown(e: KeyboardEvent) {
      if (e.key === 'Escape') setOpen(false);
    }
    window.document.addEventListener('mousedown', handleClick);
    window.document.addEventListener('keydown', handleKeyDown);
    return () => {
      window.document.removeEventListener('mousedown', handleClick);
      window.document.removeEventListener('keydown', handleKeyDown);
    };
  }, [open]);

  return (
    <span className="relative inline-block">
      <button
        ref={ref}
        type="button"
        onClick={() => setOpen((prev) => !prev)}
        onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); setOpen((prev) => !prev); } }}
        className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-purple-50 text-purple-800 hover:bg-purple-100 transition-colors cursor-pointer align-middle"
        style={{ fontSize: '11px', lineHeight: '16px' }}
        aria-expanded={open}
        aria-label={`Source: ${sourceDocument}, Page: ${page}`}
      >
        <span className="font-medium">Source:</span> {sourceDocument}, Page: {page}
      </button>
      {open && chunkText && (
        <div
          ref={tooltipRef}
          role="tooltip"
          className="absolute z-50 bottom-full left-1/2 -translate-x-1/2 mb-2 w-72 p-3 bg-ink text-white text-caption leading-relaxed rounded-lg shadow-elevated"
        >
          {chunkText}
          <div className="absolute top-full left-1/2 -translate-x-1/2 w-2 h-2 bg-ink rotate-45 -mt-1" />
        </div>
      )}
    </span>
  );
}
