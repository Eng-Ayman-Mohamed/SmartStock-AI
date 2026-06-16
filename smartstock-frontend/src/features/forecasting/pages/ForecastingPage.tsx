import { useState, useEffect } from 'react';
import { Bell, RefreshCw, TrendingUp, ChevronLeft, ChevronRight, ChevronsLeft, ChevronsRight } from 'lucide-react';
import { useQueryClient } from '@tanstack/react-query';
import { useForecastDashboard } from '../hooks/useForecastDashboard';
import SkuChart from '../components/SkuChart';
import AlertSidebar from '../components/AlertSidebar';
import { classifyAlert, type AlertInfo } from '../utils/classifyAlert';
import Card from '../../../shared/components/Card';
import Button from '../../../shared/components/Button';
import { usePagination } from '../../../shared/hooks/usePagination';

const PAGE_SIZE = 6;

export default function ForecastingPage() {
  const [page, setPage] = useState(1);
  const [isAlertModalOpen, setIsAlertModalOpen] = useState(false);
  const { data, isLoading, isError } = useForecastDashboard(page, PAGE_SIZE);
  const queryClient = useQueryClient();
  const [dismissed, setDismissed] = useState<Set<string>>(new Set());

  const skus = data?.skus ?? [];
  const allAlertSkus = data?.alerts ?? [];
  const pagination = data?.pagination;

  const alerts: AlertInfo[] = allAlertSkus
    .map(classifyAlert)
    .filter((a): a is AlertInfo => a !== null)
    .filter(a => !dismissed.has(a.sku.id));

  useEffect(() => {
    if (alerts.length === 0) setIsAlertModalOpen(false);
  }, [alerts.length]);

  const totalSkus = pagination?.total ?? 0;
  const paginationControls = usePagination({
    total: totalSkus,
    pageSize: PAGE_SIZE,
    currentPage: page,
  });

  const handleDismiss = (id: string) =>
    setDismissed(prev => new Set([...prev, id]));

  const handleRefresh = () =>
    queryClient.invalidateQueries({ queryKey: ['forecast-dashboard'] });

  return (
    <div className="flex flex-col xl:flex-row gap-6 animate-fadeIn">
      <div className="flex-1 min-w-0 space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-page-heading text-ink">Demand Forecasting</h1>
            <p className="text-body text-ink-muted mt-1">Peek 30 days ahead — AI predicts what you'll need before you need it</p>
          </div>
          <div className="flex items-center gap-2">
            {alerts.length > 0 && (
              <button
                onClick={() => setIsAlertModalOpen(true)}
                className="xl:hidden relative flex items-center justify-center w-9 h-9 rounded-md border border-hairline bg-canvas text-ink-muted hover:bg-canvas-soft hover:text-ink transition-colors"
                aria-label="Open alerts"
              >
                <Bell className="w-4 h-4" />
                <span className="absolute -top-1.5 -right-1.5 flex items-center justify-center w-4.5 h-4.5 rounded-full bg-red-500 text-[10px] font-semibold text-white min-w-[18px] px-1">
                  {alerts.length}
                </span>
              </button>
            )}
            <Button variant="primary" size="md" onClick={handleRefresh}>
              <RefreshCw className="w-4 h-4" /> Refresh
            </Button>
          </div>
        </div>

        {isError && (
          <div className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-body text-red-800">
            Failed to load forecast data from /api/forecasting/dashboard/
          </div>
        )}

        {isLoading ? (
          <div className="grid grid-cols-1 xl:grid-cols-2 gap-5">
            {[1,2,3,4].map(i => (
              <div key={i} className="h-72 rounded-md border border-hairline bg-hairline animate-skeleton" />
            ))}
          </div>
        ) : skus.length === 0 ? (
          <Card>
            <div className="flex flex-col items-center justify-center py-16">
              <TrendingUp className="w-12 h-12 text-ink-faint mb-4" />
              <h3 className="text-card-title text-ink-secondary mb-1">No forecast data</h3>
              <p className="text-body text-ink-muted text-center max-w-[280px]">
                Forecast data will appear here once the AI model completes its initial analysis.
              </p>
            </div>
          </Card>
        ) : (
          <>
            <div className="grid grid-cols-1 xl:grid-cols-2 gap-5">
              {skus.map((sku, i) => (
                <SkuChart key={sku.id} sku={sku} colorIdx={(page - 1) * PAGE_SIZE + i}
                  hasAlert={alerts.some(a => a!.sku.id === sku.id)} />
              ))}
            </div>

            {totalSkus > PAGE_SIZE && (
              <div className="flex flex-col gap-3 border-t border-hairline px-4 py-3 sm:flex-row sm:items-center sm:justify-between">
                <p className="text-caption text-ink-muted">
                  Showing{" "}
                  <span className="tabular-nums text-ink-secondary">
                    {paginationControls.startItem}
                  </span>
                  {" - "}
                  <span className="tabular-nums text-ink-secondary">
                    {paginationControls.endItem}
                  </span>
                  {" of "}
                  <span className="tabular-nums text-ink-secondary">
                    {totalSkus}
                  </span>
                  {" SKUs"}
                </p>
                <div className="flex items-center gap-1" aria-label="Forecast pagination">
                  <Button
                    variant="utility"
                    size="sm"
                    className="h-11 w-11 px-0"
                    onClick={() => setPage(1)}
                    disabled={!paginationControls.hasPrev}
                    aria-label="First page"
                    title="First page"
                  >
                    <ChevronsLeft className="h-5 w-5" />
                  </Button>
                  <Button
                    variant="utility"
                    size="sm"
                    className="h-11 w-11 px-0"
                    onClick={() => setPage((value) => Math.max(1, value - 1))}
                    disabled={!paginationControls.hasPrev}
                    aria-label="Previous page"
                    title="Previous page"
                  >
                    <ChevronLeft className="h-5 w-5" />
                  </Button>
                  {paginationControls.pages.map((pageNumber, index) =>
                    pageNumber === -1 ? (
                      <span
                        key={`gap-${index}`}
                        className="flex h-11 w-11 items-center justify-center text-caption text-ink-faint"
                      >
                        ...
                      </span>
                    ) : (
                      <Button
                        key={pageNumber}
                        variant={pageNumber === page ? 'primary' : 'utility'}
                        size="sm"
                        className="h-11 w-11 px-0 tabular-nums"
                        onClick={() => setPage(pageNumber)}
                        aria-label={`Page ${pageNumber}`}
                        title={`Page ${pageNumber}`}
                      >
                        {pageNumber}
                      </Button>
                    )
                  )}
                  <Button
                    variant="utility"
                    size="sm"
                    className="h-11 w-11 px-0"
                    onClick={() => setPage((value) => Math.min(paginationControls.totalPages, value + 1))}
                    disabled={!paginationControls.hasNext}
                    aria-label="Next page"
                    title="Next page"
                  >
                    <ChevronRight className="h-5 w-5" />
                  </Button>
                  <Button
                    variant="utility"
                    size="sm"
                    className="h-11 w-11 px-0"
                    onClick={() => setPage(paginationControls.totalPages)}
                    disabled={!paginationControls.hasNext}
                    aria-label="Last page"
                    title="Last page"
                  >
                    <ChevronsRight className="h-5 w-5" />
                  </Button>
                </div>
              </div>
            )}
          </>
        )}
      </div>

      <AlertSidebar alerts={alerts} onDismiss={handleDismiss} isModalOpen={isAlertModalOpen} onModalClose={() => setIsAlertModalOpen(false)} />

    </div>
  );
}
