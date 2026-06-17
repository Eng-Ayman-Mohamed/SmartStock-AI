import { useState, useEffect } from 'react';
import { Bell, X } from 'lucide-react';
import AlertBanner from './AlertBanner';
import type { AlertInfo } from '../utils/classifyAlert';

interface AlertSidebarProps {
  alerts: AlertInfo[];
  onDismiss: (id: string) => void;
  isModalOpen: boolean;
  onModalClose: () => void;
}

function SeverityCount({ criticalCount, warningCount }: { criticalCount: number; warningCount: number }) {
  return (
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
  );
}

export default function AlertSidebar({ alerts, onDismiss, isModalOpen, onModalClose }: AlertSidebarProps) {
  const [isCollapsed, setIsCollapsed] = useState(false);

  const criticalCount = alerts.filter(a => a.severity === 'critical').length;
  const warningCount = alerts.filter(a => a.severity === 'warning').length;

  useEffect(() => {
    if (isModalOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
    return () => { document.body.style.overflow = ''; };
  }, [isModalOpen]);

  return (
    <>
      {/* Desktop: sticky sidebar (xl+) */}
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
                  <SeverityCount criticalCount={criticalCount} warningCount={warningCount} />
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
                {[...alerts].sort((a, b) => (a.severity === 'critical' ? -1 : b.severity === 'critical' ? 1 : 0)).map(alert => (
                  <AlertBanner key={alert.sku.id} alert={alert} onDismiss={onDismiss} />
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Mobile/tablet: alert modal overlay (below xl) */}
      {isModalOpen && (
        <div className="xl:hidden fixed inset-0 z-50 flex items-end sm:items-center justify-center bg-black/30 animate-fadeIn">
          <div
            className="w-full sm:max-w-2xl bg-canvas rounded-t-xl sm:rounded-lg animate-slideUp max-h-[80vh] flex flex-col"
            role="dialog"
            aria-modal="true"
            aria-label="Alerts"
          >
            <div className="flex items-center justify-between px-6 pt-6 pb-4 border-b border-hairline shrink-0">
              <div>
                <h3 className="text-card-title text-ink">Alerts</h3>
                <SeverityCount criticalCount={criticalCount} warningCount={warningCount} />
              </div>
              <button
                onClick={onModalClose}
                className="shrink-0 p-1 rounded hover:bg-hairline transition-colors"
                aria-label="Close alerts"
              >
                <X className="w-5 h-5 text-ink-muted" />
              </button>
            </div>

            <div className="p-5 space-y-2 overflow-y-auto">
              {[...alerts].sort((a, b) => (a.severity === 'critical' ? -1 : b.severity === 'critical' ? 1 : 0)).map(alert => (
                <AlertBanner key={alert.sku.id} alert={alert} onDismiss={onDismiss} />
              ))}
            </div>
          </div>

          {/* Backdrop click to close */}
          <button
            onClick={onModalClose}
            className="fixed inset-0 z-[-1]"
            aria-label="Close alerts"
          />
        </div>
      )}
    </>
  );
}
