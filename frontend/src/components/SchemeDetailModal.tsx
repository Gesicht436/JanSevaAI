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

    if (!profile || !profile.confirmed) {
      setIsLoading(false);
      setExplanation(
        `Profile confirmation is required to view official grounded eligibility explanations. Under this scheme: ${scheme.description || scheme.benefit_snippet}`
      );
      return;
    }

    explainScheme(scheme.slug, profile)
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

  const automatedCriteria = (scheme.criteria_results || []).filter((c) => !c.is_specialized && c.field);
  const specializedCriteriaQuotes = scheme.specialized_criteria || [];

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-black/40 backdrop-blur-md flex items-center justify-center p-4">
      <div className="bg-white rounded-3xl max-w-3xl w-full max-h-[92vh] flex flex-col shadow-2xl border border-zinc-200/90 overflow-hidden animate-fadeIn">
        
        {/* Modal Header */}
        <div className="p-6 sm:p-8 border-b border-zinc-100 flex items-start justify-between bg-zinc-50/50">
          <div className="space-y-2 pr-4">
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-[11px] font-semibold uppercase tracking-wider bg-zinc-100 text-zinc-700 px-2.5 py-0.5 rounded-full border border-zinc-200">
                {scheme.level} Scheme
              </span>
              <span className="text-[11px] font-semibold bg-emerald-50 text-emerald-800 px-2.5 py-0.5 rounded-full border border-emerald-200 flex items-center space-x-1">
                <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
                <span>{(scheme.verified_ratio * 100).toFixed(0)}% Verifiable</span>
              </span>
              {scheme.requires_manual_review && (
                <span className="text-[11px] font-semibold bg-amber-50 text-amber-800 px-2.5 py-0.5 rounded-full border border-amber-200 flex items-center space-x-1">
                  <AlertTriangle className="w-3.5 h-3.5 text-amber-600" />
                  <span>Department Review Required</span>
                </span>
              )}
              <a
                href={mySchemeUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center space-x-1 text-xs font-semibold text-zinc-700 hover:text-black bg-white hover:bg-zinc-100 border border-zinc-200 px-3 py-0.5 rounded-full transition-colors shadow-2xs"
                title="Open official scheme page on myScheme.gov.in"
              >
                <span>myScheme.gov.in</span>
                <ExternalLink className="w-3.5 h-3.5 text-zinc-400" />
              </a>
            </div>
            <h2 className="text-xl sm:text-2xl font-bold tracking-tight text-zinc-900 leading-snug">{scheme.name}</h2>
            <p className="text-xs text-zinc-500 font-normal">{scheme.ministry_or_department || 'Government of India'}</p>
          </div>

          <button
            onClick={onClose}
            className="p-2 text-zinc-400 hover:text-zinc-900 hover:bg-zinc-200/60 rounded-full transition-colors flex-shrink-0"
            title="Close dialog"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-6 sm:p-8 overflow-y-auto space-y-6 text-sm">
          
          {/* Grounded AI Explanation */}
          <div className="p-5 rounded-2xl bg-zinc-50 border border-zinc-200/80 space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2 text-xs font-semibold text-zinc-800 uppercase tracking-wide">
                <Sparkles className="w-4 h-4 text-zinc-700" />
                <span>Grounded Plain-Language Explanation</span>
              </div>

              <button
                type="button"
                onClick={toggleAudio}
                className={`flex items-center space-x-1 px-3 py-1 text-xs font-medium rounded-xl transition-all ${
                  isPlaying ? 'bg-zinc-900 text-white shadow-xs' : 'bg-white text-zinc-700 border border-zinc-200 hover:bg-zinc-100'
                }`}
              >
                {isPlaying ? <VolumeX className="w-3.5 h-3.5" /> : <Volume2 className="w-3.5 h-3.5" />}
                <span>{isPlaying ? 'Pause' : 'Listen'}</span>
              </button>
            </div>

            <p className="text-zinc-700 leading-relaxed text-xs sm:text-sm font-normal">
              {isLoading ? 'Synthesizing verified citations…' : explanation}
            </p>

            {citations.length > 0 && (
              <div className="pt-2 flex flex-wrap gap-1.5 items-center">
                <span className="text-[10px] font-semibold uppercase text-zinc-500">Official Citations:</span>
                {citations.map((cite, idx) => (
                  <span key={idx} className="text-[10px] font-mono bg-white text-zinc-700 px-2 py-0.5 rounded-md border border-zinc-200">
                    {cite}
                  </span>
                ))}
              </div>
            )}
          </div>

          {/* Scheme Description & Overview */}
          <div className="space-y-2">
            <h4 className="text-xs font-semibold uppercase tracking-wider text-zinc-400 flex items-center space-x-1.5">
              <Info className="w-3.5 h-3.5 text-zinc-500" />
              <span>Scheme Description & Overview</span>
            </h4>
            <div className="p-4 bg-zinc-50/70 rounded-2xl border border-zinc-200/80 text-xs sm:text-sm text-zinc-700 leading-relaxed font-normal">
              {scheme.description || scheme.benefit_snippet || 'No detailed description available in catalog.'}
            </div>
          </div>

          {/* Benefits Overview */}
          <div className="space-y-2">
            <h4 className="text-xs font-semibold uppercase tracking-wider text-zinc-400">Benefit Summary</h4>
            <div className="p-4 bg-zinc-50/70 rounded-2xl border border-zinc-200/80 text-xs text-zinc-700 leading-relaxed font-normal">
              {scheme.benefit_snippet || 'Direct benefit transfers, subsidies, interest subvention, or capacity building.'}
            </div>
          </div>

          {/* Section: Required Documents Checklist */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <h4 className="text-xs font-semibold uppercase tracking-wider text-zinc-700 flex items-center space-x-1.5">
                <FileText className="w-4 h-4 text-zinc-600" />
                <span>Required Documents ({scheme.required_documents?.length || 0})</span>
              </h4>
              <span className="text-[11px] text-zinc-400 font-normal">Keep ready before applying</span>
            </div>

            {scheme.required_documents && scheme.required_documents.length > 0 ? (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                {scheme.required_documents.map((docItem, idx) => {
                  const doc = typeof docItem === 'string' ? { type: null, text: docItem } : docItem;
                  const docType = doc.type ?? null;
                  const isHeld = docType ? (profile?.documents_held || []).includes(docType) : false;

                  return (
                    <div
                      key={idx}
                      className={`flex flex-col p-3 rounded-xl border text-xs transition-colors space-y-1.5 ${
                        isHeld
                          ? 'bg-emerald-50/50 border-emerald-200 text-emerald-950'
                          : docType
                          ? 'bg-amber-50/40 border-amber-200 text-amber-950'
                          : 'bg-zinc-50 border-zinc-200/90 text-zinc-800'
                      }`}
                    >
                      <div className="flex items-start justify-between gap-2">
                        <div className="flex items-start space-x-2">
                          {isHeld ? (
                            <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0 mt-0.5" />
                          ) : docType ? (
                            <AlertCircle className="w-4 h-4 text-amber-600 flex-shrink-0 mt-0.5" />
                          ) : (
                            <HelpCircle className="w-4 h-4 text-zinc-500 flex-shrink-0 mt-0.5" />
                          )}
                          <span className="leading-snug font-medium">{doc.text}</span>
                        </div>
                        <span
                          className={`text-[9px] uppercase tracking-wider font-semibold px-1.5 py-0.5 rounded shrink-0 ${
                            isHeld
                              ? 'bg-emerald-100 text-emerald-800'
                              : docType
                              ? 'bg-amber-100 text-amber-800'
                              : 'bg-zinc-200/70 text-zinc-600'
                          }`}
                        >
                          {isHeld ? 'Have' : docType ? 'Needs Confirmation' : 'Unclassified'}
                        </span>
                      </div>
                      {!docType && (
                        <p className="text-[10px] text-zinc-500 italic pl-6">
                          Specific document format evaluated by nodal department at application.
                        </p>
                      )}
                    </div>
                  );
                })}
              </div>
            ) : (
              <div className="p-3 bg-zinc-50 rounded-xl border border-dashed border-zinc-200 text-xs text-zinc-400 italic">
                No specific mandatory documents listed in the official catalog for this scheme.
              </div>
            )}
          </div>

          {/* Section: Specialized & Department-Evaluated Eligibility Criteria */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <h4 className="text-xs font-semibold uppercase tracking-wider text-zinc-700 flex items-center space-x-1.5">
                <Building2 className="w-4 h-4 text-amber-600" />
                <span>Department-Evaluated & Specialized Criteria ({specializedCriteriaQuotes.length})</span>
              </h4>
              <span className="text-[10px] font-semibold uppercase bg-amber-50 text-amber-800 px-2.5 py-0.5 rounded-full border border-amber-200">
                Self-Verification Required
              </span>
            </div>

            <div className="p-4 bg-amber-50/60 rounded-2xl border border-amber-200/80 space-y-3">
              <div className="flex items-start space-x-2.5">
                <HelpCircle className="w-4 h-4 text-amber-700 flex-shrink-0 mt-0.5" />
                <p className="text-xs text-amber-950 leading-relaxed font-normal">
                  <strong>Department Prerequisite Notice:</strong> Our automated AI engine verifies statutory baseline parameters (age limits, state residency, education level, category, and income). However, the specific conditions below cannot be evaluated automatically (e.g. specialized engineering credentials, years of domain expertise, departmental registrations, or subjective committee evaluations). <em>These depend directly on the applicant and are evaluated by the administering nodal department at the time of application.</em>
                </p>
              </div>

              {specializedCriteriaQuotes.length > 0 ? (
                <div className="space-y-2 pt-1">
                  {specializedCriteriaQuotes.map((quote, idx) => (
                    <div
                      key={idx}
                      className="p-3 bg-white rounded-xl border border-amber-200/90 shadow-2xs flex items-start space-x-2.5"
                    >
                      <span className="w-5 h-5 rounded-full bg-amber-100 text-amber-900 flex items-center justify-center font-bold text-[10px] flex-shrink-0 mt-0.5">
                        {idx + 1}
                      </span>
                      <div className="flex-1">
                        <p className="text-xs text-zinc-800 italic font-medium leading-relaxed">"{quote}"</p>
                        <span className="inline-block text-[10px] text-amber-800 font-medium mt-1">
                          Evaluated by nodal department / scheme authority
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-xs text-zinc-400 italic pl-6">
                  No additional specialized department prerequisites required for this scheme.
                </p>
              )}
            </div>
          </div>

          {/* Section: Automated Statutory Criteria Evaluation */}
          <div className="space-y-2">
            <h4 className="text-xs font-semibold uppercase tracking-wider text-zinc-400">
              Automated Statutory Eligibility Checks (Evaluated by JanSeva AI)
            </h4>
            {automatedCriteria.length > 0 ? (
              <div className="space-y-2">
                {automatedCriteria.map((c, i) => (
                  <div
                    key={i}
                    className={`p-3 rounded-xl border text-xs space-y-1 ${
                      c.result === 'pass'
                        ? 'bg-emerald-50/50 border-emerald-200 text-emerald-950'
                        : c.result === 'fail'
                        ? 'bg-zinc-100 border-zinc-200 text-zinc-700'
                        : 'bg-amber-50/50 border-amber-200 text-amber-950'
                    }`}
                  >
                    <div className="flex items-center justify-between font-semibold">
                      <span className="flex items-center space-x-1.5">
                        {c.result === 'pass' && <Check className="w-3.5 h-3.5 text-emerald-600" />}
                        {c.result === 'fail' && <AlertTriangle className="w-3.5 h-3.5 text-zinc-500" />}
                        {c.result === 'unknown' && <AlertCircle className="w-3.5 h-3.5 text-amber-600" />}
                        <span>{c.field ? c.field.replaceAll('_', ' ').toUpperCase() : 'Statutory Rule'}</span>
                      </span>
                      <span className="text-[10px] uppercase tracking-wider opacity-60">[{c.result}]</span>
                    </div>

                    <p className="italic text-zinc-700 font-normal">"{c.quote}"</p>
                    {c.note && <p className="text-[11px] text-zinc-500 font-normal">Note: {c.note}</p>}
                  </div>
                ))}
              </div>
            ) : (
              <div className="p-3 bg-zinc-50 rounded-xl border border-zinc-200 text-xs text-zinc-600">
                All statutory profile parameters (age, state, category) are satisfied. Check the specialized department conditions above for final eligibility.
              </div>
            )}
          </div>
        </div>

        {/* Modal Footer */}
        <div className="p-5 sm:p-6 border-t border-zinc-100 bg-zinc-50/80 flex flex-wrap items-center justify-between gap-3">
          <a
            href={mySchemeUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center space-x-1.5 px-4 py-2 bg-zinc-900 hover:bg-zinc-800 text-white text-xs font-semibold rounded-xl shadow-xs transition-all active:scale-[0.98]"
          >
            <span>Open on myScheme.gov.in</span>
            <ExternalLink className="w-3.5 h-3.5" />
          </a>

          <button
            onClick={onClose}
            className="px-5 py-2 bg-zinc-100 hover:bg-zinc-200 text-zinc-800 text-xs font-semibold rounded-xl transition-colors"
          >
            Close Details
          </button>
        </div>
      </div>
    </div>
  );
};
