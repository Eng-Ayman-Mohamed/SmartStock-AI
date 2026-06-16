import { useState } from 'react';
import { Bell, X } from 'lucide-react';
import AlertBanner from './AlertBanner';
import type { AlertInfo } from '../utils/classifyAlert';

interface AlertSidebarProps {
  alerts: AlertInfo[];
  onDismiss: (id: string) => void;
}

export default function AlertSidebar({ alerts, onDismiss }: AlertSidebarProps) {
  const [isCollapsed, setIsCollapsed] = useState(false);

  const criticalCount = alerts.filter(a => a.severity === 'critical').length;
  const warningCount = alerts.filter(a => a.severity === 'warning').length;

  return (
    <>
      <div
        className={`
          hidden xl:block shrink-0 transition-all duration-300 ease-in-out
          ${isCollapsed ? 'w-12' : 'w-80'}
        `}
      >
        <div className="sticky top-14 self-start overflow-hidden rounded-lg border border-hairline bg-canvas shadow-soft animate-slideLeft">
          {isCollapsed ? (
            <button
              onClick={() => setIsCollapsed(false)}
              className="flex flex-col items-center w-full py-4 hover:bg-canvas-soft transition-colors group"
              aria-label="Expand alerts panel"
            >
              <div className="relative">
                <Bell className="w-5 h-5 text-ink-muted group-hover:text-ink transition-colors" />
                {alerts.length > 0 && (
                  <span className="absolute -top-1.5 -right-1.5 flex items-center justify-center w-4 h-4 rounded-full bg-red-500 text-[10px] font-semibold text-white">
                    {alerts.length}
                  </span>
                )}
              </div>
            </button>
          ) : (
            <div>
              <div className="flex items-center justify-between px-5 pt-5 pb-3 border-b border-hairline">
                <div>
                  <h3 className="text-card-title text-ink">Alerts</h3>
                  <p className="text-caption text-ink-muted mt-0.5">
                    {criticalCount > 0 && (
                      <span className="text-red-600 font-medium">{criticalCount} critical</span>
                    )}
                    {criticalCount > 0 && warningCount > 0 && <span className="text-ink-faint"> · </span>}
                    {warningCount > 0 && (
                      <span className="text-orange-600 font-medium">{warningCount} warning</span>
                    )}
                    {criticalCount === 0 && warningCount === 0 && (
                      <span className="text-green-600">All clear</span>
                    )}
                  </p>
                </div>
                <button
                  onClick={() => setIsCollapsed(true)}
                  className="shrink-0 p-1 rounded hover:bg-hairline transition-colors"
                  aria-label="Collapse alerts panel"
                >
                  <X className="w-4 h-4 text-ink-muted" />
                </button>
              </div>

              <div className="p-3 space-y-2 max-h-[calc(100vh-220px)] overflow-y-auto">
                {alerts.sort((a) => (a.severity === 'critical' ? -1 : 1)).map(alert => (
                  <AlertBanner key={alert.sku.id} alert={alert} onDismiss={onDismiss} />
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      <div className="xl:hidden">
        {alerts.length > 0 && (
          <div className="rounded-lg border border-hairline bg-canvas">
            <div className="flex items-center justify-between px-5 pt-5 pb-3 border-b border-hairline">
              <div>
                <h3 className="text-card-title text-ink">Alerts</h3>
                <p className="text-caption text-ink-muted mt-0.5">
                  {criticalCount > 0 && (
                    <span className="text-red-600 font-medium">{criticalCount} critical</span>
                  )}
                  {criticalCount > 0 && warningCount > 0 && <span className="text-ink-faint"> · </span>}
                  {warningCount > 0 && (
                    <span className="text-orange-600 font-medium">{warningCount} warning</span>
                  )}
                  {criticalCount === 0 && warningCount === 0 && (
                    <span className="text-green-600">All clear</span>
                  )}
                </p>
              </div>
              <Bell className="w-4 h-4 text-ink-muted" />
            </div>
            <div className="p-4 space-y-2">
              {alerts.sort((a) => (a.severity === 'critical' ? -1 : 1)).map(alert => (
                <AlertBanner key={alert.sku.id} alert={alert} onDismiss={onDismiss} />
              ))}
            </div>
          </div>
        )}
      </div>
    </>
  );
}
