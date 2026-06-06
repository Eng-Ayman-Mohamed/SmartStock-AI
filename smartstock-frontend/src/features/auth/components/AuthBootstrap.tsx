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
        className="min-h-screen flex items-center justify-center bg-gray-50"
        role="status"
        aria-live="polite"
        aria-label="Loading application"
      >
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-md bg-brand-600 flex items-center justify-center text-white text-body font-semibold">
            S
          </div>
          <span className="text-body text-gray-600">Loading SmartStock AI…</span>
        </div>
      </div>
    );
  }

  return <>{children}</>;
}
