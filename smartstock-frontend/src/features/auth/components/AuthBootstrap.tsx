import { useEffect, useRef } from 'react';
import { useAuthStore } from '../../../store/authStore';

interface AuthBootstrapProps {
  children: React.ReactNode;
}

export default function AuthBootstrap({ children }: AuthBootstrapProps) {
  const bootstrap = useAuthStore((s) => s.bootstrapSession);
  const isBootstrapping = useAuthStore((s) => s.isBootstrapping);
  const startedRef = useRef(false);

  useEffect(() => {
    if (startedRef.current) return;
    startedRef.current = true;
    void bootstrap();
  }, [bootstrap]);

  if (isBootstrapping) {
    return (
      <div
        className="min-h-screen flex items-center justify-center bg-canvas-soft"
        role="status"
        aria-live="polite"
        aria-label="Loading application"
      >
        <div className="flex items-center gap-3">
          <img src="/smart-32.png" alt="SmartStock AI" className="w-8 h-8 shrink-0" loading="lazy" />
          <span className="text-body text-ink-muted">Loading SmartStock AI…</span>
        </div>
      </div>
    );
  }

  return <>{children}</>;
}
