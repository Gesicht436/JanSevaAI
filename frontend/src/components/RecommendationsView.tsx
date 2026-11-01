import React, { useState, useMemo } from 'react';
import { SchemeVerdictResult, MatchResponse } from '../types';
import { SchemeCard } from './SchemeCard';
import { 
  CheckCircle, 
  AlertCircle, 
  XCircle, 
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
        const matchesCat = (s.categories || []).some((c) => c.toLowerCase().includes(q));
        if (!matchesName && !matchesDept && !matchesBenefit && !matchesCat) {
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
        <div className="bg-gradient-to-r from-emerald-500 via-teal-600 to-emerald-700 text-white rounded-2xl p-4 shadow-lg flex items-center space-x-3.5 animate-bounce-subtle">
          <div className="bg-white/20 p-2 rounded-xl backdrop-blur-sm">
            <Sparkles className="w-6 h-6 text-yellow-300 animate-spin" />
          </div>
          <div>
            <h4 className="font-bold text-sm tracking-wide">Eligibility Progression Update</h4>
            <p className="text-xs text-emerald-100 font-medium">{unlock_summary}</p>
          </div>
        </div>
      )}

      {/* Tabs and Summary Counters */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200 pb-3">
        <div className="flex flex-wrap gap-2">
          {/* Likely Eligible Tab */}
          <button
            onClick={() => setActiveTab('eligible')}
            className={`flex items-center space-x-2 px-4 py-2.5 rounded-xl font-medium text-xs sm:text-sm transition-all ${
              activeTab === 'eligible'
                ? 'bg-emerald-600 text-white shadow-md'
                : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
            }`}
          >
            <CheckCircle className="w-4 h-4" />
            <span>Likely Eligible</span>
            <span
              className={`text-xs px-2 py-0.5 rounded-full font-bold ${
                activeTab === 'eligible' ? 'bg-white/20 text-white' : 'bg-emerald-100 text-emerald-800'
              }`}
            >
              {counts.eligible}
            </span>
          </button>

          {/* Needs More Info Tab */}
          <button
            onClick={() => setActiveTab('needs_more_info')}
            className={`flex items-center space-x-2 px-4 py-2.5 rounded-xl font-medium text-xs sm:text-sm transition-all ${
              activeTab === 'needs_more_info'
                ? 'bg-amber-600 text-white shadow-md'
                : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
            }`}
          >
            <AlertCircle className="w-4 h-4" />
            <span>Needs More Info</span>
            <span
              className={`text-xs px-2 py-0.5 rounded-full font-bold ${
                activeTab === 'needs_more_info' ? 'bg-white/20 text-white' : 'bg-amber-100 text-amber-800'
              }`}
            >
              {counts.needs_more_info}
            </span>
          </button>

          {/* Ineligible Tab */}
          <button
            onClick={() => setActiveTab('ineligible')}
            className={`flex items-center space-x-2 px-4 py-2.5 rounded-xl font-medium text-xs sm:text-sm transition-all ${
              activeTab === 'ineligible'
                ? 'bg-rose-600 text-white shadow-md'
                : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
            }`}
          >
            <XCircle className="w-4 h-4" />
            <span>Ineligible</span>
            <span
              className={`text-xs px-2 py-0.5 rounded-full font-bold ${
                activeTab === 'ineligible' ? 'bg-white/20 text-white' : 'bg-rose-100 text-rose-800'
              }`}
            >
              {counts.ineligible}
            </span>
          </button>

          {/* Closed Tab */}
          <button
            onClick={() => setActiveTab('closed')}
            className={`flex items-center space-x-2 px-4 py-2.5 rounded-xl font-medium text-xs sm:text-sm transition-all ${
              activeTab === 'closed'
                ? 'bg-slate-700 text-white shadow-md'
                : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
            }`}
          >
            <Clock className="w-4 h-4" />
            <span>Past / Closed</span>
            <span
              className={`text-xs px-2 py-0.5 rounded-full font-bold ${
                activeTab === 'closed' ? 'bg-white/20 text-white' : 'bg-slate-200 text-slate-800'
              }`}
            >
              {counts.closed}
            </span>
          </button>
        </div>

        {/* Filter / Search Controls */}
        <div className="flex items-center space-x-2">
          <div className="relative flex-1 sm:w-56">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
            <input
              type="text"
              placeholder="Filter schemes..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-9 pr-3 py-1.5 bg-slate-50 border border-slate-200 rounded-xl text-xs sm:text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <select
            value={levelFilter}
            onChange={(e) => setLevelFilter(e.target.value as any)}
            className="bg-slate-50 border border-slate-200 rounded-xl px-2.5 py-1.5 text-xs sm:text-sm text-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
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
        <div className="bg-slate-50 border border-dashed border-slate-300 rounded-2xl p-10 text-center flex flex-col items-center justify-center space-y-3">
          <div className="w-12 h-12 rounded-full bg-slate-100 flex items-center justify-center text-slate-400">
            <Layers className="w-6 h-6" />
          </div>
          <div>
            <h5 className="font-semibold text-slate-700 text-sm">No schemes found in this category</h5>
            <p className="text-xs text-slate-500 mt-1 max-w-sm">
              {searchQuery
                ? `No schemes matched "${searchQuery}". Try clearing search filters.`
                : activeTab === 'eligible'
                ? 'Answer follow-up questions above to unlock schemes currently pending more information.'
                : 'No schemes currently classified under this tier.'}
            </p>
          </div>
          {searchQuery && (
            <button
              onClick={() => setSearchQuery('')}
              className="text-xs text-blue-600 hover:underline font-medium"
            >
              Clear filter
            </button>
          )}
        </div>
      )}
    </div>
  );
};
