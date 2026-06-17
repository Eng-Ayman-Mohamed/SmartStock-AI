import { memo, type ReactNode } from 'react';
import { ArrowUpDown, ChevronDown, ChevronLeft, ChevronRight, ChevronsLeft, ChevronsRight, ChevronUp } from 'lucide-react';
import Button from './Button';

export interface Column<T> {
  key: string;
  label: string;
  align?: 'left' | 'center' | 'right';
  width?: string;
  render: (row: T) => ReactNode;
  sortable?: boolean;
  sortKey?: string;
  sortOrder?: 'asc' | 'desc';
}

export interface PaginationConfig {
  currentPage: number;
  totalPages: number;
  total: number;
  startItem: number;
  endItem: number;
  hasPrev: boolean;
  hasNext: boolean;
  pages: number[];
  onPageChange: (page: number) => void;
  itemLabel?: string;
}

interface DataTableProps<T> {
  columns: Column<T>[];
  data: T[];
  keyExtractor: (row: T) => string;
  caption?: string;
  emptyState?: ReactNode;
  pagination?: PaginationConfig;
  onSort?: (key: string) => void;
}

function DataTable<T>({ columns, data, keyExtractor, caption, emptyState, pagination, onSort }: DataTableProps<T>) {
  if (data.length === 0 && emptyState) {
    return <>{emptyState}</>;
  }

  return (
    <div>
      <div className="overflow-x-auto">
        <table className="w-full table-fixed border-collapse">
          {caption && <caption className="sr-only">{caption}</caption>}
          <thead>
            <tr className="bg-canvas-soft border-b border-hairline">
              {columns.map((col) => (
                <th
                  key={col.key}
                  scope="col"
                  className={`h-9 px-3 text-eyebrow text-ink-secondary select-none ${
                    col.align === 'right' ? 'text-right' : col.align === 'center' ? 'text-center' : 'text-left'
                  }`}
                  style={col.width ? { width: col.width } : undefined}
                >
                  {col.sortable ? (
                    <button
                      type="button"
                      onClick={() => onSort?.(col.key)}
                      className="inline-flex items-center gap-1 hover:text-ink transition-colors cursor-pointer"
                    >
                      {col.label}
                      {col.sortOrder === 'asc' ? (
                        <ChevronUp className="w-3 h-3" />
                      ) : col.sortOrder === 'desc' ? (
                        <ChevronDown className="w-3 h-3" />
                      ) : (
                        <ArrowUpDown className="w-3 h-3 text-ink-faint" />
                      )}
                    </button>
                  ) : (
                    col.label
                  )}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {data.map((row) => (
              <tr
                key={keyExtractor(row)}
                className="bg-canvas border-b border-hairline hover:bg-canvas-soft transition-colors duration-150 group"
                tabIndex={0}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    const btn = e.currentTarget.querySelector('button, a, [role="button"]');
                    if (btn instanceof HTMLElement) btn.click();
                  }
                }}
                role="row"
              >
                {columns.map((col) => (
                  <td
                    key={col.key}
                    className={`h-11 px-3 text-body text-ink-secondary truncate ${
                      col.align === 'right' ? 'text-right' : col.align === 'center' ? 'text-center' : 'text-left'
                    }`}
                  >
                    {col.render(row)}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {pagination && pagination.total > 0 && (
        <div className="flex flex-col gap-3 border-t border-hairline px-4 py-3 sm:flex-row sm:items-center sm:justify-between">
          <p className="text-caption text-ink-muted">
            Showing{" "}
            <span className="tabular-nums text-ink-secondary">
              {pagination.startItem}
            </span>
            {" - "}
            <span className="tabular-nums text-ink-secondary">
              {pagination.endItem}
            </span>
            {" of "}
            <span className="tabular-nums text-ink-secondary">
              {pagination.total}
            </span>
            {pagination.itemLabel ? <> {pagination.itemLabel}</> : null}
          </p>
          <div className="flex items-center gap-1" aria-label="Pagination">
            <Button
              variant="utility"
              size="sm"
              className="h-11 w-11 px-0"
              onClick={() => pagination.onPageChange(1)}
              disabled={!pagination.hasPrev}
              aria-label="First page"
              title="First page"
            >
              <ChevronsLeft className="h-5 w-5" />
            </Button>
            <Button
              variant="utility"
              size="sm"
              className="h-11 w-11 px-0"
              onClick={() => pagination.onPageChange(Math.max(1, pagination.currentPage - 1))}
              disabled={!pagination.hasPrev}
              aria-label="Previous page"
              title="Previous page"
            >
              <ChevronLeft className="h-5 w-5" />
            </Button>
            {pagination.pages.map((pageNumber, index) =>
              pageNumber === -1 ? (
                <span
                  key={`gap-${index}`}
                  className="flex h-11 w-11 items-center justify-center text-caption text-ink-faint"
                >
                  ...
                </span>
              ) : (
                <Button
                  key={pageNumber}
                  variant={pageNumber === pagination.currentPage ? 'primary' : 'utility'}
                  size="sm"
                  className="h-11 w-11 px-0 tabular-nums"
                  onClick={() => pagination.onPageChange(pageNumber)}
                  aria-label={`Page ${pageNumber}`}
                  title={`Page ${pageNumber}`}
                >
                  {pageNumber}
                </Button>
              ),
            )}
            <Button
              variant="utility"
              size="sm"
              className="h-11 w-11 px-0"
              onClick={() => pagination.onPageChange(Math.min(pagination.totalPages, pagination.currentPage + 1))}
              disabled={!pagination.hasNext}
              aria-label="Next page"
              title="Next page"
            >
              <ChevronRight className="h-5 w-5" />
            </Button>
            <Button
              variant="utility"
              size="sm"
              className="h-11 w-11 px-0"
              onClick={() => pagination.onPageChange(pagination.totalPages)}
              disabled={!pagination.hasNext}
              aria-label="Last page"
              title="Last page"
            >
              <ChevronsRight className="h-5 w-5" />
            </Button>
          </div>
        </div>
      )}
    </div>
  );
};

export default memo(DataTable) as typeof DataTable;
