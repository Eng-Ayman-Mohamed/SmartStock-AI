import { useMemo } from 'react';
import { Power } from 'lucide-react';
import DataTable, { type Column } from '../../../shared/components/DataTable';
import Card from '../../../shared/components/Card';
import RoleBadge from './RoleBadge';
import RoleSelect from './RoleSelect';
import type { User } from '../types';
import { useDeactivateUser, useUpdateUserRole } from '../hooks/useUsers';
import { useAuthStore } from '../../../store/authStore';

interface UsersTableProps {
  users: User[];
  emptyState?: React.ReactNode;
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

export default function UsersTable({ users, emptyState }: UsersTableProps) {
  const currentUserId = useAuthStore((s) => s.user?.id);
  const updateRole = useUpdateUserRole();
  const deactivate = useDeactivateUser();

  const columns: Column<User>[] = useMemo(
    () => [
      {
        key: 'name',
        label: 'User',
        width: '32%',
        render: (u) => (
          <div className="flex items-center gap-3 min-w-0">
            <div
              className="w-8 h-8 rounded-full bg-brand-600 flex items-center justify-center text-white text-caption font-medium shrink-0"
              aria-hidden="true"
            >
              {getInitials(u.name)}
            </div>
            <div className="min-w-0">
              <p className="text-body text-gray-900 font-medium truncate">
                {u.name}
                {currentUserId === u.id && (
                  <span className="ml-1.5 text-caption text-gray-400 font-normal">(you)</span>
                )}
              </p>
              <p className="text-caption text-gray-600 truncate">{u.email}</p>
            </div>
          </div>
        ),
      },
      {
        key: 'role',
        label: 'Role',
        width: '20%',
        render: (u) => (
          <div className="flex items-center gap-2">
            <RoleBadge role={u.role} />
            <RoleSelect
              value={u.role}
              currentUserId={currentUserId}
              selfId={u.id}
              onChange={(role) => updateRole.mutate({ id: u.id, role })}
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
        render: (u) =>
          u.is_active ? (
            <span className="inline-flex items-center gap-1.5 text-caption font-medium text-green-700">
              <span className="w-1.5 h-1.5 rounded-full bg-green-500" aria-hidden="true" />
              Active
            </span>
          ) : (
            <span className="inline-flex items-center gap-1.5 text-caption font-medium text-gray-500">
              <span className="w-1.5 h-1.5 rounded-full bg-gray-400" aria-hidden="true" />
              Deactivated
            </span>
          ),
      },
      {
        key: 'joined',
        label: 'Joined',
        width: '18%',
        render: (u) => (
          <span className="text-caption text-gray-600">{formatDate(u.date_joined)}</span>
        ),
      },
      {
        key: 'actions',
        label: '',
        align: 'right',
        width: '16%',
        render: (u) => {
          const isSelf = currentUserId === u.id;
          return (
            <button
              type="button"
              onClick={() => deactivate.mutate(u.id)}
              disabled={!u.is_active || isSelf || deactivate.isPending}
              title={isSelf ? "You can't deactivate your own account" : 'Deactivate user'}
              className="inline-flex items-center gap-1 px-2 py-1 rounded text-caption font-medium text-red-600 hover:bg-red-50 disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:bg-transparent"
            >
              <Power className="w-3.5 h-3.5" aria-hidden="true" />
              <span>Deactivate</span>
            </button>
          );
        },
      },
    ],
    [currentUserId, updateRole, deactivate],
  );

  if (users.length === 0 && emptyState) {
    return <Card>{emptyState}</Card>;
  }

  return (
    <Card>
      <DataTable
        columns={columns}
        data={users}
        keyExtractor={(u) => String(u.id)}
        caption="Team members"
      />
    </Card>
  );
}
