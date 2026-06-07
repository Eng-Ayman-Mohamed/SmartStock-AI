import { type RouteObject } from 'react-router-dom';
import Layout from '../shared/components/Layout';
import DashboardPage from '../features/dashboard/pages/DashboardPage';
import InventoryPage from '../features/inventory/pages/InventoryPage';
import ForecastingPage from '../features/forecasting/pages/ForecastingPage';
import PurchasingPage from '../features/purchasing/pages/PurchasingPage';
import AIAssistantPage from '../features/ai-assistant/pages/AIAssistantPage';
import InvoiceScanPage from '../features/invoice-scan/pages/InvoiceScanPage';
import UsersSettingsPage from '../features/users/pages/UsersSettingsPage';
import ProfilePage from '../features/profile/pages/ProfilePage';
import LoginPage from '../features/auth/pages/LoginPage';
import RegisterPage from '../features/auth/pages/RegisterPage';
import ForbiddenPage from '../features/auth/pages/ForbiddenPage';
import ProtectedRoute from '../features/auth/components/ProtectedRoute';
import RedirectIfAuthenticated from '../features/auth/components/RedirectIfAuthenticated';

export const routes: RouteObject[] = [
  {
    element: <RedirectIfAuthenticated />,
    children: [
      { path: 'login', element: <LoginPage /> },
      { path: 'register', element: <RegisterPage /> },
    ],
  },
  { path: 'forbidden', element: <ForbiddenPage /> },
  {
    element: <ProtectedRoute />,
    children: [
      {
        element: <Layout />,
        children: [
          { index: true, element: <DashboardPage /> },
          { path: 'profile', element: <ProfilePage /> },
          { path: 'inventory', element: <InventoryPage /> },
          { path: 'forecasting', element: <ForecastingPage /> },
          { path: 'purchasing', element: <PurchasingPage /> },
          { path: 'ai-assistant', element: <AIAssistantPage /> },
          { path: 'invoice-scan', element: <InvoiceScanPage /> },
        ],
      },
    ],
  },
  {
    element: <ProtectedRoute allowedRoles={['admin']} />,
    children: [
      {
        element: <Layout />,
        children: [{ path: 'settings', element: <UsersSettingsPage /> }],
      },
    ],
  },
];
