import { fetchSpeechAudio } from './api';

let currentAudio: HTMLAudioElement | null = null;

export async function speakText(text: string, onEnded?: () => void): Promise<void> {
  stopSpeaking();

  try {
    const audioBlob = await fetchSpeechAudio(text);
    const audioUrl = URL.createObjectURL(audioBlob);
    const audio = new Audio(audioUrl);
    currentAudio = audio;

    audio.onended = () => {
      URL.revokeObjectURL(audioUrl);
      currentAudio = null;
      if (onEnded) onEnded();
    };

    audio.onerror = () => {
      URL.revokeObjectURL(audioUrl);
      currentAudio = null;
      fallbackWebSpeech(text, onEnded);
    };

    await audio.play();
  } catch (err) {
    fallbackWebSpeech(text, onEnded);
  }
}

export function stopSpeaking(): void {
  if (currentAudio) {
    currentAudio.pause();
    currentAudio.currentTime = 0;
    currentAudio = null;
  }
  if (typeof window !== 'undefined' && window.speechSynthesis) {
    window.speechSynthesis.cancel();
  }
}

function fallbackWebSpeech(text: string, onEnded?: () => void): void {
  if (typeof window === 'undefined' || !window.speechSynthesis) return;
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.lang = 'en-IN';
  utterance.rate = 0.95;
  if (onEnded) utterance.onend = onEnded;
  window.speechSynthesis.speak(utterance);
}
