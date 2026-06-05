import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { QueryClientProvider } from '@tanstack/react-query';
import { queryClient } from './lib/queryClient';
import Layout from './shared/components/Layout';
import DashboardPage from './features/dashboard/pages/DashboardPage';
import InventoryPage from './features/inventory/pages/InventoryPage';
import ForecastingPage from './features/forecasting/pages/ForecastingPage';
import PurchasingPage from './features/purchasing/pages/PurchasingPage';

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route element={<Layout />}>
            <Route path="/" element={<DashboardPage />} />
            <Route path="/inventory" element={<InventoryPage />} />
            <Route path="/forecasting" element={<ForecastingPage />} />
            <Route path="/purchasing" element={<PurchasingPage />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
