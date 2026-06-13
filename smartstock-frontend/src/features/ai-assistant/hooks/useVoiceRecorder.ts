import { useState, useRef, useCallback, useEffect } from 'react';
import { transcribeAudio } from '../api';

type RecorderState = 'idle' | 'recording' | 'transcribing';

const MAX_DURATION = 30;

function stopMediaRecorder(mr: MediaRecorder | null) {
  if (mr && mr.state === 'recording') {
    mr.stop();
  }
}

export function useVoiceRecorder(onTranscript?: (text: string) => void) {
  const [state, setState] = useState<RecorderState>('idle');
  const [error, setError] = useState<string | null>(null);
  const [elapsed, setElapsed] = useState(0);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const onTranscriptRef = useRef(onTranscript);

  useEffect(() => {
    onTranscriptRef.current = onTranscript;
  }, [onTranscript]);

  const cancelledRef = useRef(false);

  const cleanup = useCallback(() => {
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
    stopMediaRecorder(mediaRecorderRef.current);
    mediaRecorderRef.current = null;
    chunksRef.current = [];
    setElapsed(0);
  }, []);

  useEffect(() => cleanup, [cleanup]);

  const startRecording = useCallback(async () => {
    setError(null);
    cancelledRef.current = false;
    if (!navigator.mediaDevices?.getUserMedia) {
      setError('Voice input is not supported in this browser.');
      return;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mr = new MediaRecorder(stream, { mimeType: 'audio/webm;codecs=opus' });
      chunksRef.current = [];

      mr.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data);
      };

      mr.onstop = async () => {
        stream.getTracks().forEach((t) => t.stop());
        if (cancelledRef.current) return;
        setState('transcribing');
        try {
          const blob = new Blob(chunksRef.current, { type: 'audio/webm' });
          const text = await transcribeAudio(blob);
          onTranscriptRef.current?.(text);
        } catch (e) {
          setError(e instanceof Error ? e.message : 'Transcription failed.');
        } finally {
          setState('idle');
          chunksRef.current = [];
        }
      };

      mr.start();
      mediaRecorderRef.current = mr;
      setState('recording');

      let secs = 0;
      timerRef.current = setInterval(() => {
        secs += 1;
        setElapsed(secs);
        if (secs >= MAX_DURATION) {
          stopMediaRecorder(mediaRecorderRef.current);
        }
      }, 1000);
    } catch {
      setError('Microphone permission denied.');
    }
  }, []);

  const stopRecording = useCallback(() => {
    stopMediaRecorder(mediaRecorderRef.current);
  }, []);

  const cancelRecording = useCallback(() => {
    cancelledRef.current = true;
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stream.getTracks().forEach((t) => t.stop());
      mediaRecorderRef.current.stop();
    }
    mediaRecorderRef.current = null;
    chunksRef.current = [];
    setState('idle');
    setElapsed(0);
  }, []);

  return {
    state,
    error,
    elapsed,
    maxDuration: MAX_DURATION,
    startRecording,
    stopRecording,
    cancelRecording,
    isSupported: typeof navigator !== 'undefined' && !!navigator.mediaDevices?.getUserMedia,
  };
}
