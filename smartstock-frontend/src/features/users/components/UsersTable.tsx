import { useMemo } from 'react';
import { Power } from 'lucide-react';
import DataTable, { type Column, type PaginationConfig } from '../../../shared/components/DataTable';
import Card from '../../../shared/components/Card';
import RoleBadge from './RoleBadge';
import RoleSelect from './RoleSelect';
import type { User } from '../types';
import { useDeactivateUser, useUpdateUserRole } from '../hooks/useUsers';
import { useAuthStore } from '../../../store/authStore';
import { getAvatarColor } from '../../../shared/utils/avatar';
import { useToastStore } from '../../../store/toastStore';

interface UsersTableProps {
  users: User[];
  emptyState?: React.ReactNode;
  pagination?: PaginationConfig;
  sortField?: string;
  sortOrder?: string;
  onSort?: (key: string) => void;
}

function getInitials(name: string): string {
  return name
    .split(' ')
    .map((n) => n[0])
    .join('')
    .toUpperCase()
    .slice(0, 2);
}

function formatDate(iso: string | null): string {
  if (!iso) return '—';
  return new Date(iso).toLocaleDateString(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
}

export default function UsersTable({ users, emptyState, pagination, sortField, sortOrder, onSort }: UsersTableProps) {
  const currentUserId = useAuthStore((s) => s.user?.id);
  const updateRole = useUpdateUserRole();
  const deactivate = useDeactivateUser();
  const addToast = useToastStore((s) => s.addToast);

  const columns: Column<User>[] = useMemo(
    () => [
      {
        key: 'name',
        label: 'User',
        width: '32%',
        sortable: true,
        sortOrder: sortField === 'name' ? (sortOrder as 'asc' | 'desc') : undefined,
        render: (u) => (
          <div className="flex items-center gap-3 min-w-0">
            <div
              className={"w-8 h-8 rounded-full " + getAvatarColor(u.name) + " flex items-center justify-center text-white text-caption font-medium shrink-0"}
              aria-hidden="true"
            >
              {getInitials(u.name)}
            </div>
            <div className="min-w-0">
              <p className="text-body text-ink font-medium truncate">
                {u.name}
                {currentUserId === u.id && (
                  <span className="ml-1.5 text-caption text-ink-faint font-normal">(you)</span>
                )}
              </p>
              <p className="text-caption text-ink-muted truncate">{u.email}</p>
            </div>
          </div>
        ),
      },
      {
        key: 'role',
        label: 'Role',
        width: '20%',
        sortable: true,
        sortOrder: sortField === 'role' ? (sortOrder as 'asc' | 'desc') : undefined,
        render: (u) => (
          <div className="flex items-center gap-2">
            <RoleBadge role={u.role} />
            <RoleSelect
              value={u.role}
              currentUserId={currentUserId}
              selfId={u.id}
              onChange={(role) =>
                updateRole.mutate(
                  { id: u.id, role },
                  {
                    onSuccess: () => addToast('Role updated successfully', 'success'),
                    onError: () => addToast('Failed to update role', 'error'),
                  },
                )
              }
              disabled={updateRole.isPending}
              ariaLabel={`Change role for ${u.name}`}
            />
          </div>
        ),
      },
      {
        key: 'status',
        label: 'Status',
        width: '14%',
        sortable: true,
        sortOrder: sortField === 'status' ? (sortOrder as 'asc' | 'desc') : undefined,
        render: (u) =>
          u.is_active ? (
            <span className="inline-flex items-center gap-1.5 text-caption font-medium text-green-700 dark:text-green-400">
              <span className="w-1.5 h-1.5 rounded-full bg-green-500" aria-hidden="true" />
              Active
            </span>
          ) : (
            <span className="inline-flex items-center gap-1.5 text-caption font-medium text-gray-600 dark:text-ink-muted">
              <span className="w-1.5 h-1.5 rounded-full bg-gray-400 dark:bg-ink-faint" aria-hidden="true" />
              Deactivated
            </span>
          ),
      },
      {
        key: 'joined',
        label: 'Joined',
        width: '18%',
        sortable: true,
        sortOrder: sortField === 'joined' ? (sortOrder as 'asc' | 'desc') : undefined,
        render: (u) => (
          <span className="text-caption text-ink-muted">{formatDate(u.date_joined)}</span>
        ),
      },
    ],
    [currentUserId, updateRole, addToast, sortField, sortOrder],
  );

  function renderActions(u: User) {
    const isSelf = currentUserId === u.id;
    return (
      <button
        type="button"
        onClick={() =>
          deactivate.mutate(u.id, {
            onSuccess: () => addToast('User deactivated successfully', 'success'),
            onError: () => addToast('Failed to deactivate user', 'error'),
          })
        }
        disabled={!u.is_active || isSelf || deactivate.isPending}
        title={isSelf ? "You can't deactivate your own account" : 'Deactivate user'}
        className="inline-flex items-center gap-1 px-2 py-1 rounded text-caption font-medium text-red-600 hover:bg-red-50 dark:hover:bg-red-900/30 disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:bg-transparent"
      >
        <Power className="w-3.5 h-3.5" aria-hidden="true" />
        <span>Deactivate</span>
      </button>
    );
  }

  if (users.length === 0 && emptyState) {
    return <Card>{emptyState}</Card>;
  }

  return (
    <Card noPadding>
      <DataTable
        columns={columns}
        data={users}
        keyExtractor={(u) => String(u.id)}
        caption="Team members"
        pagination={pagination}
        onSort={onSort}
        actionsLabel="Actions"
        renderActions={renderActions}
      />
    </Card>
  );
}
