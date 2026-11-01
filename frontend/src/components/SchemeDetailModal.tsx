import React, { useEffect, useState } from 'react';
import { SchemeVerdictResult, CitizenProfile } from '../types';
import { explainScheme } from '../services/api';
import { speakText, stopSpeaking } from '../services/tts';
import { 
  X, 
  Volume2, 
  VolumeX, 
  ShieldCheck, 
  Sparkles, 
  Check, 
  AlertTriangle, 
  AlertCircle, 
  ExternalLink,
  FileText,
  Building2,
  CheckCircle2,
  Info,
  HelpCircle
} from 'lucide-react';

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

  const mySchemeUrl = scheme.myscheme_url || `https://www.myscheme.gov.in/schemes/${scheme.slug}`;

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
            `You are evaluated as ${scheme.verdict} for ${scheme.name}. Under this scheme: ${scheme.description || scheme.benefit_snippet}`
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
      speakText(explanation || scheme.description || scheme.benefit_snippet, () => setIsPlaying(false));
    }
  };

  // Filter automated vs specialized criteria
  const automatedCriteria = (scheme.criteria_results || []).filter((c) => !c.is_specialized && c.field);
  const specializedCriteriaQuotes = scheme.specialized_criteria || [];

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-white rounded-3xl max-w-3xl w-full max-h-[92vh] flex flex-col shadow-2xl border border-slate-200 overflow-hidden animate-fadeIn">
        
        {/* Modal Header */}
        <div className="p-6 border-b border-slate-100 flex items-start justify-between bg-slate-50/80">
          <div className="space-y-1.5 pr-4">
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-[11px] font-bold uppercase tracking-wider bg-blue-100 text-blue-800 px-2.5 py-0.5 rounded-full">
                {scheme.level} Scheme
              </span>
              <span className="text-[11px] font-bold bg-emerald-100 text-emerald-800 px-2 py-0.5 rounded-full border border-emerald-200 flex items-center space-x-1">
                <ShieldCheck className="w-3.5 h-3.5" />
                <span>{(scheme.verified_ratio * 100).toFixed(0)}% Verifiable</span>
              </span>
              <a
                href={mySchemeUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center space-x-1.5 text-xs font-bold text-blue-700 bg-blue-50 hover:bg-blue-100 border border-blue-200 px-3 py-0.5 rounded-full transition-colors"
                title="Open official scheme page on myScheme.gov.in"
              >
                <span>myscheme.gov.in</span>
                <ExternalLink className="w-3.5 h-3.5" />
              </a>
            </div>
            <h2 className="text-xl font-extrabold text-slate-900 leading-snug">{scheme.name}</h2>
            <p className="text-xs text-slate-500">{scheme.ministry_or_department || 'Government of India'}</p>
          </div>

          <button
            onClick={onClose}
            className="p-2 text-slate-400 hover:text-slate-700 hover:bg-slate-200/60 rounded-full transition-colors flex-shrink-0"
            title="Close dialog"
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

          {/* Scheme Description & Overview */}
          <div>
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-2 flex items-center space-x-1.5">
              <Info className="w-3.5 h-3.5 text-blue-600" />
              <span>Scheme Description & Overview</span>
            </h4>
            <div className="p-4 bg-slate-50 rounded-2xl border border-slate-200 text-xs sm:text-sm text-slate-700 leading-relaxed">
              {scheme.description || scheme.benefit_snippet || 'No detailed description available in catalog.'}
            </div>
          </div>

          {/* Benefits Overview */}
          <div>
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-2">Benefit Summary</h4>
            <div className="p-3.5 bg-slate-50 rounded-2xl border border-slate-200 text-xs text-slate-700 leading-relaxed">
              {scheme.benefit_snippet || 'Direct benefit transfers, subsidies, interest subvention, or capacity building.'}
            </div>
          </div>

          {/* Section: Required Documents Checklist */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-700 flex items-center space-x-1.5">
                <FileText className="w-4 h-4 text-indigo-600" />
                <span>Required Documents ({scheme.required_documents?.length || 0})</span>
              </h4>
              <span className="text-[11px] text-slate-500 font-medium">Keep ready before applying</span>
            </div>

            {scheme.required_documents && scheme.required_documents.length > 0 ? (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {scheme.required_documents.map((doc, idx) => (
                  <div
                    key={idx}
                    className="flex items-start space-x-2.5 p-3 bg-slate-50 hover:bg-slate-100/90 rounded-xl border border-slate-200 text-xs text-slate-800 transition-colors"
                  >
                    <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0 mt-0.5" />
                    <span className="leading-snug font-medium">{doc}</span>
                  </div>
                ))}
              </div>
            ) : (
              <div className="p-3 bg-slate-50 rounded-xl border border-dashed border-slate-200 text-xs text-slate-500 italic">
                No specific mandatory documents listed in the official catalog for this scheme.
              </div>
            )}
          </div>

          {/* Section: Specialized & Department-Evaluated Eligibility Criteria */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <h4 className="text-xs font-bold uppercase tracking-wider text-amber-900 flex items-center space-x-1.5">
                <Building2 className="w-4 h-4 text-amber-600" />
                <span>Department-Evaluated & Specialized Criteria ({specializedCriteriaQuotes.length})</span>
              </h4>
              <span className="text-[10px] font-bold uppercase bg-amber-100 text-amber-800 px-2.5 py-0.5 rounded-full border border-amber-300">
                Self-Verification Required
              </span>
            </div>

            <div className="p-4 bg-amber-50/80 rounded-2xl border border-amber-200/90 space-y-3">
              <div className="flex items-start space-x-2.5">
                <HelpCircle className="w-4 h-4 text-amber-700 flex-shrink-0 mt-0.5" />
                <p className="text-xs text-amber-950 leading-relaxed">
                  <strong>Department Prerequisite Notice:</strong> Our automated AI engine verifies statutory baseline parameters (age limits, state residency, education level, category, and income). However, the specific conditions below cannot be evaluated automatically (e.g. specialized engineering credentials, years of domain expertise, departmental registrations, or subjective committee evaluations). <em>These depend directly on the applicant and the scheme's administering department or nodal agency.</em>
                </p>
              </div>

              {specializedCriteriaQuotes.length > 0 ? (
                <div className="space-y-2 pt-1">
                  {specializedCriteriaQuotes.map((quote, idx) => (
                    <div
                      key={idx}
                      className="p-3 bg-white rounded-xl border border-amber-200 shadow-xs flex items-start space-x-2.5"
                    >
                      <span className="w-5 h-5 rounded-full bg-amber-100 text-amber-800 flex items-center justify-center font-bold text-[10px] flex-shrink-0 mt-0.5">
                        {idx + 1}
                      </span>
                      <div className="flex-1">
                        <p className="text-xs text-slate-800 italic font-medium">"{quote}"</p>
                        <span className="inline-block text-[10px] text-amber-800 font-semibold mt-1">
                          Evaluated by nodal department / scheme authority
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-xs text-slate-500 italic pl-6">
                  No additional specialized department prerequisites required for this scheme.
                </p>
              )}
            </div>
          </div>

          {/* Section: Automated Statutory Criteria Evaluation */}
          <div>
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-2">
              Automated Statutory Eligibility Checks (Evaluated by JanSeva AI)
            </h4>
            {automatedCriteria.length > 0 ? (
              <div className="space-y-2">
                {automatedCriteria.map((c, i) => (
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
                        <span>{c.field ? c.field.replaceAll('_', ' ').toUpperCase() : 'Statutory Rule'}</span>
                      </span>
                      <span className="text-[10px] uppercase tracking-wider opacity-75">[{c.result}]</span>
                    </div>

                    <p className="italic text-slate-700">"{c.quote}"</p>
                    {c.note && <p className="text-[11px] text-slate-500">Note: {c.note}</p>}
                  </div>
                ))}
              </div>
            ) : (
              <div className="p-3 bg-slate-50 rounded-xl border border-slate-200 text-xs text-slate-600">
                All statutory profile parameters (age, state, category) are satisfied. Check the specialized department conditions above for final eligibility.
              </div>
            )}
          </div>
        </div>

        {/* Modal Footer */}
        <div className="p-4 border-t border-slate-100 bg-slate-50/80 flex flex-wrap items-center justify-between gap-3">
          <a
            href={mySchemeUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center space-x-1.5 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold rounded-xl shadow-sm transition-colors"
          >
            <span>Open on myScheme.gov.in</span>
            <ExternalLink className="w-3.5 h-3.5" />
          </a>

          <button
            onClick={onClose}
            className="px-5 py-2 bg-slate-800 hover:bg-slate-900 text-white text-xs font-semibold rounded-xl transition-colors"
          >
            Close Details
          </button>
        </div>
      </div>
    </div>
  );
};
