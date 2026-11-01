import React from 'react';
import { CatalogStatus } from '../types';
import { ShieldCheck, RotateCcw, Landmark } from 'lucide-react';

interface NavbarProps {
  catalogStatus: CatalogStatus | null;
  onReset: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({ catalogStatus, onReset }) => {
  return (
    <header className="bg-white border-b border-slate-200 sticky top-0 z-30 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-xl bg-blue-600 flex items-center justify-center text-white shadow-md shadow-blue-500/20">
            <Landmark className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="font-extrabold text-lg tracking-tight text-slate-900">JanSeva AI</span>
              <span className="text-[10px] font-bold uppercase tracking-wider bg-blue-50 text-blue-700 px-2 py-0.5 rounded-full border border-blue-200">
                NagrikPulse
              </span>
            </div>
            <p className="text-[11px] text-slate-500 hidden sm:block">Verifiable & Hallucination-Free Government Welfare Discovery</p>
          </div>
        </div>

        <div className="flex items-center space-x-4">
          {catalogStatus && (
            <div className="hidden md:flex items-center space-x-2 text-xs bg-emerald-50 text-emerald-800 px-3 py-1.5 rounded-full border border-emerald-200">
              <ShieldCheck className="w-4 h-4 text-emerald-600 shrink-0" />
              <span>
                <strong className="font-semibold">{catalogStatus.compiled_schemes}</strong> Schemes Verified
              </span>
            </div>
          )}

          <button
            onClick={onReset}
            className="flex items-center space-x-1.5 text-xs font-semibold text-slate-600 hover:text-slate-900 hover:bg-slate-100 px-3 py-1.5 rounded-lg border border-slate-200 transition-colors"
            title="Start New Session"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>Reset</span>
          </button>
        </div>
      </div>
    </header>
  );
};
