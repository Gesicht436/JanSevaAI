import React, { useState } from 'react';
import { ArrowUp, Sparkles, HelpCircle } from 'lucide-react';
import { CitizenProfile } from '../types';
import { VoiceRecorder } from './VoiceRecorder';

interface ChatIntakeProps {
  onExtractText: (text: string) => void;
  onExtractAudio: (audioBlob: Blob) => void;
  isLoading: boolean;
  clarificationPrompt?: string | null;
  suggestedFields?: string[];
  currentProfile?: CitizenProfile | null;
}

export const ChatIntake: React.FC<ChatIntakeProps> = ({
  onExtractText,
  onExtractAudio,
  isLoading,
  clarificationPrompt = null,
  suggestedFields = [],
  currentProfile = null,
}) => {
  const [inputText, setInputText] = useState('');

  const samplePrompts = [
    'I am a bachelor in IT, 26 years old with 3 years experience, seeking a startup loan in Gujarat.',
    'I am a 38-year-old rural farmer in Uttar Pradesh with 3 acres land looking for crop subsidies.',
    'I am a 20-year-old female student in Delhi pursuing B.Sc, looking for higher education scholarships.',
    'I am an artisan in Rajasthan with ₹1.5 Lakh annual family income seeking equipment support.',
  ];

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputText.trim() || isLoading) return;
    onExtractText(inputText.trim());
    setInputText('');
  };

  return (
    <div className="bg-white rounded-3xl p-6 sm:p-10 border border-zinc-200/80 shadow-[0_1px_3px_rgba(0,0,0,0.02)] space-y-8 animate-fadeIn max-w-3xl mx-auto">
      {/* Header */}
      <div className="space-y-3 text-center sm:text-left">
        <div className="inline-flex items-center space-x-1.5 px-3 py-1 bg-zinc-100 rounded-full text-zinc-700 text-xs font-medium border border-zinc-200/60">
          <Sparkles className="w-3.5 h-3.5 text-zinc-600" />
          <span>Step 1 · Natural Speech & Text</span>
        </div>
        
        <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-zinc-900 leading-tight">
          Find government support grounded in verified statutory rules.
        </h1>
        
        <p className="text-sm text-zinc-500 leading-relaxed max-w-2xl font-normal">
          Describe your background, education, work, and the assistance you need in plain English or Hinglish. We extract your facts without fabricating any criteria.
        </p>

        <div className="flex flex-wrap items-center justify-center sm:justify-start gap-2 pt-1 text-xs text-zinc-500 font-normal">
          <span className="flex items-center space-x-1 px-2.5 py-1 rounded-md bg-zinc-50 border border-zinc-200/60 text-zinc-700">
            <span>✓ Verifiable Citations</span>
          </span>
          <span className="flex items-center space-x-1 px-2.5 py-1 rounded-md bg-zinc-50 border border-zinc-200/60 text-zinc-700">
            <span>✓ Private & Session-Only</span>
          </span>
          <span className="flex items-center space-x-1 px-2.5 py-1 rounded-md bg-zinc-50 border border-zinc-200/60 text-zinc-700">
            <span>✓ Rule E9 Confirmed</span>
          </span>
        </div>
      </div>

      {/* Sparse Clarification Prompt (if triggered) */}
      {clarificationPrompt && (
        <div className="p-4 rounded-2xl bg-amber-50/70 border border-amber-200/80 space-y-2">
          <div className="flex items-start space-x-3">
            <HelpCircle className="w-4 h-4 text-amber-700 shrink-0 mt-0.5" />
            <div>
              <p className="text-xs font-semibold text-amber-900 uppercase tracking-wide">Additional Details Helpful</p>
              <p className="text-xs sm:text-sm text-amber-800 mt-0.5 leading-relaxed">{clarificationPrompt}</p>
            </div>
          </div>
          {suggestedFields.length > 0 && (
            <div className="flex flex-wrap gap-1.5 pl-7 pt-1">
              {suggestedFields.map((f) => (
                <span key={f} className="text-[11px] font-medium bg-white text-amber-800 border border-amber-300/80 px-2.5 py-0.5 rounded-full">
                  + {f.replaceAll('_', ' ')}
                </span>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Input Box */}
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="relative border border-zinc-200 rounded-2xl transition-all focus-within:border-zinc-800 focus-within:ring-2 focus-within:ring-zinc-800/10 bg-zinc-50/50">
          <textarea
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            placeholder={
              currentProfile
                ? 'Reply with additional details (e.g. "I live in Gujarat and hold a BPL card")…'
                : 'e.g. I am 26, bachelor in IT, with 3 years of work experience, looking for enterprise credit in Gujarat…'
            }
            rows={4}
            className="w-full bg-transparent p-4 pb-14 text-sm text-zinc-900 placeholder-zinc-400 focus:outline-none resize-none font-normal leading-relaxed"
          />

          <div className="absolute bottom-3 right-3 flex items-center space-x-2">
            <VoiceRecorder
              onTranscript={(spoken) => setInputText(spoken)}
              onAudioRecorded={onExtractAudio}
              disabled={isLoading}
            />

            <button
              type="submit"
              disabled={isLoading || !inputText.trim()}
              className="flex items-center space-x-1.5 px-4 py-2 bg-zinc-900 hover:bg-zinc-800 text-white text-xs font-semibold rounded-xl shadow-xs disabled:opacity-30 disabled:cursor-not-allowed transition-all active:scale-[0.98]"
            >
              <span>{isLoading ? 'Analyzing…' : 'Analyze Facts'}</span>
              <ArrowUp className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>

        {/* Example Prompt Chips */}
        {!currentProfile && (
          <div className="space-y-2 pt-1">
            <p className="text-xs font-medium text-zinc-400">Or click a sample scenario to pre-fill:</p>
            <div className="flex flex-wrap gap-2">
              {samplePrompts.map((prompt, idx) => (
                <button
                  key={idx}
                  type="button"
                  onClick={() => setInputText(prompt)}
                  className="text-left text-xs bg-zinc-100/80 hover:bg-zinc-200/70 text-zinc-700 px-3 py-1.5 rounded-full border border-zinc-200/60 transition-colors"
                >
                  {prompt}
                </button>
              ))}
            </div>
          </div>
        )}
      </form>
    </div>
  );
};
