import { useMemo, useState } from 'react';
import { Users, UserPlus } from 'lucide-react';
import Button from '../../../shared/components/Button';
import EmptyState from '../../../shared/components/EmptyState';
import Skeleton from '../../../shared/components/Skeleton';
import InviteUserModal from '../components/InviteUserModal';
import UsersFilterBar from '../components/UsersFilterBar';
import UsersTable from '../components/UsersTable';
import { useUsers } from '../hooks/useUsers';
import type { StatusFilter } from '../types';

export default function UsersSettingsPage() {
  const { data: users, isLoading, isError, error, refetch } = useUsers();
  const [inviteOpen, setInviteOpen] = useState(false);
  const [query, setQuery] = useState('');
  const [status, setStatus] = useState<StatusFilter>('all');

  const filtered = useMemo(() => {
    if (!users) return [];
    const q = query.trim().toLowerCase();
    return users.filter((u) => {
      const matchesQuery =
        !q || u.email.toLowerCase().includes(q) || u.name.toLowerCase().includes(q);
      const matchesStatus =
        status === 'all' || (status === 'active' ? u.is_active : !u.is_active);
      return matchesQuery && matchesStatus;
    });
  }, [users, query, status]);

  return (
    <div className="space-y-6 animate-fadeIn">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div>
          <h1 className="text-page-heading text-gray-900">Team & permissions</h1>
          <p className="text-body text-gray-600 mt-1">
            Manage who can access SmartStock AI and what they can do.
          </p>
        </div>
        <Button variant="primary" size="md" onClick={() => setInviteOpen(true)}>
          <UserPlus className="w-4 h-4" aria-hidden="true" />
          <span>Invite user</span>
        </Button>
      </div>

      {isLoading ? (
        <div className="bg-white border border-gray-100 rounded-lg p-5 space-y-3">
          <Skeleton className="h-4 w-1/3" />
          <Skeleton className="h-4 w-2/3" />
          <Skeleton className="h-4 w-1/2" />
        </div>
      ) : isError ? (
        <div className="bg-white border border-red-100 rounded-lg p-5">
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
            onQueryChange={setQuery}
            status={status}
            onStatusChange={setStatus}
            totalCount={users?.length ?? 0}
            filteredCount={filtered.length}
          />
          <UsersTable
            users={filtered}
            emptyState={
              users && users.length > 0 ? (
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
          />
        </>
      )}

      <InviteUserModal open={inviteOpen} onClose={() => setInviteOpen(false)} />
    </div>
  );
}
