import { Link } from 'react-router-dom';
import { ShieldAlert, ArrowLeft } from 'lucide-react';
import Button from '../../../shared/components/Button';

export default function ForbiddenPage() {
  return (
    <div className="min-h-[calc(100vh-72px)] flex items-center justify-center px-4 py-12">
      <div className="w-full max-w-[420px] text-center">
        <div className="flex items-center justify-center w-12 h-12 rounded-full bg-red-50 mx-auto mb-4">
          <ShieldAlert className="w-6 h-6 text-red-600" aria-hidden="true" />
        </div>
        <h1 className="text-section-title font-semibold text-gray-900">Access denied</h1>
        <p className="mt-2 text-body text-gray-600">
          You don't have permission to view this page. Contact your administrator if you think this is a
          mistake.
        </p>
        <div className="mt-6 flex items-center justify-center gap-2">
          <Link to="/">
            <Button variant="primary" size="md">
              <ArrowLeft className="w-4 h-4" aria-hidden="true" />
              <span>Back to dashboard</span>
            </Button>
          </Link>
        </div>
      </div>
    </div>
  );
}
