import { Search, Check } from 'lucide-react';
import type { ChangeEvent } from 'react';
import type { StatusFilter } from '../types';

interface UsersFilterBarProps {
  query: string;
  onQueryChange: (value: string) => void;
  status: StatusFilter;
  onStatusChange: (value: StatusFilter) => void;
  totalCount: number;
  filteredCount: number;
}

const STATUSES: { value: StatusFilter; label: string }[] = [
  { value: 'all', label: 'All' },
  { value: 'active', label: 'Active' },
  { value: 'deactivated', label: 'Deactivated' },
];

export default function UsersFilterBar({
  query,
  onQueryChange,
  status,
  onStatusChange,
  totalCount,
  filteredCount,
}: UsersFilterBarProps) {
  return (
    <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-4">
      <div className="relative flex-1 max-w-md">
        <Search
          className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none"
          aria-hidden="true"
        />
        <input
          type="search"
          value={query}
          onChange={(e: ChangeEvent<HTMLInputElement>) => onQueryChange(e.target.value)}
          placeholder="Search by name or email"
          aria-label="Search users"
          className="w-full h-9 pl-9 pr-3 rounded-md border border-gray-100 bg-white text-body text-gray-900 placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-brand-100 focus:border-brand-600 transition-colors"
        />
      </div>

      <div className="flex items-center gap-3">
        <div className="inline-flex items-center rounded-md border border-gray-100 bg-white p-0.5">
          {STATUSES.map((s) => {
            const isSelected = s.value === status;
            return (
              <button
                key={s.value}
                type="button"
                onClick={() => onStatusChange(s.value)}
                className={`inline-flex items-center gap-1 px-2.5 h-8 rounded text-caption font-medium transition-colors ${
                  isSelected
                    ? 'bg-brand-50 text-brand-800'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
                aria-pressed={isSelected}
              >
                {isSelected && <Check className="w-3 h-3" aria-hidden="true" />}
                <span>{s.label}</span>
              </button>
            );
          })}
        </div>
        <span className="text-caption text-gray-600 hidden sm:inline">
          {filteredCount === totalCount ? (
            <>{totalCount} {totalCount === 1 ? 'user' : 'users'}</>
          ) : (
            <>
              {filteredCount} of {totalCount}
            </>
          )}
        </span>
      </div>
    </div>
  );
}
