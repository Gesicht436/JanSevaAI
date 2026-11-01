import React, { useState, useRef, useEffect } from 'react';
import { Mic, Square } from 'lucide-react';

interface VoiceRecorderProps {
  onTranscript?: (text: string) => void;
  onAudioRecorded?: (audioBlob: Blob) => void;
  disabled?: boolean;
}

export const VoiceRecorder: React.FC<VoiceRecorderProps> = ({
  onTranscript,
  onAudioRecorded,
  disabled,
}) => {
  const [recording, setRecording] = useState(false);
  const [countdown, setCountdown] = useState(0);
  const recognitionRef = useRef<any>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const timerRef = useRef<number | null>(null);

  // Check Web Speech API availability
  const hasSpeechRecognition = typeof window !== 'undefined' && (
    'SpeechRecognition' in window || 'webkitSpeechRecognition' in window
  );

  useEffect(() => {
    return () => {
      if (recognitionRef.current) {
        try {
          recognitionRef.current.abort();
        } catch {}
      }
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    };
  }, []);

  const startRecording = async () => {
    // Mode 1: Web Speech API (transcribes live speech directly into chatbox)
    if (hasSpeechRecognition && onTranscript) {
      try {
        const SpeechRecognitionClass = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
        const recognition = new SpeechRecognitionClass();
        recognitionRef.current = recognition;

        recognition.continuous = true;
        recognition.interimResults = true;
        recognition.lang = 'en-IN'; // Indian English handles Indian names & states

        let finalTranscript = '';

        recognition.onresult = (event: any) => {
          let currentInterim = '';
          for (let i = event.resultIndex; i < event.results.length; i++) {
            const transcript = event.results[i][0].transcript;
            if (event.results[i].isFinal) {
              finalTranscript += transcript + ' ';
            } else {
              currentInterim += transcript;
            }
          }
          const spoken = (finalTranscript + currentInterim).trim();
          if (spoken) {
            onTranscript(spoken);
          }
        };

        recognition.onerror = (event: any) => {
          console.warn('Speech recognition status:', event.error);
          stopRecording();
        };

        recognition.onend = () => {
          setRecording(false);
          if (timerRef.current) {
            clearInterval(timerRef.current);
            timerRef.current = null;
          }
        };

        recognition.start();
        setRecording(true);
        setCountdown(60);

        timerRef.current = window.setInterval(() => {
          setCountdown((prev) => {
            if (prev <= 1) {
              stopRecording();
              return 0;
            }
            return prev - 1;
          });
        }, 1000);
        return;
      } catch (err) {
        console.warn('Web Speech API failed to start, falling back to MediaRecorder:', err);
      }
    }

    // Mode 2: MediaRecorder fallback
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      chunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = () => {
        const mimeType = mediaRecorder.mimeType || 'audio/webm';
        const blob = new Blob(chunksRef.current, { type: mimeType });
        if (onAudioRecorded) {
          onAudioRecorded(blob);
        }
        stream.getTracks().forEach((track) => track.stop());
      };

      mediaRecorder.start();
      setRecording(true);
      setCountdown(60);

      timerRef.current = window.setInterval(() => {
        setCountdown((prev) => {
          if (prev <= 1) {
            stopRecording();
            return 0;
          }
          return prev - 1;
        });
      }, 1000);
    } catch {
      alert('Microphone access denied or unavailable in this browser.');
    }
  };

  const stopRecording = () => {
    if (recognitionRef.current) {
      try {
        recognitionRef.current.stop();
      } catch {}
      recognitionRef.current = null;
    }
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop();
    }
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
    setRecording(false);
  };

  return (
    <div className="flex items-center space-x-2">
      {recording ? (
        <button
          type="button"
          onClick={stopRecording}
          className="flex items-center space-x-2 px-3 py-1.5 bg-zinc-900 text-white text-xs font-medium rounded-xl shadow-xs transition-all active:scale-[0.98]"
          title="Stop recording"
        >
          <span className="w-2 h-2 rounded-full bg-rose-500 animate-ping" />
          <Square className="w-3 h-3 fill-current" />
          <span>Stop ({countdown}s)</span>
        </button>
      ) : (
        <button
          type="button"
          onClick={startRecording}
          disabled={disabled}
          className="flex items-center space-x-1.5 px-3 py-1.5 bg-zinc-100 hover:bg-zinc-200 text-zinc-700 text-xs font-medium rounded-xl border border-zinc-200/80 transition-all disabled:opacity-40 active:scale-[0.98]"
          title="Click to speak your background using your microphone"
        >
          <Mic className="w-3.5 h-3.5 text-zinc-600" />
          <span className="hidden sm:inline">Voice</span>
        </button>
      )}
    </div>
  );
};
