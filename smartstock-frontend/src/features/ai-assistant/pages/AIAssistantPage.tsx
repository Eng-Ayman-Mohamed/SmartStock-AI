import ChatPanel from '../components/ChatPanel';

export default function AIAssistantPage() {
  return (
    <div className="flex-1 min-h-0 animate-fadeIn flex flex-col">
      <div className="flex flex-wrap items-center justify-between gap-3 mb-6 shrink-0">
        <div>
          <h1 className="text-page-heading text-ink">AI Assistant</h1>
          <p className="text-body text-ink-muted mt-1 hidden sm:block">Your warehouse brain — ask about stock, forecasts, or suppliers</p>
        </div>
      </div>

      <div className="flex-1 flex flex-col min-h-0">
        <ChatPanel />
      </div>
    </div>
  );
}
