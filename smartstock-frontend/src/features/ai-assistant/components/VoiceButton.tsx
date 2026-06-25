import { useEffect } from 'react';
import { Mic, Square, Loader2 } from 'lucide-react';
import { useVoiceRecorder } from '../hooks/useVoiceRecorder';

interface VoiceButtonProps {
  onTranscript: (text: string) => void;
}

function AudioBars({ level }: { level: number }) {
  const bars = [0, 1, 2, 3, 4];
  return (
    <div className="flex items-center gap-[3px] h-5" aria-hidden="true">
      {bars.map((i) => {
        const offset = Math.abs(i - 2) * 0.15;
        const height = Math.max(0.15, Math.min(1, level * 1.8 + offset));
        return (
          <div
            key={i}
            className="w-[3px] rounded-full bg-white transition-transform duration-75"
            style={{ height: '100%', transform: `scaleY(${height})` }}
          />
        );
      })}
    </div>
  );
}

export default function VoiceButton({ onTranscript }: VoiceButtonProps) {
  const { state, error, elapsed, maxDuration, transcript, clearTranscript, audioLevel, startRecording, stopRecording, isSupported } =
    useVoiceRecorder();

  useEffect(() => {
    if (transcript) {
      onTranscript(transcript);
      clearTranscript();
    }
  }, [transcript, onTranscript, clearTranscript]);

  if (!isSupported) {
    return (
      <div className="relative group">
        <button
          disabled
          className="flex items-center justify-center w-11 h-11 min-h-[44px] min-w-[44px] rounded-full bg-canvas-soft text-ink-faint transition-colors cursor-not-allowed"
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
        <AudioBars level={audioLevel} />
        <button
          onClick={stopRecording}
          className="flex items-center justify-center w-11 h-11 min-h-[44px] min-w-[44px] rounded-full bg-red-500 text-white hover:bg-red-600 transition-colors shrink-0 animate-pulse"
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
        className="flex items-center justify-center w-11 h-11 min-h-[44px] min-w-[44px] rounded-full bg-brand-50 text-brand-600 dark:bg-brand-900/30 dark:text-brand-400 transition-colors cursor-wait"
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
        className="flex items-center justify-center w-11 h-11 min-h-[44px] min-w-[44px] rounded-full text-ink-muted hover:bg-canvas-soft hover:text-ink transition-colors shrink-0"
        aria-label="Start voice recording"
        aria-describedby={error ? 'voice-error' : undefined}
      >
        <Mic className="w-4 h-4" />
      </button>
      {error && (
        <span role="tooltip" id="voice-error" className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-2 py-1 text-caption bg-red-50 text-red-800 dark:bg-red-900/30 dark:text-red-400 rounded whitespace-nowrap pointer-events-none">
          {error}
        </span>
      )}
    </div>
  );
}
