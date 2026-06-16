/* eslint-disable react-refresh/only-export-components */
import { Suspense, lazy } from 'react';
import { type RouteObject } from 'react-router-dom';
import Layout from '../shared/components/Layout';
import ProtectedRoute from '../features/auth/components/ProtectedRoute';
import RedirectIfAuthenticated from '../features/auth/components/RedirectIfAuthenticated';

const DashboardPage = lazy(() => import('../features/dashboard/pages/DashboardPage'));
const InventoryPage = lazy(() => import('../features/inventory/pages/InventoryPage'));
const ForecastingPage = lazy(() => import('../features/forecasting/pages/ForecastingPage'));
const PurchasingPage = lazy(() => import('../features/purchasing/pages/PurchasingPage'));
const AIAssistantPage = lazy(() => import('../features/ai-assistant/pages/AIAssistantPage'));
const InvoiceScanPage = lazy(() => import('../features/invoice-scan/pages/InvoiceScanPage'));
const UsersSettingsPage = lazy(() => import('../features/users/pages/UsersSettingsPage'));
const ProfilePage = lazy(() => import('../features/profile/pages/ProfilePage'));
const LoginPage = lazy(() => import('../features/auth/pages/LoginPage'));
const RegisterPage = lazy(() => import('../features/auth/pages/RegisterPage'));
const ForbiddenPage = lazy(() => import('../features/auth/pages/ForbiddenPage'));
const SuppliersPage = lazy(() => import('../features/purchasing/pages/SuppliersPage').then(m => ({ default: m.SuppliersPage })));

const SuspenseWrapper = ({ children }: { children: React.ReactNode }) => (
  <Suspense fallback={<div className="flex items-center justify-center h-64 text-ink-muted">Loading...</div>}>
    {children}
  </Suspense>
);

export const routes: RouteObject[] = [
  {
    element: <RedirectIfAuthenticated />,
    children: [
      { path: 'login', element: <SuspenseWrapper><LoginPage /></SuspenseWrapper> },
      { path: 'register', element: <SuspenseWrapper><RegisterPage /></SuspenseWrapper> },
    ],
  },
  { path: 'forbidden', element: <SuspenseWrapper><ForbiddenPage /></SuspenseWrapper> },
  {
    element: <ProtectedRoute />,
    children: [
      {
        element: <Layout />,
        children: [
          { index: true, element: <SuspenseWrapper><DashboardPage /></SuspenseWrapper> },
          { path: 'profile', element: <SuspenseWrapper><ProfilePage /></SuspenseWrapper> },
          { path: 'inventory', element: <SuspenseWrapper><InventoryPage /></SuspenseWrapper> },
          { path: 'forecasting', element: <SuspenseWrapper><ForecastingPage /></SuspenseWrapper> },
          { path: 'purchasing', element: <SuspenseWrapper><PurchasingPage /></SuspenseWrapper> },
          { path: 'ai-assistant', element: <SuspenseWrapper><AIAssistantPage /></SuspenseWrapper> },
          { path: 'invoice-scan', element: <SuspenseWrapper><InvoiceScanPage /></SuspenseWrapper> },
          { path: 'suppliers', element: <SuspenseWrapper><SuppliersPage /></SuspenseWrapper> },
        ],
      },
    ],
  },
  {
    element: <ProtectedRoute allowedRoles={['admin']} />,
    children: [
      {
        element: <Layout />,
        children: [{ path: 'settings', element: <SuspenseWrapper><UsersSettingsPage /></SuspenseWrapper> }],
      },
    ],
  },
];
