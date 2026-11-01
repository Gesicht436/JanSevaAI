import React, { useState } from 'react';
import { Send, Sparkles, MessageSquare, HelpCircle } from 'lucide-react';
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
    'I am a bachelor in IT, 26 years old fellow with some experience in IT sector and wants some loan in Gujarat.',
    'I am a 38-year-old widow in rural Gujarat managing 2 acres of farmland.',
    'I am 19, studying B.Sc in Uttar Pradesh from an OBC family, looking for scholarships.',
    'I am a small artisan in Rajasthan with ₹1.2 Lakh income looking for equipment subsidies.',
  ];

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputText.trim() || isLoading) return;
    onExtractText(inputText.trim());
    setInputText('');
  };

  return (
    <div className="bg-white rounded-3xl p-6 sm:p-8 shadow-sm border border-slate-200 space-y-6">
      {/* Header */}
      <div>
        <div className="inline-flex items-center space-x-1.5 px-3 py-1 bg-blue-50 border border-blue-200 rounded-full text-blue-700 text-xs font-bold uppercase tracking-wider mb-2">
          <Sparkles className="w-3.5 h-3.5" />
          <span>Step 1 · Conversational Intake</span>
        </div>
        <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
          Find Government Support Grounded in Verifiable Rules.
        </h1>
        <p className="text-sm text-slate-500 mt-1">
          Describe your background, education, work, and the assistance you need in plain English or Hinglish.
        </p>

        <div className="flex flex-wrap gap-3 mt-3 text-xs text-slate-600 font-medium">
          <span className="flex items-center text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-md border border-emerald-200">
            ✓ Official Source Citations
          </span>
          <span className="flex items-center text-blue-700 bg-blue-50 px-2 py-0.5 rounded-md border border-blue-200">
            ✓ Session-Only / No Account
          </span>
          <span className="flex items-center text-indigo-700 bg-indigo-50 px-2 py-0.5 rounded-md border border-indigo-200">
            ✓ Verifiable Two-Stage Matching
          </span>
        </div>
      </div>

      {/* Sparse Clarification Prompt (if triggered) */}
      {clarificationPrompt && (
        <div className="p-4 rounded-2xl bg-amber-50 border border-amber-200 space-y-2">
          <div className="flex items-start space-x-3">
            <HelpCircle className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
            <div>
              <p className="text-xs font-bold text-amber-900 uppercase tracking-wider">A Little More Context Needed</p>
              <p className="text-sm text-amber-800 mt-0.5 leading-relaxed">{clarificationPrompt}</p>
            </div>
          </div>
          {suggestedFields.length > 0 && (
            <div className="flex flex-wrap gap-1.5 pl-8 pt-1">
              {suggestedFields.map((f) => (
                <span key={f} className="text-[11px] font-semibold bg-white text-amber-800 border border-amber-300 px-2 py-0.5 rounded-full">
                  + {f.replaceAll('_', ' ')}
                </span>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Input Box */}
      <form onSubmit={handleSubmit} className="space-y-3">
        <div className="relative border-2 border-slate-200 focus-within:border-blue-500 rounded-2xl transition-all shadow-inner bg-slate-50/50">
          <textarea
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            placeholder={
              currentProfile
                ? 'Reply with additional details (e.g. "I live in Gujarat and hold a BPL card")…'
                : 'e.g. I am 26, bachelor in IT, have 2 years of work experience in software, looking for startup loans in Gujarat…'
            }
            rows={4}
            className="w-full bg-transparent p-4 pb-12 text-sm text-slate-800 placeholder-slate-400 focus:outline-none resize-none font-normal"
          />

          <div className="absolute bottom-2.5 right-2.5 flex items-center space-x-2">
            <VoiceRecorder
              onTranscript={(spoken) => setInputText(spoken)}
              onAudioRecorded={onExtractAudio}
              disabled={isLoading}
            />

            <button
              type="submit"
              disabled={isLoading || !inputText.trim()}
              className="flex items-center space-x-1.5 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold rounded-xl shadow-md shadow-blue-500/20 disabled:opacity-40 disabled:cursor-not-allowed transition-all"
            >
              <Send className="w-3.5 h-3.5" />
              <span>{isLoading ? 'Parsing…' : 'Submit'}</span>
            </button>
          </div>
        </div>

        {/* Example Prompt Chips */}
        {!currentProfile && (
          <div className="pt-2">
            <p className="text-xs font-semibold text-slate-400 mb-2 flex items-center space-x-1">
              <MessageSquare className="w-3.5 h-3.5" />
              <span>Or try an example citizen query:</span>
            </p>
            <div className="flex flex-wrap gap-2">
              {samplePrompts.map((prompt, idx) => (
                <button
                  key={idx}
                  type="button"
                  onClick={() => setInputText(prompt)}
                  className="text-left text-xs bg-slate-100 hover:bg-slate-200 text-slate-700 px-3 py-1.5 rounded-xl border border-slate-200/80 transition-colors"
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
