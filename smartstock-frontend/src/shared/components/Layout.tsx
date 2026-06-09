import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';
import Header from './Header';
import ToastContainer from './Toast';

export default function Layout() {
  return (
    <div className="flex min-h-screen bg-canvas-soft">
      <Sidebar />
      <div className="flex-1 min-w-0 flex flex-col">
        <Header />
        <div className="flex justify-center">
          <main className="w-full max-w-[1440px] px-8 py-8">
            <Outlet />
          </main>
        </div>
      </div>
      <ToastContainer />
    </div>
  );
}
