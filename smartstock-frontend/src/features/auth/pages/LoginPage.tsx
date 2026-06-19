import { Link } from 'react-router-dom';
import { Sparkles } from 'lucide-react';
import LoginForm from '../components/LoginForm';

export default function LoginPage() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-canvas-soft px-4 py-12">
      <div className="w-full max-w-[400px]">
        <div className="flex flex-col items-center mb-8">
          <Link to="/" className="flex items-center gap-2 mb-2">
            <div className="flex items-center justify-center w-9 h-9 rounded-md bg-brand-600">
              <Sparkles className="w-5 h-5 text-white" aria-hidden="true" />
            </div>
            <span className="text-card-title font-semibold text-ink">SmartStock AI</span>
          </Link>
          <h1 className="text-section-heading font-semibold text-ink">Welcome back</h1>
          <p className="mt-1 text-body text-ink-muted">Sign in to your warehouse dashboard</p>
        </div>

        <div className="bg-canvas rounded-lg border border-hairline shadow-sm p-6 sm:p-8">
          <LoginForm />
        </div>

        <p className="mt-6 text-center text-caption text-ink-faint">
          Secure session via JWT · Refresh token stored in HttpOnly cookie
        </p>
      </div>
    </div>
  );
}
