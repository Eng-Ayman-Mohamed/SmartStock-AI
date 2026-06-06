import { useLocation } from 'react-router-dom';
import { Bell, Menu } from 'lucide-react';

const pageTitles: Record<string, string> = {
  '/': 'Dashboard',
  '/inventory': 'Inventory',
  '/forecasting': 'Forecasting',
  '/purchasing': 'Purchasing',
  '/ai-assistant': 'AI Assistant',
  '/invoice-scan': 'Invoice Scan',
  '/settings': 'Settings',
};

export default function Header() {
  const location = useLocation();
  const title = pageTitles[location.pathname] || 'SmartStock AI';

  // Get sidebar toggle — we dispatch a custom event so Sidebar can listen
  const handleToggle = () => {
    window.dispatchEvent(new CustomEvent('toggle-sidebar'));
  };

  return (
    <header className="sticky top-0 z-30 flex items-center justify-between h-10 px-4 sm:px-6 border-b-[1px] border-gray-100 bg-white">
      <div className="flex items-center gap-2">
        <button
          onClick={handleToggle}
          className="md:hidden flex items-center justify-center w-7 h-7 rounded-md text-gray-400 hover:text-gray-600 hover:bg-gray-50 transition-colors"
          aria-label="Toggle navigation"
        >
          <Menu className="w-4 h-4" />
        </button>
        <nav aria-label="Breadcrumb">
          <ol className="flex items-center gap-1.5 text-caption text-gray-600">
            <li>SmartStock AI</li>
            <li aria-hidden="true" className="text-gray-300">/</li>
            <li className="text-gray-900 font-medium" aria-current="page">{title}</li>
          </ol>
        </nav>
      </div>

      <div className="flex items-center gap-3">
        <button
          className="relative flex items-center justify-center w-7 h-7 rounded-md text-gray-400 hover:text-gray-600 hover:bg-gray-50 transition-colors"
          aria-label="Notifications"
        >
          <Bell className="w-4 h-4" />
        </button>

        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-full bg-brand-600 flex items-center justify-center text-white text-[11px] font-medium" aria-hidden="true">
            JD
          </div>
          <span className="hidden sm:inline text-caption font-medium text-gray-600">John Doe</span>
          <span className="hidden lg:inline-flex items-center px-1.5 py-0.5 rounded-sm text-caption font-medium bg-brand-50 text-brand-800">
            Manager
          </span>
        </div>
      </div>
    </header>
  );
}
