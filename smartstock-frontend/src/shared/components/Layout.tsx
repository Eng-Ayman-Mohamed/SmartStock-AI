import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';
import Header from './Header';
import ToastContainer from './Toast';

export default function Layout() {
  return (
    <div className="flex h-screen bg-canvas-soft">
      <Sidebar />
      <div className="flex-1 min-w-0 flex flex-col h-screen overflow-y-auto">
        <Header />
        <div className="flex justify-center flex-1 min-h-0">
          <main className="w-full max-w-[1440px] px-4 sm:px-6 lg:px-8 py-4 sm:py-6 lg:py-8 flex-1 min-h-0 flex flex-col">
            <Outlet />
          </main>
        </div>
      </div>
      <ToastContainer />
    </div>
  );
}
