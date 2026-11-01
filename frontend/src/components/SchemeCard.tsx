import React, { useState } from 'react';
import { SchemeVerdictResult } from '../types';
import { speakText, stopSpeaking } from '../services/tts';
import { Volume2, VolumeX, CheckCircle, AlertCircle, Sparkles, ChevronRight } from 'lucide-react';

interface SchemeCardProps {
  scheme: SchemeVerdictResult;
  onSelect: (scheme: SchemeVerdictResult) => void;
}

export const SchemeCard: React.FC<SchemeCardProps> = ({ scheme, onSelect }) => {
  const [isPlaying, setIsPlaying] = useState(false);

  const handleAudioToggle = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (isPlaying) {
      stopSpeaking();
      setIsPlaying(false);
    } else {
      setIsPlaying(true);
      const textToSpeak = `${scheme.name}. Under this scheme: ${scheme.benefit_snippet}`;
      speakText(textToSpeak, () => setIsPlaying(false));
    }
  };

  const getVerdictBadge = () => {
    if (scheme.verdict === 'eligible') {
      return (
        <span className="flex items-center space-x-1 text-xs font-bold text-emerald-700 bg-emerald-50 border border-emerald-200 px-2.5 py-1 rounded-full">
          <CheckCircle className="w-3.5 h-3.5" />
          <span>Likely Eligible</span>
        </span>
      );
    }
    if (scheme.verdict === 'needs_more_info') {
      return (
        <span className="flex items-center space-x-1 text-xs font-bold text-amber-700 bg-amber-50 border border-amber-200 px-2.5 py-1 rounded-full">
          <AlertCircle className="w-3.5 h-3.5" />
          <span>Needs More Info</span>
        </span>
      );
    }
    return (
      <span className="text-xs font-semibold text-slate-500 bg-slate-100 px-2 py-0.5 rounded-full">
        {scheme.verdict}
      </span>
    );
  };

  return (
    <div
      onClick={() => onSelect(scheme)}
      className="bg-white rounded-2xl p-5 border border-slate-200 hover:border-blue-400 hover:shadow-md transition-all cursor-pointer flex flex-col justify-between space-y-4 relative group"
    >
      <div>
        {/* Top Badges */}
        <div className="flex flex-wrap items-center justify-between gap-2 mb-2">
          <div className="flex items-center space-x-2">
            {getVerdictBadge()}
            {scheme.unlocked_in_this_round && (
              <span className="flex items-center space-x-1 text-xs font-extrabold text-blue-700 bg-blue-100 border border-blue-300 px-2.5 py-1 rounded-full animate-bounce">
                <Sparkles className="w-3.5 h-3.5 text-blue-600 fill-current" />
                <span>Unlocked Now!</span>
              </span>
            )}
          </div>

          <div className="flex items-center space-x-1.5">
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500 bg-slate-100 px-2 py-0.5 rounded">
              {scheme.level}
            </span>
            <span className="text-[10px] font-bold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
              {(scheme.verified_ratio * 100).toFixed(0)}% Verified
            </span>
          </div>
        </div>

        {/* Scheme Name */}
        <h3 className="font-extrabold text-base text-slate-900 group-hover:text-blue-600 transition-colors line-clamp-2">
          {scheme.name}
        </h3>

        {/* Ministry */}
        <p className="text-xs font-medium text-slate-500 mt-1 line-clamp-1">
          {scheme.ministry_or_department || 'Government of India'}
        </p>

        {/* Benefit Snippet */}
        <p className="text-xs text-slate-600 mt-3 line-clamp-3 leading-relaxed bg-slate-50 p-2.5 rounded-xl border border-slate-100">
          {scheme.benefit_snippet || 'Provides financial assistance, subsidies, or institutional support to eligible beneficiaries.'}
        </p>
      </div>

      {/* Card Footer Actions */}
      <div className="flex items-center justify-between pt-2 border-t border-slate-100 text-xs">
        <button
          type="button"
          onClick={handleAudioToggle}
          className={`flex items-center space-x-1.5 px-2.5 py-1.5 rounded-lg border transition-colors ${
            isPlaying
              ? 'bg-blue-600 text-white border-blue-600'
              : 'text-slate-600 hover:text-slate-900 bg-slate-50 border-slate-200'
          }`}
          title="Listen to explanation"
        >
          {isPlaying ? <VolumeX className="w-3.5 h-3.5" /> : <Volume2 className="w-3.5 h-3.5 text-blue-600" />}
          <span>{isPlaying ? 'Stop' : 'Listen'}</span>
        </button>

        <span className="flex items-center space-x-1 text-blue-600 font-semibold group-hover:translate-x-0.5 transition-transform">
          <span>View Evidence</span>
          <ChevronRight className="w-3.5 h-3.5" />
        </span>
      </div>
    </div>
  );
};
