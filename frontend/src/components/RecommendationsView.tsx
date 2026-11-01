import React, { useState, useMemo } from 'react';
import { SchemeVerdictResult, MatchResponse } from '../types';
import { SchemeCard } from './SchemeCard';
import { 
  CheckCircle, 
  AlertCircle, 
  Clock, 
  Search, 
  Sparkles, 
  Layers
} from 'lucide-react';

interface RecommendationsViewProps {
  matchResponse: MatchResponse;
  onSelectScheme: (scheme: SchemeVerdictResult) => void;
}

type TabType = 'eligible' | 'needs_more_info' | 'ineligible' | 'closed';

export const RecommendationsView: React.FC<RecommendationsViewProps> = ({
  matchResponse,
  onSelectScheme,
}) => {
  const [activeTab, setActiveTab] = useState<TabType>('eligible');
  const [searchQuery, setSearchQuery] = useState('');
  const [levelFilter, setLevelFilter] = useState<'all' | 'central' | 'state'>('all');

  const { counts, results, unlock_summary } = matchResponse;

  const currentSchemes = useMemo(() => {
    let list: SchemeVerdictResult[] = [];
    if (activeTab === 'eligible') list = results.eligible || [];
    else if (activeTab === 'needs_more_info') list = results.needs_more_info || [];
    else if (activeTab === 'ineligible') list = results.ineligible || [];
    else if (activeTab === 'closed') list = results.closed || [];

    return list.filter((s) => {
      // Search query filter
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        const matchesName = s.name.toLowerCase().includes(q);
        const matchesDept = (s.ministry_or_department || '').toLowerCase().includes(q);
        const matchesBenefit = (s.benefit_snippet || '').toLowerCase().includes(q);
        const matchesDesc = (s.description || '').toLowerCase().includes(q);
        const matchesCat = (s.categories || []).some((c) => c.toLowerCase().includes(q));
        if (!matchesName && !matchesDept && !matchesBenefit && !matchesDesc && !matchesCat) {
          return false;
        }
      }

      // Level filter
      if (levelFilter !== 'all') {
        if (s.level.toLowerCase() !== levelFilter) return false;
      }

      return true;
    });
  }, [activeTab, results, searchQuery, levelFilter]);

  return (
    <div className="space-y-6">
      {/* Dynamic Unlock Banner */}
      {unlock_summary && (
        <div className="bg-zinc-900 text-white rounded-2xl p-4 shadow-sm flex items-center space-x-3.5 animate-fadeIn">
          <div className="bg-white/10 p-2 rounded-xl">
            <Sparkles className="w-5 h-5 text-amber-300" />
          </div>
          <div>
            <h4 className="font-semibold text-xs uppercase tracking-wider text-zinc-300">Progression Update</h4>
            <p className="text-xs text-zinc-100 font-normal mt-0.5">{unlock_summary}</p>
          </div>
        </div>
      )}

      {/* Tabs and Summary Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-zinc-200/80 pb-4">
        {/* Tier Tabs */}
        <div className="flex flex-wrap gap-2">
          {/* Likely Eligible Tab */}
          <button
            onClick={() => setActiveTab('eligible')}
            className={`flex items-center space-x-2 px-3.5 py-2 rounded-xl text-xs font-semibold transition-all ${
              activeTab === 'eligible'
                ? 'bg-zinc-900 text-white shadow-xs'
                : 'bg-zinc-100 text-zinc-700 hover:bg-zinc-200/80'
            }`}
          >
            <CheckCircle className={`w-3.5 h-3.5 ${activeTab === 'eligible' ? 'text-emerald-400' : 'text-emerald-600'}`} />
            <span>Likely Eligible</span>
            <span
              className={`text-[11px] px-2 py-0.5 rounded-full font-bold ${
                activeTab === 'eligible' ? 'bg-white/20 text-white' : 'bg-emerald-100 text-emerald-800'
              }`}
            >
              {counts.eligible}
            </span>
          </button>

          {/* Needs More Info Tab */}
          <button
            onClick={() => setActiveTab('needs_more_info')}
            className={`flex items-center space-x-2 px-3.5 py-2 rounded-xl text-xs font-semibold transition-all ${
              activeTab === 'needs_more_info'
                ? 'bg-zinc-900 text-white shadow-xs'
                : 'bg-zinc-100 text-zinc-700 hover:bg-zinc-200/80'
            }`}
          >
            <AlertCircle className={`w-3.5 h-3.5 ${activeTab === 'needs_more_info' ? 'text-amber-400' : 'text-amber-600'}`} />
            <span>Needs More Info</span>
            <span
              className={`text-[11px] px-2 py-0.5 rounded-full font-bold ${
                activeTab === 'needs_more_info' ? 'bg-white/20 text-white' : 'bg-amber-100 text-amber-800'
              }`}
            >
              {counts.needs_more_info}
            </span>
          </button>

          {/* Ineligible Tab */}
          <button
            onClick={() => setActiveTab('ineligible')}
            className={`flex items-center space-x-2 px-3.5 py-2 rounded-xl text-xs font-semibold transition-all ${
              activeTab === 'ineligible'
                ? 'bg-zinc-900 text-white shadow-xs'
                : 'bg-zinc-100 text-zinc-700 hover:bg-zinc-200/80'
            }`}
          >
            <span>Ineligible</span>
            <span
              className={`text-[11px] px-2 py-0.5 rounded-full font-bold ${
                activeTab === 'ineligible' ? 'bg-white/20 text-white' : 'bg-zinc-200 text-zinc-700'
              }`}
            >
              {counts.ineligible}
            </span>
          </button>

          {/* Closed Tab */}
          <button
            onClick={() => setActiveTab('closed')}
            className={`flex items-center space-x-2 px-3.5 py-2 rounded-xl text-xs font-semibold transition-all ${
              activeTab === 'closed'
                ? 'bg-zinc-900 text-white shadow-xs'
                : 'bg-zinc-100 text-zinc-700 hover:bg-zinc-200/80'
            }`}
          >
            <Clock className="w-3.5 h-3.5 opacity-60" />
            <span>Closed</span>
            <span
              className={`text-[11px] px-2 py-0.5 rounded-full font-bold ${
                activeTab === 'closed' ? 'bg-white/20 text-white' : 'bg-zinc-200 text-zinc-700'
              }`}
            >
              {counts.closed}
            </span>
          </button>
        </div>

        {/* Filter / Search Controls */}
        <div className="flex items-center space-x-2">
          <div className="relative flex-1 sm:w-60">
            <Search className="w-3.5 h-3.5 text-zinc-400 absolute left-3 top-2.5" />
            <input
              type="text"
              placeholder="Search schemes or benefits…"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-9 pr-3 py-1.5 bg-white border border-zinc-200 rounded-xl text-xs text-zinc-800 placeholder-zinc-400 focus:outline-none focus:ring-1 focus:ring-zinc-800"
            />
          </div>

          <select
            value={levelFilter}
            onChange={(e) => setLevelFilter(e.target.value as any)}
            className="bg-white border border-zinc-200 rounded-xl px-2.5 py-1.5 text-xs text-zinc-700 focus:outline-none focus:ring-1 focus:ring-zinc-800"
          >
            <option value="all">All Levels</option>
            <option value="central">Central Gov</option>
            <option value="state">State Gov</option>
          </select>
        </div>
      </div>

      {/* Schemes Grid */}
      {currentSchemes.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {currentSchemes.map((scheme) => (
            <SchemeCard
              key={scheme.slug}
              scheme={scheme}
              onSelect={onSelectScheme}
            />
          ))}
        </div>
      ) : (
        <div className="bg-white border border-dashed border-zinc-200 rounded-3xl p-12 text-center flex flex-col items-center justify-center space-y-3">
          <div className="w-12 h-12 rounded-2xl bg-zinc-100 flex items-center justify-center text-zinc-400">
            <Layers className="w-5 h-5" />
          </div>
          <div>
            <h5 className="font-semibold text-zinc-800 text-sm">No schemes found in this tier</h5>
            <p className="text-xs text-zinc-500 mt-1 max-w-sm">
              {searchQuery
                ? `No schemes matched "${searchQuery}". Clear your search query to see all results.`
                : activeTab === 'eligible'
                ? 'Answer follow-up prompts above to unlock pending schemes waiting for additional details.'
                : 'No schemes currently classified under this tier.'}
            </p>
          </div>
          {searchQuery && (
            <button
              onClick={() => setSearchQuery('')}
              className="text-xs text-zinc-800 font-medium hover:underline"
            >
              Clear search filter
            </button>
          )}
        </div>
      )}
    </div>
  );
};
