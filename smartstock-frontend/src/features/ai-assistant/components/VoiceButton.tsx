import { Mic, Square, Loader2 } from 'lucide-react';
import { useVoiceRecorder } from '../hooks/useVoiceRecorder';

interface VoiceButtonProps {
  onTranscript: (text: string) => void;
}

export default function VoiceButton({ onTranscript }: VoiceButtonProps) {
  const { state, error, elapsed, maxDuration, startRecording, stopRecording, isSupported } =
    useVoiceRecorder(onTranscript);

  if (!isSupported) {
    return (
      <div className="relative group">
        <button
          disabled
          className="flex items-center justify-center w-9 h-9 rounded-full bg-canvas-soft text-ink-faint transition-colors cursor-not-allowed"
          aria-label="Voice input not supported"
        >
          <Mic className="w-4 h-4" />
        </button>
        <span className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-2 py-1 text-caption bg-ink text-white rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap pointer-events-none">
          Voice not supported in this browser
        </span>
      </div>
    );
  }

  if (state === 'recording') {
    const remaining = maxDuration - elapsed;
    return (
      <div className="flex items-center gap-1.5">
        <span className="text-caption text-red-600 tabular-nums font-medium" aria-live="polite">
          {remaining}s
        </span>
        <button
          onClick={stopRecording}
          className="flex items-center justify-center w-9 h-9 rounded-full bg-red-500 text-white hover:bg-red-600 transition-colors shrink-0 animate-pulse"
          aria-label="Stop recording"
        >
          <Square className="w-4 h-4" />
        </button>
      </div>
    );
  }

  if (state === 'transcribing') {
    return (
      <button
        disabled
        className="flex items-center justify-center w-9 h-9 rounded-full bg-brand-50 text-brand-600 transition-colors cursor-wait"
        aria-label="Transcribing..."
      >
        <Loader2 className="w-4 h-4 animate-spin" />
      </button>
    );
  }

  return (
    <div className="relative">
      <button
        onClick={startRecording}
        className="flex items-center justify-center w-9 h-9 rounded-full text-ink-muted hover:bg-canvas-soft hover:text-ink transition-colors shrink-0"
        aria-label="Start voice recording"
      >
        <Mic className="w-4 h-4" />
      </button>
      {error && (
        <span className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-2 py-1 text-caption bg-red-50 text-red-600 rounded whitespace-nowrap pointer-events-none">
          {error}
        </span>
      )}
    </div>
  );
}
