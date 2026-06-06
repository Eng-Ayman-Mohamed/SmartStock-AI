import { type RouteObject } from 'react-router-dom';
import Layout from '../shared/components/Layout';
import DashboardPage from '../features/dashboard/pages/DashboardPage';
import InventoryPage from '../features/inventory/pages/InventoryPage';
import ForecastingPage from '../features/forecasting/pages/ForecastingPage';
import PurchasingPage from '../features/purchasing/pages/PurchasingPage';
import AIAssistantPage from '../features/ai-assistant/pages/AIAssistantPage';
import InvoiceScanPage from '../features/invoice-scan/pages/InvoiceScanPage';
import SettingsPage from '../features/settings/pages/SettingsPage';

export const routes: RouteObject[] = [
  {
    element: <Layout />,
    children: [
      { index: true, element: <DashboardPage /> },
      { path: 'inventory', element: <InventoryPage /> },
      { path: 'forecasting', element: <ForecastingPage /> },
      { path: 'purchasing', element: <PurchasingPage /> },
      { path: 'ai-assistant', element: <AIAssistantPage /> },
      { path: 'invoice-scan', element: <InvoiceScanPage /> },
      { path: 'settings', element: <SettingsPage /> },
    ],
  },
];
