import { useMemo } from 'react';

interface UsePaginationOptions {
  total: number;
  pageSize: number;
  currentPage: number;
}

interface UsePaginationResult {
  pages: number[];
  totalPages: number;
  hasPrev: boolean;
  hasNext: boolean;
  startItem: number;
  endItem: number;
}

export function usePagination({ total, pageSize, currentPage }: UsePaginationOptions): UsePaginationResult {
  const totalPages = Math.max(1, Math.ceil(total / pageSize));

  const pages = useMemo(() => {
    const delta = 2;
    const range: number[] = [];
    for (let i = Math.max(1, currentPage - delta); i <= Math.min(totalPages, currentPage + delta); i++) {
      range.push(i);
    }
    if (range[0] > 1) {
      if (range[0] > 2) range.unshift(-1);
      range.unshift(1);
    }
    if (range[range.length - 1] < totalPages) {
      if (range[range.length - 1] < totalPages - 1) range.push(-1);
      range.push(totalPages);
    }
    return range;
  }, [totalPages, currentPage]);

  return {
    pages,
    totalPages,
    hasPrev: currentPage > 1,
    hasNext: currentPage < totalPages,
    startItem: (currentPage - 1) * pageSize + 1,
    endItem: Math.min(currentPage * pageSize, total),
  };
}
