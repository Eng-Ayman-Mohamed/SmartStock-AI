import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  BarChart3,
  MessageSquare,
  FileCheck2,
  ScanText,
  Mic,
  AlertCircle,
  CheckCircle,
} from "lucide-react";
import { useAuthStore } from "../../../store/authStore";
import ThemeToggle from "../../../shared/components/ThemeToggle";
import Button from "../../../shared/components/Button";

const FEATURES = [
  {
    Icon: BarChart3,
    title: "Demand forecasting",
    body: "Predict demand patterns and prevent stockouts before they happen. Get AI-powered recommendations tailored to your business.",
    isAI: true,
  },
  {
    Icon: MessageSquare,
    title: "Ask in plain English",
    body: "Query your inventory using natural language. No complex reports or filters needed — just ask and get instant answers.",
    isAI: true,
  },
  {
    Icon: FileCheck2,
    title: "Auto-drafted POs",
    body: "Automatically prepare purchase orders based on forecasted demand. Review and approve in one click.",
    isAI: false,
  },
  {
    Icon: ScanText,
    title: "Invoice scanning",
    body: "Upload supplier invoices and extract key data automatically. Eliminate manual data entry and reduce errors.",
    isAI: false,
  },
  {
    Icon: Mic,
    title: "Voice commands",
    body: "Update inventory hands-free using voice commands. Perfect for busy warehouse environments.",
    isAI: false,
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
      { threshold: 0 },
    );
    observer.observe(sentinel);
    return () => observer.disconnect();
  }, []);

  return (
    <>
      <div ref={sentinelRef} className="h-0" aria-hidden="true" />
      <header
        className={`flex justify-center w-full px-4 sm:px-6 pt-6 pb-1 transition-all duration-200 ${
          isScrolled
            ? "sticky top-0 z-50 bg-canvas/80 backdrop-blur-md border-b border-hairline py-4"
            : ""
        }`}
      >
        <div className="flex items-center justify-between w-full max-w-[1120px]">
          <div className="flex items-center gap-6 min-w-0">
            <button
              onClick={() => navigate("/")}
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
                onClick={() => navigate("/dashboard")}
              >
                Dashboard
              </Button>
            ) : (
              <>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => navigate("/login")}
                >
                  Log in
                </Button>
                <Button
                  variant="primary"
                  size="sm"
                  onClick={() => navigate("/register")}
                >
                  Start for free
                </Button>
              </>
            )}
          </div>
        </div>
      </header>
    </>
  );
}

export default function LandingPage() {
  const navigate = useNavigate();
  const user = useAuthStore((s) => s.user);

  const featuresRef = useRef<HTMLDivElement>(null);

  // Landing page doesn't use Layout, so body overflow:hidden blocks scroll
  useEffect(() => {
    document.body.style.overflow = "auto";
    return () => {
      document.body.style.overflow = "";
    };
  }, []);

  // Staggered scroll reveal for feature cards
  useEffect(() => {
    const container = featuresRef.current;
    if (!container) return;

    const cards = container.querySelectorAll("article");
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.remove("opacity-0");
            entry.target.classList.add("animate-fadeIn");
            observer.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.1 },
    );

    cards.forEach((card, i) => {
      card.classList.add("opacity-0");
      (card as HTMLElement).style.transitionDelay = `${i * 80}ms`;
      observer.observe(card);
    });

    return () => observer.disconnect();
  }, []);

  return (
    <div className="min-h-screen flex flex-col bg-canvas-soft text-ink-secondary">
      <Header />

      <main className="flex-1 max-w-[920px] mx-auto w-full px-4 sm:px-6">
        {/* Hero */}
        <section className="relative pt-[clamp(48px,9vh,92px)] text-center">
          {/* Gradient background */}
          <div
            className="absolute inset-0 bg-gradient-to-b from-brand-50/50 to-transparent pointer-events-none -z-10 dark:from-brand-950/20"
            aria-hidden="true"
          />

          <div className="max-w-[680px] mx-auto">
            {/* Eyebrow with purple dot */}
            <p
              className="text-eyebrow font-semibold text-ink-muted uppercase mb-4 flex items-center justify-center gap-2 animate-fadeIn"
              style={{ animationDelay: "0ms" }}
            >
              <span
                className="w-1.5 h-1.5 rounded-full bg-purple-600"
                aria-hidden="true"
              />
              AI inventory planning
            </p>

            {/* Larger headline */}
            <h1
              className="font-bold text-ink tracking-tight leading-[1.07] text-[clamp(36px,6vw,56px)] animate-fadeIn"
              style={{ textWrap: "balance", animationDelay: "150ms" }}
            >
              Know what you need before you run out.
            </h1>

            {/* Enhanced subtitle */}
            <p
              className="text-body text-ink-secondary leading-relaxed max-w-[52ch] mx-auto mt-5 animate-fadeIn"
              style={{ animationDelay: "300ms" }}
            >
              Forecast demand, ask questions in plain English, and approve
              purchase orders from one simple workspace.
            </p>

            {/* CTAs */}
            <div
              className="flex flex-wrap items-center justify-center gap-5 mt-8 animate-fadeIn"
              style={{ animationDelay: "450ms" }}
            >
              <Button
                variant="primary"
                size="lg"
                onClick={() => navigate("/register")}
              >
                Start for free
              </Button>
              {user ? (
                <Button
                  variant="ghost"
                  size="lg"
                  onClick={() => navigate("/dashboard")}
                >
                  Go to dashboard
                </Button>
              ) : (
                <Button
                  variant="ghost"
                  size="lg"
                  onClick={() => navigate("/login")}
                >
                  Log in
                </Button>
              )}
            </div>

            {/* Trust badge */}
            <p
              className="text-caption text-ink-muted mt-5 animate-fadeIn"
              style={{ animationDelay: "600ms" }}
            >
              Free plan available · No credit card required
            </p>
          </div>
        </section>

        {/* Problem / Solution */}
        <section className="max-w-[800px] mx-auto mt-[clamp(44px,7vw,68px)]">
          <div className="grid grid-cols-1 sm:grid-cols-2 divide-y sm:divide-y-0 sm:divide-x divide-hairline bg-canvas border border-hairline rounded-2xl overflow-hidden">
            <article className="p-6 sm:p-7">
              <div className="flex items-center gap-2 mb-3">
                <AlertCircle
                  size={16}
                  strokeWidth={1.7}
                  className="text-red-600 dark:text-red-400"
                  aria-hidden="true"
                />
                <span className="text-eyebrow font-semibold uppercase tracking-widest text-red-600 dark:text-red-400">
                  The problem
                </span>
              </div>
              <p className="text-caption text-ink-muted leading-relaxed">
                Warehouse teams react too late when stock is low, invoices pile
                up, and purchase orders take manual work.
              </p>
            </article>
            <article className="p-6 sm:p-7 sm:border-l-2 sm:border-brand-200">
              <div className="flex items-center gap-2 mb-3">
                <CheckCircle
                  size={16}
                  strokeWidth={1.7}
                  className="text-green-600 dark:text-green-400"
                  aria-hidden="true"
                />
                <span className="text-eyebrow font-semibold uppercase tracking-widest text-green-600 dark:text-green-400">
                  The solution
                </span>
              </div>
              <p className="text-caption font-medium text-ink leading-relaxed">
                SmartStock AI predicts demand, answers inventory questions, and
                prepares purchase orders for approval.
              </p>
            </article>
          </div>
        </section>

        {/* Features */}
        <section
          id="features"
          className="mt-[clamp(48px,8vw,76px)] pt-[clamp(36px,5vw,44px)] border-t border-hairline"
        >
          <h2 className="text-section-heading font-semibold text-ink text-center mb-10">
            Everything you need to stay ahead
          </h2>
          <div
            ref={featuresRef}
            className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4"
          >
            {FEATURES.map(({ Icon, title, body, isAI }) => (
              <article
                key={title}
                className="rounded-xl p-4 transition-all duration-200 hover:bg-canvas hover:shadow-soft hover:-translate-y-0.5 dark:hover:bg-canvas"
              >
                <Icon
                  size={22}
                  strokeWidth={1.7}
                  className={`mb-3.5 ${isAI ? "text-purple-600 dark:text-purple-400" : "text-ink-muted"}`}
                />
                <h3 className="text-card-title font-semibold text-ink mb-1.5 leading-snug">
                  {title}
                </h3>
                <p className="text-caption text-ink-muted leading-relaxed">
                  {body}
                </p>
              </article>
            ))}
          </div>
        </section>

        {/* Final CTA */}
        <section className="max-w-[760px] mx-auto mt-[clamp(48px,8vw,76px)] text-center bg-gradient-to-br from-brand-50 to-purple-50/50 dark:from-brand-950/30 dark:to-purple-950/20 border border-hairline rounded-[18px] px-6 sm:px-10 py-[clamp(34px,6vw,48px)]">
          <h2 className="font-bold text-ink tracking-tight leading-tight text-[clamp(22px,3.4vw,28px)] mb-3">
            Ready to optimize your stock?
          </h2>
          <p className="text-caption text-ink-muted mb-6">
            Join teams already saving hours every week
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <Button
              variant="primary"
              size="lg"
              onClick={() => navigate("/register")}
            >
              Start for free
            </Button>
            <Button variant="ghost" size="lg">
              Schedule a demo
            </Button>
          </div>
        </section>
      </main>

      <footer className="w-full px-4 sm:px-6 mt-[clamp(40px,6vw,60px)] pt-8 pb-8 border-t border-hairline">
        <div className="max-w-[1120px] mx-auto">
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-8">
            {/* Product column */}
            <nav aria-label="Product">
              <h4 className="text-card-title font-semibold text-ink mb-3">
                Product
              </h4>
              <ul className="space-y-2">
                <li>
                  <a
                    href="#features"
                    className="text-caption text-ink-muted hover:text-brand-600 transition-colors"
                  >
                    Features
                  </a>
                </li>
                <li>
                  <a
                    href="#"
                    className="text-caption text-ink-muted hover:text-brand-600 transition-colors"
                  >
                    Pricing
                  </a>
                </li>
                <li>
                  <a
                    href="#"
                    className="text-caption text-ink-muted hover:text-brand-600 transition-colors"
                  >
                    Changelog
                  </a>
                </li>
                <li>
                  <a
                    href="#"
                    className="text-caption text-ink-muted hover:text-brand-600 transition-colors"
                  >
                    API
                  </a>
                </li>
              </ul>
            </nav>

            {/* Company column */}
            <nav aria-label="Company">
              <h4 className="text-card-title font-semibold text-ink mb-3">
                Company
              </h4>
              <ul className="space-y-2">
                <li>
                  <a
                    href="#"
                    className="text-caption text-ink-muted hover:text-brand-600 transition-colors"
                  >
                    About
                  </a>
                </li>
                <li>
                  <a
                    href="#"
                    className="text-caption text-ink-muted hover:text-brand-600 transition-colors"
                  >
                    Blog
                  </a>
                </li>
                <li>
                  <a
                    href="#"
                    className="text-caption text-ink-muted hover:text-brand-600 transition-colors"
                  >
                    Careers
                  </a>
                </li>
                <li>
                  <a
                    href="#"
                    className="text-caption text-ink-muted hover:text-brand-600 transition-colors"
                  >
                    Contact
                  </a>
                </li>
              </ul>
            </nav>

            {/* Resources column */}
            <nav aria-label="Resources">
              <h4 className="text-card-title font-semibold text-ink mb-3">
                Resources
              </h4>
              <ul className="space-y-2">
                <li>
                  <a
                    href="#"
                    className="text-caption text-ink-muted hover:text-brand-600 transition-colors"
                  >
                    Documentation
                  </a>
                </li>
                <li>
                  <a
                    href="#"
                    className="text-caption text-ink-muted hover:text-brand-600 transition-colors"
                  >
                    Help center
                  </a>
                </li>
                <li>
                  <a
                    href="#"
                    className="text-caption text-ink-muted hover:text-brand-600 transition-colors"
                  >
                    Status
                  </a>
                </li>
              </ul>
            </nav>

            {/* Legal column */}
            <nav aria-label="Legal">
              <h4 className="text-card-title font-semibold text-ink mb-3">
                Legal
              </h4>
              <ul className="space-y-2">
                <li>
                  <a
                    href="#"
                    className="text-caption text-ink-muted hover:text-brand-600 transition-colors"
                  >
                    Privacy policy
                  </a>
                </li>
                <li>
                  <a
                    href="#"
                    className="text-caption text-ink-muted hover:text-brand-600 transition-colors"
                  >
                    Terms of service
                  </a>
                </li>
              </ul>
            </nav>
          </div>
        </div>
      </footer>

      {/* Footer bottom bar - full width, sticks to bottom */}
      <div className="sticky bottom-0 w-full px-4 sm:px-6 py-4 border-t border-hairline bg-canvas-soft/80 backdrop-blur-md z-40">
        <div className="max-w-[1120px] mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
          <p className="text-caption text-ink-muted">
            © {new Date().getFullYear()} SmartStock AI
          </p>
          <div className="flex items-center gap-4">
            <a
              href="#"
              className="text-ink-muted hover:text-brand-600 transition-colors"
              aria-label="LinkedIn"
            >
              <svg
                width="18"
                height="18"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="1.7"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <path d="M16 8a6 6 0 0 1 6 6v7h-4v-7a2 2 0 0 0-2-2 2 2 0 0 0-2 2v7h-4v-7a6 6 0 0 1 6-6z" />
                <rect x="2" y="9" width="4" height="12" />
                <circle cx="4" cy="4" r="2" />
              </svg>
            </a>
            <a
              href="https://github.com/Eng-Ayman-Mohamed/SmartStock-AI"
              className="text-ink-muted hover:text-brand-600 transition-colors"
              aria-label="GitHub"
            >
              <svg
                width="18"
                height="18"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="1.7"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <path d="M9 19c-5 1.5-5-2.5-7-3m14 6v-3.87a3.37 3.37 0 0 0-.94-2.61c3.14-.35 6.44-1.54 6.44-7A5.44 5.44 0 0 0 20 4.77 5.07 5.07 0 0 0 19.91 1S18.73.65 16 2.48a13.38 13.38 0 0 0-7 0C6.27.65 5.09 1 5.09 1A5.07 5.07 0 0 0 5 4.77a5.44 5.44 0 0 0-1.5 3.78c0 5.42 3.3 6.61 6.44 7A3.37 3.37 0 0 0 9 18.13V22" />
              </svg>
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}
