export default function NotificationSkeleton({ count = 1 }: { count?: number }) {
  return (
    <>
      {Array.from({ length: count }).map((_, i) => (
        <div
          key={i}
          className="flex items-start gap-3 px-4 py-3 animate-pulse"
        >
          <div className="mt-0.5 w-5 h-5 rounded bg-canvas-soft" />
          <div className="flex-1 min-w-0 space-y-2">
            <div className="h-4 w-3/4 rounded bg-canvas-soft" />
            <div className="h-3 w-full rounded bg-canvas-soft" />
            <div className="flex items-center gap-2">
              <div className="h-3 w-16 rounded bg-canvas-soft" />
              <div className="h-3 w-20 rounded bg-canvas-soft" />
            </div>
          </div>
        </div>
      ))}
    </>
  );
}
