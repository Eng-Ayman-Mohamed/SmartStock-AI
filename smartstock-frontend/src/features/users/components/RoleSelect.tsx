import { Check, ChevronDown } from 'lucide-react';
import { useState, useRef, useEffect } from 'react';
import type { Role } from '../types';
import { ROLE_META } from './RoleBadge';

interface RoleSelectProps {
  value: Role;
  onChange: (role: Role) => void;
  disabled?: boolean;
  excludeSelf?: boolean;
  currentUserId?: number;
  selfId?: number;
  ariaLabel?: string;
}

const ROLES: Role[] = ['viewer', 'manager', 'admin'];

export default function RoleSelect({
  value,
  onChange,
  disabled = false,
  selfId,
  currentUserId,
  ariaLabel = 'Change role',
}: RoleSelectProps) {
  const [open, setOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    function onDocClick(e: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener('mousedown', onDocClick);
    return () => document.removeEventListener('mousedown', onDocClick);
  }, [open]);

  const isSelf = currentUserId !== undefined && selfId === currentUserId;

  return (
    <div className="relative inline-block" ref={containerRef}>
      <button
        type="button"
        onClick={() => !disabled && setOpen((o) => !o)}
        disabled={disabled}
        aria-haspopup="listbox"
        aria-expanded={open}
        aria-label={ariaLabel}
        className="inline-flex items-center gap-1.5 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        <span className="sr-only">Current role: {ROLE_META[value].label}</span>
        <ChevronDown
          className={`w-3 h-3 text-gray-400 transition-transform ${open ? 'rotate-180' : ''}`}
          aria-hidden="true"
        />
      </button>
      {open && (
        <ul
          role="listbox"
          className="absolute right-0 z-20 mt-1 w-44 rounded-md border border-gray-100 bg-white shadow-lg py-1"
        >
          {ROLES.map((role) => {
            const isSelected = role === value;
            const meta = ROLE_META[role];
            const isDisabled = isSelf && role !== 'admin';
            return (
              <li key={role}>
                <button
                  type="button"
                  role="option"
                  aria-selected={isSelected}
                  disabled={isDisabled}
                  onClick={() => {
                    onChange(role);
                    setOpen(false);
                  }}
                  className={`w-full flex items-center justify-between gap-2 px-3 py-2 text-caption text-left text-gray-900 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed ${
                    isSelected ? 'bg-gray-50' : ''
                  }`}
                >
                  <span className="capitalize">{meta.label}</span>
                  {isSelected && <Check className="w-3.5 h-3.5 text-brand-600" aria-hidden="true" />}
                  {isDisabled && (
                    <span className="text-caption text-gray-400">can't demote self</span>
                  )}
                </button>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
