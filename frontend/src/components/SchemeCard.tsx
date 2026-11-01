import React, { useState } from 'react';
import { SchemeVerdictResult } from '../types';
import { speakText, stopSpeaking } from '../services/tts';
import { 
  Volume2, 
  VolumeX, 
  CheckCircle, 
  AlertCircle, 
  Sparkles, 
  ChevronRight, 
  ExternalLink,
  FileText,
  Building2,
  Clock
} from 'lucide-react';

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
      const textToSpeak = `${scheme.name}. Under this scheme: ${scheme.description || scheme.benefit_snippet}`;
      speakText(textToSpeak, () => setIsPlaying(false));
    }
  };

  const mySchemeUrl = scheme.myscheme_url || `https://www.myscheme.gov.in/schemes/${scheme.slug}`;

  const getVerdictBadge = () => {
    if (scheme.verdict === 'eligible') {
      return (
        <span className="inline-flex items-center space-x-1.5 text-xs font-semibold text-emerald-800 bg-emerald-50 border border-emerald-200 px-2.5 py-0.5 rounded-full">
          <CheckCircle className="w-3.5 h-3.5 text-emerald-600" />
          <span>Likely Eligible</span>
        </span>
      );
    }
    if (scheme.verdict === 'needs_more_info') {
      return (
        <span className="inline-flex items-center space-x-1.5 text-xs font-semibold text-amber-800 bg-amber-50 border border-amber-200 px-2.5 py-0.5 rounded-full">
          <AlertCircle className="w-3.5 h-3.5 text-amber-600" />
          <span>Needs More Info</span>
        </span>
      );
    }
    if (scheme.verdict === 'closed') {
      return (
        <span className="inline-flex items-center space-x-1.5 text-xs font-semibold text-zinc-600 bg-zinc-100 border border-zinc-200 px-2.5 py-0.5 rounded-full">
          <Clock className="w-3.5 h-3.5 text-zinc-500" />
          <span>Past Deadline</span>
        </span>
      );
    }
    return (
      <span className="inline-flex items-center space-x-1.5 text-xs font-medium text-zinc-600 bg-zinc-100 border border-zinc-200 px-2.5 py-0.5 rounded-full">
        <span>Ineligible</span>
      </span>
    );
  };

  return (
    <div
      onClick={() => onSelect(scheme)}
      className="bg-white rounded-3xl p-6 border border-zinc-200/80 hover:border-zinc-400/90 shadow-[0_1px_3px_rgba(0,0,0,0.02)] hover:shadow-md transition-all cursor-pointer flex flex-col justify-between space-y-4 relative group active:scale-[0.99]"
    >
      <div className="space-y-3">
        {/* Top Badges */}
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div className="flex items-center space-x-2">
            {getVerdictBadge()}
            {scheme.unlocked_in_this_round && (
              <span className="inline-flex items-center space-x-1 text-xs font-semibold text-indigo-700 bg-indigo-50 border border-indigo-200 px-2.5 py-0.5 rounded-full animate-bounce">
                <Sparkles className="w-3 h-3 text-indigo-600" />
                <span>Unlocked Now</span>
              </span>
            )}
          </div>

          <div className="flex items-center space-x-1.5 text-[11px] text-zinc-400 font-medium">
            <span className="uppercase tracking-wider px-2 py-0.5 rounded-md bg-zinc-100 text-zinc-600">
              {scheme.level}
            </span>
            <span className="px-2 py-0.5 rounded-md bg-zinc-50 border border-zinc-200/60 text-zinc-600">
              {(scheme.verified_ratio * 100).toFixed(0)}% Verified
            </span>
          </div>
        </div>

        {/* Scheme Name */}
        <h3 className="font-semibold text-base text-zinc-900 group-hover:text-black transition-colors line-clamp-2 leading-snug">
          {scheme.name}
        </h3>

        {/* Ministry */}
        <p className="text-xs text-zinc-500 line-clamp-1 font-normal">
          {scheme.ministry_or_department || 'Government of India'}
        </p>

        {/* Benefit Callout Box */}
        <div className="bg-zinc-50 border border-zinc-100 rounded-2xl p-3.5 text-xs text-zinc-700 leading-relaxed line-clamp-3">
          {scheme.description || scheme.benefit_snippet || 'Provides financial assistance, subsidies, or institutional support to eligible beneficiaries.'}
        </div>

        {/* Requirement Indicators (Docs count & Specialized Dept checks) */}
        <div className="flex flex-wrap items-center gap-2 pt-1">
          {scheme.required_documents && scheme.required_documents.length > 0 && (
            <span
              className="inline-flex items-center space-x-1 text-[11px] font-medium text-zinc-600 bg-zinc-100/80 px-2.5 py-0.5 rounded-md"
              title={`${scheme.required_documents.length} official documents required`}
            >
              <FileText className="w-3 h-3 text-zinc-500" />
              <span>{scheme.required_documents.length} Docs Required</span>
            </span>
          )}

          {scheme.specialized_criteria && scheme.specialized_criteria.length > 0 && (
            <span
              className="inline-flex items-center space-x-1 text-[11px] font-medium text-amber-800 bg-amber-50 border border-amber-200/80 px-2.5 py-0.5 rounded-md"
              title={`${scheme.specialized_criteria.length} specialized criteria require department self-verification`}
            >
              <Building2 className="w-3 h-3 text-amber-600" />
              <span>{scheme.specialized_criteria.length} Dept Checks</span>
            </span>
          )}
        </div>
      </div>

      {/* Card Footer Actions */}
      <div className="flex items-center justify-between pt-3 border-t border-zinc-100 text-xs">
        <div className="flex items-center space-x-2">
          <button
            type="button"
            onClick={handleAudioToggle}
            className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-xl border transition-all ${
              isPlaying
                ? 'bg-zinc-900 text-white border-zinc-900 shadow-xs'
                : 'text-zinc-600 hover:text-zinc-900 bg-zinc-50 hover:bg-zinc-100 border-zinc-200/80'
            }`}
            title="Listen to explanation"
          >
            {isPlaying ? <VolumeX className="w-3.5 h-3.5" /> : <Volume2 className="w-3.5 h-3.5" />}
            <span className="font-medium">{isPlaying ? 'Stop' : 'Listen'}</span>
          </button>

          <a
            href={mySchemeUrl}
            target="_blank"
            rel="noopener noreferrer"
            onClick={(e) => e.stopPropagation()}
            className="flex items-center space-x-1 text-xs text-zinc-600 hover:text-zinc-900 font-medium px-2.5 py-1.5 rounded-xl hover:bg-zinc-100 transition-colors"
            title="Open official scheme on myScheme.gov.in"
          >
            <span>myScheme</span>
            <ExternalLink className="w-3 h-3 text-zinc-400" />
          </a>
        </div>

        <span className="flex items-center space-x-1 text-zinc-900 font-semibold text-xs group-hover:translate-x-0.5 transition-transform">
          <span>Details</span>
          <ChevronRight className="w-3.5 h-3.5" />
        </span>
      </div>
    </div>
  );
};
