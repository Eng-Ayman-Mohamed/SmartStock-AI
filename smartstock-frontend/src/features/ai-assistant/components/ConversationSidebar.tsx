import { useMemo } from 'react';
import { MessageSquarePlus, Trash2, MessageCircle } from 'lucide-react';
import type { Conversation } from '../types';

interface ConversationSidebarProps {
  conversations: Conversation[];
  activeId: string | null;
  onSelect: (id: string) => void;
  onNew: () => void;
  onDelete: (id: string) => void;
  isLoading: boolean;
}

function getDateGroup(dateStr: string): string {
  const date = new Date(dateStr);
  const now = new Date();
  const startOfToday = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const startOfYesterday = new Date(startOfToday);
  startOfYesterday.setDate(startOfYesterday.getDate() - 1);
  const startOfWeek = new Date(startOfToday);
  startOfWeek.setDate(startOfWeek.getDate() - 7);

  if (date >= startOfToday) return 'Today';
  if (date >= startOfYesterday) return 'Yesterday';
  if (date >= startOfWeek) return 'Previous 7 days';
  return 'Older';
}

function formatRelativeDate(dateStr: string): string {
  const date = new Date(dateStr);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / (1000 * 60));
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60));

  if (diffMins < 1) return 'Just now';
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  return date.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
}

interface GroupedConversations {
  label: string;
  items: Conversation[];
}

function groupConversations(conversations: Conversation[]): GroupedConversations[] {
  const groups: Record<string, Conversation[]> = {};
  const groupOrder = ['Today', 'Yesterday', 'Previous 7 days', 'Older'];

  for (const conv of conversations) {
    const group = getDateGroup(conv.updated_at);
    if (!groups[group]) groups[group] = [];
    groups[group].push(conv);
  }

  return groupOrder
    .filter((label) => groups[label]?.length)
    .map((label) => ({ label, items: groups[label] }));
}

export default function ConversationSidebar({
  conversations,
  activeId,
  onSelect,
  onNew,
  onDelete,
  isLoading,
}: ConversationSidebarProps) {
  const grouped = useMemo(() => groupConversations(conversations), [conversations]);

  const handleDelete = (id: string) => {
    if (window.confirm('Delete this conversation?')) {
      onDelete(id);
    }
  };

  return (
    <div className="flex flex-col h-full bg-canvas border-r border-hairline">
      <div className="p-3 border-b border-hairline">
        <button
          onClick={onNew}
          disabled={isLoading}
          className="flex items-center justify-center gap-2 w-full px-3 py-2 rounded-lg bg-brand-600 text-white text-body font-medium hover:bg-brand-700 active:bg-brand-800 transition-colors disabled:opacity-50 shadow-sm"
        >
          <MessageSquarePlus className="w-4 h-4" />
          New Chat
        </button>
      </div>

      <div className="flex-1 overflow-y-auto px-2 py-2 space-y-4">
        {grouped.map((group) => (
          <div key={group.label}>
            <p className="px-2 py-1 text-eyebrow uppercase text-ink-faint tracking-wider">
              {group.label}
            </p>
            <div className="space-y-0.5">
              {group.items.map((conv) => (
                <div
                  key={conv.id}
                  className={`group relative flex items-center gap-2.5 px-2.5 py-2 rounded-lg cursor-pointer transition-all duration-150 ${
                    activeId === conv.id
                      ? 'bg-brand-50 dark:bg-brand-900/20 border-l-2 border-l-brand-600 border border-brand-200/60 dark:border-brand-800/60'
                      : 'border-l-2 border-l-transparent hover:bg-canvas-soft border border-transparent'
                  }`}
                  onClick={() => onSelect(conv.id)}
                >
                  <div
                    className={`flex items-center justify-center w-7 h-7 rounded-md shrink-0 ${
                      activeId === conv.id
                        ? 'bg-brand-100 dark:bg-brand-900/40'
                        : 'bg-canvas-soft'
                    }`}
                  >
                    <MessageCircle
                      className={`w-3.5 h-3.5 ${
                        activeId === conv.id
                          ? 'text-brand-600'
                          : 'text-ink-faint'
                      }`}
                    />
                  </div>

                  <div className="flex-1 min-w-0">
                        <p
                          className={`text-sm truncate leading-snug ${
                            activeId === conv.id ? 'text-ink font-medium' : 'text-ink'
                          }`}
                        >
                          {conv.title}
                        </p>
                        <p className="text-xs text-ink-faint mt-0.5">
                          {formatRelativeDate(conv.updated_at)}
                          {conv.message_count != null && conv.message_count > 0 && (
                            <> · {conv.message_count} msg{conv.message_count !== 1 ? 's' : ''}</>
                          )}
                        </p>
                  </div>

                  <div className="hidden group-hover:flex items-center gap-0.5 shrink-0">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleDelete(conv.id);
                        }}
                        className="p-1 rounded text-ink-faint hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors"
                        title="Delete"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                </div>
              ))}
            </div>
          </div>
        ))}

        {conversations.length === 0 && !isLoading && (
          <div className="flex flex-col items-center justify-center py-12 px-4">
            <div className="flex items-center justify-center w-10 h-10 rounded-full bg-canvas-soft mb-3">
              <MessageCircle className="w-5 h-5 text-ink-faint" />
            </div>
            <p className="text-sm text-ink-muted text-center">
              No conversations yet
            </p>
            <p className="text-xs text-ink-faint text-center mt-1">
              Start a new chat to begin
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
