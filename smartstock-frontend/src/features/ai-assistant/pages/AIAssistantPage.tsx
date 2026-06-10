import { useState, useRef, useEffect } from 'react';
import { Bot, Send, User, Package, AlertTriangle, FileText, TrendingUp } from 'lucide-react';
import Card from '../../../shared/components/Card';

interface Message {
  role: 'user' | 'ai';
  text: string;
}

export default function AIAssistantPage() {
  const [messages, setMessages] = useState<Message[]>([
    { role: 'ai', text: 'Hey there! I\'m keeping an eye on your stock. Ask me about inventory levels, reorder suggestions, or supplier performance.' },
  ]);
  const chatEndRef = useRef<HTMLDivElement>(null);
  const [input, setInput] = useState('');
  const [isThinking, setIsThinking] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = () => {
    if (!input.trim() || isThinking) return;
    const userMsg: Message = { role: 'user', text: input.trim() };
    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setIsThinking(true);
    setTimeout(() => {
      setMessages((prev) => [...prev, {
        role: 'ai',
        text: 'I\'ve analyzed your inventory data. Here\'s what I found: your top 3 slow-moving items this month are the "USB-C Hub" (12 units sold), "Webcam HD" (8 units), and "Monitor Stand" (5 units). Would you like me to suggest reorder adjustments or flag any items for discount?',
      }]);
      setIsThinking(false);
    }, 1500);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="h-[calc(100vh-40px-64px)] animate-fadeIn flex flex-col">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-page-heading text-ink">AI Assistant</h1>
          <p className="text-body text-ink-muted mt-1">Your warehouse brain — ask about stock, forecasts, or suppliers</p>
        </div>
      </div>

      <div className="flex-1 grid grid-cols-1 lg:grid-cols-[3fr_2fr] gap-6 min-h-0">
        <Card noPadding className="flex flex-col overflow-hidden">
          <div className="flex-1 overflow-y-auto p-6 space-y-4" aria-live="polite" aria-label="Chat messages">
            {messages.map((msg, i) => (
              <div key={i} className={`flex gap-3 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
                <div className={`flex items-center justify-center w-7 h-7 rounded-full shrink-0 ${
                  msg.role === 'user' ? 'bg-brand-600' : 'bg-purple-50'
                }`}>
                  {msg.role === 'user' ? (
                    <User className="w-4 h-4 text-white" />
                  ) : (
                    <Bot className="w-4 h-4 text-purple-600" />
                  )}
                </div>
                <div className={`max-w-[80%] ${
                  msg.role === 'user'
                    ? 'bg-brand-600 text-white rounded-lg rounded-br-sm px-4 py-2.5'
                    : 'bg-canvas-soft text-ink rounded-lg rounded-bl-sm px-4 py-2.5'
                }`}>
                  <p className="text-body leading-relaxed">{msg.text}</p>
                </div>
              </div>
            ))}
            {isThinking && (
              <div className="flex gap-3">
                <div className="flex items-center justify-center w-7 h-7 rounded-full bg-purple-50 shrink-0">
                  <Bot className="w-4 h-4 text-purple-600" />
                </div>
                <div className="bg-canvas-soft rounded-lg rounded-bl-sm px-4 py-3">
                  <span className="flex gap-1">
                    <span className="w-1.5 h-1.5 bg-ink-faint rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                    <span className="w-1.5 h-1.5 bg-ink-faint rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                    <span className="w-1.5 h-1.5 bg-ink-faint rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                  </span>
                </div>
              </div>
            )}
            <div ref={chatEndRef} />
          </div>

          <div className="px-6 py-3 border-t border-hairline">
            <div className="flex items-center gap-2">
              <input
                ref={inputRef}
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Ask about your inventory..."
                className="flex-1 h-9 px-4 rounded-full border border-hairline bg-canvas text-body text-ink placeholder:text-ink-faint hover:border-ink-muted focus:border-brand-600 focus:outline-none focus:ring-0 transition-colors"
                aria-label="Ask about your inventory"
                disabled={isThinking}
              />
              <button
                onClick={handleSend}
                disabled={isThinking || !input.trim()}
                className="flex items-center justify-center w-9 h-9 rounded-full bg-brand-600 text-white hover:bg-brand-800 disabled:bg-canvas-soft disabled:text-ink-faint transition-colors shrink-0"
                aria-label="Send message"
              >
                <Send className="w-4 h-4" />
              </button>
            </div>
          </div>
        </Card>

        <div className="space-y-4 overflow-y-auto">
          <Card title="Current Inventory Snapshot">
            <div className="space-y-3">
              {[
                { name: 'Wireless Mouse', stock: 12, threshold: 50, icon: Package },
                { name: 'USB-C Hub 6-in-1', stock: 28, threshold: 60, icon: Package },
                { name: 'Mechanical Keyboard', stock: 15, threshold: 30, icon: Package },
                { name: '27" Monitor Stand', stock: 8, threshold: 20, icon: Package },
                { name: 'Webcam HD', stock: 42, threshold: 35, icon: Package },
              ].map((item) => (
                <div key={item.name} className="flex items-center gap-3 pb-2 border-b border-hairline last:border-0 last:pb-0">
                  <div className={`flex items-center justify-center w-7 h-7 rounded-md shrink-0 ${
                    item.stock < item.threshold ? 'bg-orange-50' : 'bg-green-50'
                  }`}>
                    <item.icon className={`w-4 h-4 ${item.stock < item.threshold ? 'text-orange-600' : 'text-green-600'}`} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-body text-ink truncate">{item.name}</p>
                    <p className="text-caption text-ink-muted tabular-nums">{item.stock} units</p>
                  </div>
                  {item.stock < item.threshold && <AlertTriangle className="w-4 h-4 text-orange-600" />}
                </div>
              ))}
            </div>
          </Card>

          <Card title="Data Sources">
            <div className="space-y-2">
              {[
                { name: 'Inventory DB', status: 'Connected', icon: Package },
                { name: 'Sales Pipeline', status: 'Connected', icon: TrendingUp },
                { name: 'Supplier Catalog', status: 'Synced 2h ago', icon: FileText },
              ].map((src) => (
                <div key={src.name} className="flex items-center gap-2 text-body text-ink-muted">
                  <src.icon className="w-4 h-4 text-ink-faint" />
                  <span className="flex-1">{src.name}</span>
                  <span className="text-caption text-green-600">{src.status}</span>
                </div>
              ))}
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}
