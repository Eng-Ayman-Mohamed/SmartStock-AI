import { Link } from 'react-router-dom';
import RegisterForm from '../components/RegisterForm';

export default function RegisterPage() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-canvas-soft px-4 py-12">
      <div className="w-full max-w-[400px]">
        <div className="flex flex-col items-center mb-8">
          <Link to="/" className="flex items-center gap-2 mb-2">
            <img src="/smart-48.png" alt="SmartStock AI" className="w-9 h-9 shrink-0" loading="lazy" />
            <span className="text-card-title font-semibold text-ink">SmartStock AI</span>
          </Link>
          <h1 className="text-section-heading font-semibold text-ink">Create your account</h1>
          <p className="mt-1 text-body text-ink-muted">Get started in less than a minute</p>
        </div>

        <div className="bg-canvas rounded-lg border border-hairline shadow-sm p-6 sm:p-8">
          <RegisterForm />
        </div>

        <p className="mt-6 text-center text-caption text-ink-faint">
          Secure session via JWT · Refresh token stored in HttpOnly cookie
        </p>
      </div>
    </div>
  );
}
