import React from 'react';
import { CatalogStatus } from '../types';
import { ShieldCheck, RotateCcw, Landmark } from 'lucide-react';

interface NavbarProps {
  catalogStatus: CatalogStatus | null;
  onReset: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({ catalogStatus, onReset }) => {
  return (
    <header className="sticky top-0 z-40 bg-white/80 backdrop-blur-xl border-b border-zinc-200/80 transition-all">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Brand */}
        <div className="flex items-center space-x-3">
          <div className="w-9 h-9 rounded-xl bg-zinc-900 flex items-center justify-center text-white shadow-xs">
            <Landmark className="w-4 h-4 text-zinc-100" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="font-semibold text-base tracking-tight text-zinc-900">JanSeva AI</span>
              <span className="text-[10px] font-medium tracking-wide uppercase px-2 py-0.5 rounded-full bg-zinc-100 text-zinc-600 border border-zinc-200/60">
                NagrikPulse
              </span>
            </div>
            <p className="text-[11px] text-zinc-400 hidden sm:block tracking-normal font-normal">
              Verifiable & Zero-Hallucination Welfare Discovery
            </p>
          </div>
        </div>

        {/* Right Status & Actions */}
        <div className="flex items-center space-x-3">
          {catalogStatus && (
            <div className="hidden sm:flex items-center space-x-1.5 text-xs text-zinc-600 bg-zinc-100/80 px-3 py-1 rounded-full border border-zinc-200/60">
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
              <span>
                <strong className="font-semibold text-zinc-900">{catalogStatus.compiled_schemes}</strong> Verified Schemes
              </span>
            </div>
          )}

          <button
            onClick={onReset}
            className="flex items-center space-x-1.5 text-xs font-medium text-zinc-600 hover:text-zinc-900 hover:bg-zinc-100 px-3 py-1.5 rounded-xl border border-zinc-200/80 transition-all active:scale-[0.98]"
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
