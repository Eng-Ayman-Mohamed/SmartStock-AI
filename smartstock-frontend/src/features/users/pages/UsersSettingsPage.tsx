import { useCallback, useMemo, useState } from 'react';
import { Users, UserPlus } from 'lucide-react';
import Button from '../../../shared/components/Button';
import EmptyState from '../../../shared/components/EmptyState';
import Skeleton from '../../../shared/components/Skeleton';
import InviteUserModal from '../components/InviteUserModal';
import UsersFilterBar from '../components/UsersFilterBar';
import UsersTable from '../components/UsersTable';
import { useUsers } from '../hooks/useUsers';
import { useDebounce } from '../../../shared/hooks/useDebounce';
import { usePagination } from '../../../shared/hooks/usePagination';
import type { StatusFilter } from '../types';
import type { PaginationConfig } from '../../../shared/components/DataTable';

const PAGE_SIZE = 20;

/** Map UI status filter to backend `is_active` param. */
function statusToIsActive(status: StatusFilter): boolean | undefined {
  if (status === 'active') return true;
  if (status === 'deactivated') return false;
  return undefined;
}

export default function UsersSettingsPage() {
  const [inviteOpen, setInviteOpen] = useState(false);
  const [query, setQuery] = useState('');
  const [status, setStatus] = useState<StatusFilter>('all');
  const [page, setPage] = useState(1);
  const [sortField, setSortField] = useState('');
  const [sortOrder, setSortOrder] = useState('');

  const debouncedSearch = useDebounce(query, 300);
  const isActive = statusToIsActive(status);

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

  const { data, isLoading, isError, error, refetch } = useUsers(
    debouncedSearch || undefined,
    page,
    PAGE_SIZE,
    isActive,
    sortField || undefined,
    sortOrder || undefined,
  );

  const users = data?.results ?? [];
  const totalCount = data?.count ?? 0;
  const maxPage = Math.max(1, Math.ceil(totalCount / PAGE_SIZE));
  const currentPage = Math.min(page, maxPage);

  const pagination = usePagination({ total: totalCount, pageSize: PAGE_SIZE, currentPage });

  const handlePageChange = useCallback((p: number) => {
    setPage(p);
  }, []);

  const paginationConfig = useMemo<PaginationConfig>(() => ({
    currentPage,
    totalPages: pagination.totalPages,
    total: totalCount,
    startItem: pagination.startItem,
    endItem: pagination.endItem,
    hasPrev: pagination.hasPrev,
    hasNext: pagination.hasNext,
    pages: pagination.pages,
    onPageChange: handlePageChange,
    itemLabel: 'team members',
  }), [
    currentPage,
    pagination.totalPages,
    pagination.startItem,
    pagination.endItem,
    pagination.hasPrev,
    pagination.hasNext,
    pagination.pages,
    totalCount,
    handlePageChange,
  ]);

  return (
    <div className="space-y-6 animate-fadeIn">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div>
          <h1 className="text-page-heading text-ink">Team & permissions</h1>
          <p className="text-body text-ink-muted mt-1">
            Manage who can access SmartStock AI and what they can do.
          </p>
        </div>
        <Button variant="primary" size="md" onClick={() => setInviteOpen(true)}>
          <UserPlus className="w-4 h-4" aria-hidden="true" />
          <span>Invite user</span>
        </Button>
      </div>

      {isLoading ? (
        <div className="bg-canvas border border-hairline rounded-lg p-5 space-y-3">
          <Skeleton className="h-4 w-1/3" />
          <Skeleton className="h-4 w-2/3" />
          <Skeleton className="h-4 w-1/2" />
        </div>
      ) : isError ? (
        <div className="bg-canvas border border-red-100 rounded-lg p-5">
          <p className="text-body text-red-600">
            Couldn't load users. {(error as Error)?.message ?? 'Unknown error.'}
          </p>
          <Button variant="secondary" size="sm" className="mt-3" onClick={() => refetch()}>
            Try again
          </Button>
        </div>
      ) : (
        <>
          <UsersFilterBar
            query={query}
            onQueryChange={(v) => { setQuery(v); setPage(1); }}
            status={status}
            onStatusChange={(v) => { setStatus(v); setPage(1); }}
            totalCount={totalCount}
            filteredCount={totalCount}
          />
          <UsersTable
            users={users}
            sortField={sortField || undefined}
            sortOrder={sortOrder || undefined}
            onSort={handleSort}
            emptyState={
              totalCount > 0 ? (
                <EmptyState
                  icon={Users}
                  heading="No matches"
                  body={`No users match the current ${query ? 'search' : 'filter'}.`}
                />
              ) : (
                <EmptyState
                  icon={Users}
                  heading="No team members yet"
                  body="Invite your first user to start collaborating on SmartStock AI."
                  actionLabel="Invite user"
                  onAction={() => setInviteOpen(true)}
                />
              )
            }
            pagination={users.length > 0 ? paginationConfig : undefined}
          />
        </>
      )}

      <InviteUserModal open={inviteOpen} onClose={() => setInviteOpen(false)} />
    </div>
  );
}
