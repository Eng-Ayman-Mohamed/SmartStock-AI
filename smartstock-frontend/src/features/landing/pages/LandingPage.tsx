import { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { BarChart3, MessageSquare, FileCheck2, ScanText, Mic } from 'lucide-react';
import { useAuthStore } from '../../../store/authStore';
import ThemeToggle from '../../../shared/components/ThemeToggle';
import Button from '../../../shared/components/Button';

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

  const [isScrolled, setIsScrolled] = useState(false);
  const sentinelRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const sentinel = sentinelRef.current;
    if (!sentinel) return;
    const observer = new IntersectionObserver(
      ([entry]) => setIsScrolled(!entry.isIntersecting),
      { threshold: 0 }
    );
    observer.observe(sentinel);
    return () => observer.disconnect();
  }, []);

  return (
    <>
      <div ref={sentinelRef} className="h-0" aria-hidden="true" />
      <header
        className={`flex items-center justify-between max-w-[1120px] mx-auto w-full px-4 sm:px-6 pt-6 pb-1 transition-all duration-200 ${
          isScrolled
            ? 'sticky top-0 z-50 bg-canvas/80 backdrop-blur-md border-b border-hairline py-4'
            : ''
        }`}
      >
        <div className="flex items-center gap-6 min-w-0">
          <button
            onClick={() => navigate('/')}
            className="flex items-center gap-2.5 cursor-pointer min-w-0 shrink min-h-[44px]"
            aria-label="SmartStock AI"
          >
            <img
              src="/smart-32.png"
              alt=""
              className="w-[26px] h-[26px] shrink-0"
              width={26}
              height={26}
            />
            <span className="text-card-title font-bold text-ink tracking-tight truncate">
              SmartStock AI
            </span>
          </button>
          <nav className="hidden sm:flex items-center gap-6">
            <a
              href="#features"
              className="text-caption font-medium text-ink-muted hover:text-ink transition-colors"
            >
              Features
            </a>
          </nav>
        </div>

        <div className="flex items-center gap-2 sm:gap-3 shrink-0">
          <ThemeToggle />
          {user ? (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => navigate('/dashboard')}
            >
              Dashboard
            </Button>
          ) : (
            <>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => navigate('/login')}
              >
                Log in
              </Button>
              <Button
                variant="primary"
                size="sm"
                onClick={() => navigate('/register')}
              >
                Start for free
              </Button>
            </>
          )}
        </div>
      </header>
    </>
  );
}

export default function LandingPage() {
  const navigate = useNavigate();
  const user = useAuthStore((s) => s.user);

  // Landing page doesn't use Layout, so body overflow:hidden blocks scroll
  useEffect(() => {
    document.body.style.overflow = 'auto';
    return () => { document.body.style.overflow = ''; };
  }, []);

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
        <section id="features" className="mt-[clamp(48px,8vw,76px)] pt-[clamp(36px,5vw,44px)] border-t border-hairline">
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
