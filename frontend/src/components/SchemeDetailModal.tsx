import React, { useEffect, useState } from 'react';
import { SchemeVerdictResult, CitizenProfile } from '../types';
import { explainScheme } from '../services/api';
import { speakText, stopSpeaking } from '../services/tts';
import { X, Volume2, VolumeX, ShieldCheck, Sparkles, Check, AlertTriangle, AlertCircle } from 'lucide-react';

interface SchemeDetailModalProps {
  scheme: SchemeVerdictResult;
  profile?: CitizenProfile | null;
  onClose: () => void;
}

export const SchemeDetailModal: React.FC<SchemeDetailModalProps> = ({ scheme, profile, onClose }) => {
  const [explanation, setExplanation] = useState<string>('');
  const [citations, setCitations] = useState<string[]>([]);
  const [isPlaying, setIsPlaying] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    let active = true;
    setIsLoading(true);

    // Call explanation endpoint
    const profileToUse = profile ? { ...profile, confirmed: true } : ({ confirmed: true } as any);
    explainScheme(scheme.slug, profileToUse)
      .then((res) => {
        if (active) {
          setExplanation(res.explanation);
          setCitations(res.source_citations || []);
        }
      })
      .catch(() => {
        if (active) {
          setExplanation(
            `You are evaluated as ${scheme.verdict} for ${scheme.name}. Under this scheme: ${scheme.benefit_snippet}`
          );
        }
      })
      .finally(() => {
        if (active) setIsLoading(false);
      });

    return () => {
      active = false;
      stopSpeaking();
    };
  }, [scheme]);

  const toggleAudio = () => {
    if (isPlaying) {
      stopSpeaking();
      setIsPlaying(false);
    } else {
      setIsPlaying(true);
      speakText(explanation || scheme.benefit_snippet, () => setIsPlaying(false));
    }
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-white rounded-3xl max-w-2xl w-full max-h-[90vh] flex flex-col shadow-2xl border border-slate-200 overflow-hidden">
        {/* Modal Header */}
        <div className="p-6 border-b border-slate-100 flex items-start justify-between bg-slate-50/50">
          <div>
            <div className="flex items-center space-x-2 mb-1.5">
              <span className="text-[11px] font-bold uppercase tracking-wider bg-blue-100 text-blue-800 px-2.5 py-0.5 rounded-full">
                {scheme.level} Scheme
              </span>
              <span className="text-[11px] font-bold bg-emerald-100 text-emerald-800 px-2 py-0.5 rounded-full border border-emerald-200 flex items-center space-x-1">
                <ShieldCheck className="w-3.5 h-3.5" />
                <span>{(scheme.verified_ratio * 100).toFixed(0)}% Verifiable</span>
              </span>
            </div>
            <h2 className="text-xl font-extrabold text-slate-900">{scheme.name}</h2>
            <p className="text-xs text-slate-500 mt-0.5">{scheme.ministry_or_department}</p>
          </div>

          <button
            onClick={onClose}
            className="p-2 text-slate-400 hover:text-slate-700 hover:bg-slate-100 rounded-full transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-6 overflow-y-auto space-y-6 text-sm">
          {/* Grounded AI Explanation */}
          <div className="p-4 rounded-2xl bg-blue-50/70 border border-blue-200 space-y-2.5">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2 text-xs font-bold text-blue-900 uppercase tracking-wider">
                <Sparkles className="w-4 h-4 text-blue-600" />
                <span>Grounded Plain-Language Explanation</span>
              </div>

              <button
                type="button"
                onClick={toggleAudio}
                className={`flex items-center space-x-1 px-2.5 py-1 text-xs font-semibold rounded-lg transition-colors ${
                  isPlaying ? 'bg-blue-600 text-white' : 'bg-white text-blue-700 border border-blue-300 hover:bg-blue-100'
                }`}
              >
                {isPlaying ? <VolumeX className="w-3.5 h-3.5" /> : <Volume2 className="w-3.5 h-3.5" />}
                <span>{isPlaying ? 'Pause' : 'Listen'}</span>
              </button>
            </div>

            <p className="text-slate-800 leading-relaxed text-xs sm:text-sm">
              {isLoading ? 'Synthesizing verified citations…' : explanation}
            </p>

            {citations.length > 0 && (
              <div className="pt-2 flex flex-wrap gap-1.5 items-center">
                <span className="text-[10px] font-bold uppercase text-blue-900">Official Citations:</span>
                {citations.map((cite, idx) => (
                  <span key={idx} className="text-[10px] font-mono bg-blue-100 text-blue-800 px-2 py-0.5 rounded-full border border-blue-200">
                    {cite}
                  </span>
                ))}
              </div>
            )}
          </div>

          {/* Benefits Overview */}
          <div>
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-2">Benefit Summary</h4>
            <div className="p-3.5 bg-slate-50 rounded-2xl border border-slate-200 text-xs text-slate-700 leading-relaxed">
              {scheme.benefit_snippet || 'Direct benefit transfers, interest subventions, or equipment grants.'}
            </div>
          </div>

          {/* Verbatim Criteria Evaluation */}
          <div>
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-2">Evaluated Official Clauses</h4>
            <div className="space-y-2">
              {scheme.criteria_results.map((c, i) => (
                <div
                  key={i}
                  className={`p-3 rounded-xl border text-xs space-y-1 ${
                    c.result === 'pass'
                      ? 'bg-emerald-50/60 border-emerald-200 text-emerald-950'
                      : c.result === 'fail'
                      ? 'bg-rose-50/60 border-rose-200 text-rose-950'
                      : 'bg-amber-50/60 border-amber-200 text-amber-950'
                  }`}
                >
                  <div className="flex items-center justify-between font-bold">
                    <span className="flex items-center space-x-1.5">
                      {c.result === 'pass' && <Check className="w-3.5 h-3.5 text-emerald-600" />}
                      {c.result === 'fail' && <AlertTriangle className="w-3.5 h-3.5 text-rose-600" />}
                      {c.result === 'unknown' && <AlertCircle className="w-3.5 h-3.5 text-amber-600" />}
                      <span>{c.field ? c.field.replaceAll('_', ' ').toUpperCase() : 'Administrative Rule'}</span>
                    </span>
                    <span className="text-[10px] uppercase tracking-wider opacity-75">[{c.result}]</span>
                  </div>

                  <p className="italic text-slate-700">"{c.quote}"</p>
                  {c.note && <p className="text-[11px] text-slate-500">Note: {c.note}</p>}
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Modal Footer */}
        <div className="p-4 border-t border-slate-100 bg-slate-50 flex items-center justify-end">
          <button
            onClick={onClose}
            className="px-5 py-2 bg-slate-900 hover:bg-slate-800 text-white text-xs font-semibold rounded-xl transition-colors"
          >
            Close Details
          </button>
        </div>
      </div>
    </div>
  );
};
