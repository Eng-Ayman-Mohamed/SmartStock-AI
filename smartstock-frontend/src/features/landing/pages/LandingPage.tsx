import { useNavigate } from 'react-router-dom';
import { BarChart3, MessageSquare, FileCheck2, ScanText, Mic } from 'lucide-react';
import { useAuthStore } from '../../../store/authStore';
import { getAvatarColor } from '../../../shared/utils/avatar';
import ThemeToggle from '../../../shared/components/ThemeToggle';

function getInitials(name: string): string {
  return name
    .split(' ')
    .map((n) => n[0])
    .join('')
    .toUpperCase()
    .slice(0, 2);
}

const FEATURES = [
  {
    Icon: BarChart3,
    title: 'Demand forecasting',
    body: 'Predict demand and prevent stockouts early.',
  },
  {
    Icon: MessageSquare,
    title: 'Ask in plain English',
    body: 'Query your inventory without complex reports.',
  },
  {
    Icon: FileCheck2,
    title: 'Auto-drafted POs',
    body: 'Prepare purchase orders for quick approval.',
  },
  {
    Icon: ScanText,
    title: 'Invoice scanning',
    body: 'Read supplier invoices automatically.',
  },
  {
    Icon: Mic,
    title: 'Voice commands',
    body: 'Update inventory hands-free.',
  },
];

function Header() {
  const navigate = useNavigate();
  const user = useAuthStore((s) => s.user);

  return (
    <header className="flex items-center justify-between max-w-[920px] mx-auto w-full px-4 sm:px-6 pt-6 pb-1">
      <button
        onClick={() => navigate('/')}
        className="flex items-center gap-2.5 cursor-pointer min-w-0 shrink min-h-[44px]"
        aria-label="SmartStock AI"
      >
        <span className="grid place-items-center w-[26px] h-[26px] rounded-[7px] bg-brand-600 text-white font-bold text-sm leading-none shrink-0">
          S
        </span>
        <span className="text-card-title font-bold text-ink tracking-tight truncate">SmartStock AI</span>
      </button>

      <div className="flex items-center gap-2 sm:gap-3 shrink-0">
        <ThemeToggle />
        {user ? (
          <button
            onClick={() => navigate('/dashboard')}
            className="flex items-center gap-2 rounded-full px-2 py-1.5 hover:bg-canvas transition-colors min-h-[44px]"
          >
            <span className="text-caption font-medium text-ink-secondary hover:text-ink transition-colors">
              Dashboard
            </span>
            <span
              className={`w-6 h-6 rounded-full ${getAvatarColor(user.name)} flex items-center justify-center text-white text-[10px] font-medium`}
            >
              {getInitials(user.name)}
            </span>
          </button>
        ) : (
          <button
            onClick={() => navigate('/login')}
            className="text-caption font-medium text-ink-secondary hover:text-brand-600 transition-colors min-h-[44px] px-2"
          >
            Log in
          </button>
        )}
      </div>
    </header>
  );
}

export default function LandingPage() {
  const navigate = useNavigate();
  const user = useAuthStore((s) => s.user);

  return (
    <div className="min-h-screen flex flex-col bg-canvas-soft text-ink-secondary">
      <Header />

      <main className="flex-1 max-w-[920px] mx-auto w-full px-4 sm:px-6">
        {/* Hero */}
        <section className="pt-[clamp(48px,9vh,92px)] text-center animate-fadeIn">
          <div className="max-w-[680px] mx-auto">
            <p className="text-eyebrow font-semibold text-ink-muted uppercase tracking-widest mb-4">
              AI inventory planning
            </p>
            <h1
              className="font-bold text-ink tracking-tight leading-[1.07] text-[clamp(32px,5.2vw,52px)]"
              style={{ textWrap: 'balance' }}
            >
              Know what you need before you run out.
            </h1>
            <p className="text-body text-ink-secondary leading-relaxed max-w-[52ch] mx-auto mt-5">
              Forecast demand, ask questions in plain English, and approve purchase orders from one
              simple workspace.
            </p>
            <div className="flex flex-wrap items-center justify-center gap-5 mt-8">
              <button
                onClick={() => navigate('/register')}
                className="font-semibold text-white bg-brand-600 hover:bg-brand-500 rounded-full px-6 py-2.5 text-body transition-colors"
              >
                Start for free
              </button>
              {user ? (
                <button
                  onClick={() => navigate('/dashboard')}
                  className="text-body font-medium text-ink-secondary hover:text-brand-600 transition-colors min-h-[44px] px-3"
                >
                  Go to dashboard
                </button>
              ) : (
                <button
                  onClick={() => navigate('/login')}
                  className="text-body font-medium text-ink-secondary hover:text-brand-600 transition-colors min-h-[44px] px-3"
                >
                  Log in
                </button>
              )}
            </div>
          </div>
        </section>

        {/* Problem / Solution */}
        <section className="max-w-[800px] mx-auto mt-[clamp(44px,7vw,68px)]">
          <div className="grid grid-cols-1 sm:grid-cols-2 divide-y sm:divide-y-0 sm:divide-x divide-hairline bg-canvas border border-hairline rounded-2xl overflow-hidden">
            <article className="p-6 sm:p-7">
              <span className="block text-eyebrow font-semibold uppercase tracking-widest text-ink-muted mb-3">
                The problem
              </span>
              <p className="text-caption text-ink-muted leading-relaxed">
                Warehouse teams react too late when stock is low, invoices pile up, and purchase
                orders take manual work.
              </p>
            </article>
            <article className="p-6 sm:p-7">
              <span className="block text-eyebrow font-semibold uppercase tracking-widest text-brand-600 mb-3">
                The solution
              </span>
              <p className="text-caption font-medium text-ink leading-relaxed">
                SmartStock AI predicts demand, answers inventory questions, and prepares purchase
                orders for approval.
              </p>
            </article>
          </div>
        </section>

        {/* Features */}
        <section className="mt-[clamp(48px,8vw,76px)] pt-[clamp(36px,5vw,44px)] border-t border-hairline">
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-x-7 gap-y-8">
            {FEATURES.map(({ Icon, title, body }) => (
              <article key={title}>
                <Icon size={22} strokeWidth={1.7} className="text-ink-muted mb-3.5" />
                <h2 className="text-card-title font-semibold text-ink mb-1.5 leading-snug">
                  {title}
                </h2>
                <p className="text-caption text-ink-muted leading-relaxed">{body}</p>
              </article>
            ))}
          </div>
        </section>

        {/* Final CTA */}
        <section className="max-w-[760px] mx-auto mt-[clamp(48px,8vw,76px)] text-center bg-brand-50 dark:bg-brand-950/30 border border-hairline rounded-[18px] px-6 sm:px-10 py-[clamp(34px,6vw,48px)]">
          <h2 className="font-bold text-ink tracking-tight leading-tight text-[clamp(22px,3.4vw,28px)] mb-5">
            Ready to optimize your stock?
          </h2>
          <button
            onClick={() => navigate('/register')}
            className="font-semibold text-white bg-brand-600 hover:bg-brand-500 rounded-full px-6 py-2.5 text-body transition-colors"
          >
            Start for free
          </button>
        </section>
      </main>

      <footer className="max-w-[920px] mx-auto w-full px-4 sm:px-6 mt-[clamp(40px,6vw,60px)] pt-6 pb-11">
        <p className="text-caption text-ink-muted">© {new Date().getFullYear()} SmartStock AI</p>
      </footer>
    </div>
  );
}
