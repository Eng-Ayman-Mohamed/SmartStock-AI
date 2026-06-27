import { useEffect, useMemo, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { Loader2, CheckCircle2, XCircle } from 'lucide-react';
import { verifyEmail } from '../api';
import Button from '../../../shared/components/Button';

export default function VerifyEmailPage() {
  const [searchParams] = useSearchParams();
  const token = searchParams.get('token');

  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading');
  const [message, setMessage] = useState('');

  const missingToken = useMemo(() => !token, [token]);

  useEffect(() => {
    if (missingToken) return;

    let cancelled = false;
    verifyEmail(token!)
      .then((res) => {
        if (!cancelled) {
          setStatus('success');
          setMessage(res.detail);
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setStatus('error');
          const data = err?.response?.data;
          setMessage(data?.detail || data?.message || 'Verification failed. The link may be invalid or expired.');
        }
      });

    return () => {
      cancelled = true;
    };
  }, [token, missingToken]);

  if (missingToken) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-canvas-soft px-4 py-12">
        <div className="w-full max-w-[400px]">
          <div className="flex flex-col items-center mb-8">
            <Link to="/" className="flex items-center gap-2 mb-2">
              <img src="/smart-48.png" alt="SmartStock AI" className="w-9 h-9 shrink-0" loading="lazy" />
              <span className="text-card-title font-semibold text-ink">SmartStock AI</span>
            </Link>
            <h1 className="text-section-heading font-semibold text-ink">Email Verification</h1>
          </div>
          <div className="bg-canvas rounded-lg border border-hairline shadow-sm p-6 sm:p-8">
            <div className="flex flex-col items-center text-center gap-4">
              <XCircle className="w-10 h-10 text-red-600" />
              <p className="text-body text-ink">No verification link provided.</p>
              <Link to="/login" className="mt-2">
                <Button variant="primary" size="md">Go to Sign in</Button>
              </Link>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-canvas-soft px-4 py-12">
      <div className="w-full max-w-[400px]">
        <div className="flex flex-col items-center mb-8">
          <Link to="/" className="flex items-center gap-2 mb-2">
            <img src="/smart-48.png" alt="SmartStock AI" className="w-9 h-9 shrink-0" loading="lazy" />
            <span className="text-card-title font-semibold text-ink">SmartStock AI</span>
          </Link>
          <h1 className="text-section-heading font-semibold text-ink">Email Verification</h1>
        </div>

        <div className="bg-canvas rounded-lg border border-hairline shadow-sm p-6 sm:p-8">
          <div className="flex flex-col items-center text-center gap-4">
            {status === 'loading' && (
              <>
                <Loader2 className="w-10 h-10 text-brand-600 animate-spin" />
                <p className="text-body text-ink-muted">Verifying your email address...</p>
              </>
            )}

            {status === 'success' && (
              <>
                <CheckCircle2 className="w-10 h-10 text-green-600" />
                <p className="text-body text-ink">{message}</p>
                <Link to="/login" className="mt-2">
                  <Button variant="primary" size="md">Go to Sign in</Button>
                </Link>
              </>
            )}

            {status === 'error' && (
              <>
                <XCircle className="w-10 h-10 text-red-600" />
                <p className="text-body text-ink">{message}</p>
                <p className="text-caption text-ink-muted">
                  Your email may already be verified. Try signing in.
                </p>
                <Link to="/login" className="mt-2">
                  <Button variant="primary" size="md">Go to Sign in</Button>
                </Link>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
