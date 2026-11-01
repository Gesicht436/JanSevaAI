import React, { useState, useEffect } from 'react';
import { CitizenProfile, MatchResponse, SchemeVerdictResult, CatalogStatus } from './types';
import { extractProfile, extractProfileAudio, matchSchemes, getCatalogStatus } from './services/api';
import { Navbar } from './components/Navbar';
import { ChatIntake } from './components/ChatIntake';
import { ProfileReviewCard } from './components/ProfileReviewCard';
import { RecommendationsView } from './components/RecommendationsView';
import { FollowUpPrompt } from './components/FollowUpPrompt';
import { SchemeDetailModal } from './components/SchemeDetailModal';
import { 
  ArrowLeft, 
  RefreshCw, 
  AlertTriangle,
  Lightbulb
} from 'lucide-react';

const INITIAL_PROFILE: CitizenProfile = {
  confirmed: false,
};

export const App: React.FC = () => {
  const [profile, setProfile] = useState<CitizenProfile>(INITIAL_PROFILE);
  const [confidenceByField, setConfidenceByField] = useState<Record<string, number>>({});
  const [clarificationPrompt, setClarificationPrompt] = useState<string | null>(null);
  const [suggestedFields, setSuggestedFields] = useState<string[]>([]);
  const [matchResponse, setMatchResponse] = useState<MatchResponse | null>(null);
  const [selectedScheme, setSelectedScheme] = useState<SchemeVerdictResult | null>(null);
  const [activeStep, setActiveStep] = useState<'intake' | 'results'>('intake');
  const [isLoading, setIsLoading] = useState(false);
  const [catalogStatus, setCatalogStatus] = useState<CatalogStatus | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [dismissFollowups, setDismissFollowups] = useState(false);

  const handleReset = () => {
    setProfile(INITIAL_PROFILE);
    setConfidenceByField({});
    setClarificationPrompt(null);
    setSuggestedFields([]);
    setMatchResponse(null);
    setSelectedScheme(null);
    setActiveStep('intake');
    setErrorMessage(null);
  };

  // Fetch catalog status on mount
  useEffect(() => {
    getCatalogStatus()
      .then((status) => setCatalogStatus(status))
      .catch((err) => console.warn('Could not fetch catalog status:', err));
  }, []);

  // Handle profile extraction from chat or voice
  const handleExtractText = async (text: string) => {
    setIsLoading(true);
    setErrorMessage(null);
    try {
      const res = await extractProfile(text, profile);
      setProfile(res.profile);
      setConfidenceByField(res.confidence_by_field || {});
      setClarificationPrompt(res.clarification_prompt || null);
      setSuggestedFields(res.suggested_fields || []);
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to parse your input.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleExtractAudio = async (blob: Blob) => {
    setIsLoading(true);
    setErrorMessage(null);
    try {
      const res = await extractProfileAudio(blob, profile);
      setProfile(res.profile);
      setConfidenceByField(res.confidence_by_field || {});
      setClarificationPrompt(res.clarification_prompt || null);
      setSuggestedFields(res.suggested_fields || []);
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to process voice recording.');
    } finally {
      setIsLoading(false);
    }
  };

  // Perform scheme matching
  const handleFindSchemes = async (overrideProfile?: CitizenProfile) => {
    const prof = overrideProfile || profile;
    setIsLoading(true);
    setErrorMessage(null);
    setDismissFollowups(false);

    try {
      // Gather previously unlocked slugs if any
      const prevSlugs = matchResponse?.results.eligible.map((s) => s.slug) || [];
      const res = await matchSchemes(prof, prevSlugs);
      setMatchResponse(res);
      setActiveStep('results');
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to match schemes. Please check your network or server status.');
    } finally {
      setIsLoading(false);
    }
  };

  // Handle answering follow-up questions
  const handleFollowUpAnswer = async (field: string, value: any) => {
    const updated = { ...profile, [field]: value };
    setProfile(updated);
    await handleFindSchemes(updated);
  };

  // Demo profile presets
  const handleLoadDemo = (preset: 'it_loan' | 'farmer_subsidy' | 'student_scholarship') => {
    let demo: CitizenProfile = { confirmed: true };
    if (preset === 'it_loan') {
      demo = {
        name: 'Aarav Patel',
        age: 26,
        gender: 'male',
        marital_status: 'never_married',
        state_ut: 'Maharashtra',
        residence: 'urban',
        qualification: 'graduate',
        is_student: false,
        employment_status: 'employed',
        has_work_experience: true,
        years_of_experience: 3,
        current_sector: 'it_tech',
        aspiring_sector: 'it_tech',
        benefit_intent: 'credit_loan',
        annual_family_income_inr: 600000,
        confirmed: true,
      };
    } else if (preset === 'farmer_subsidy') {
      demo = {
        name: 'Rameshwar Yadav',
        age: 48,
        gender: 'male',
        marital_status: 'married',
        state_ut: 'Uttar Pradesh',
        residence: 'rural',
        qualification: '10th_pass',
        is_student: false,
        employment_status: 'self_employed',
        has_work_experience: true,
        years_of_experience: 25,
        current_sector: 'agriculture',
        is_farmer: true,
        land_holding_acres: 3.5,
        caste_category: 'obc',
        is_bpl: true,
        annual_family_income_inr: 120000,
        confirmed: true,
      };
    } else if (preset === 'student_scholarship') {
      demo = {
        name: 'Priya Sharma',
        age: 20,
        gender: 'female',
        marital_status: 'never_married',
        state_ut: 'Delhi',
        residence: 'urban',
        qualification: '12th_pass',
        is_student: true,
        employment_status: 'unemployed',
        has_work_experience: false,
        benefit_intent: 'scholarship',
        caste_category: 'general',
        annual_family_income_inr: 240000,
        confirmed: true,
      };
    }

    setProfile(demo);
    handleFindSchemes(demo);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50/20 to-slate-100 text-slate-800 flex flex-col font-sans">
      <Navbar catalogStatus={catalogStatus} onReset={handleReset} />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
        {/* Error notification banner */}
        {errorMessage && (
          <div className="bg-rose-50 border border-rose-300 text-rose-800 rounded-2xl p-4 flex items-center justify-between shadow-sm animate-fadeIn">
            <div className="flex items-center space-x-3">
              <AlertTriangle className="w-5 h-5 text-rose-600 flex-shrink-0" />
              <p className="text-sm font-medium">{errorMessage}</p>
            </div>
            <button
              onClick={() => setErrorMessage(null)}
              className="text-xs font-bold text-rose-700 hover:text-rose-900 underline ml-4"
            >
              Dismiss
            </button>
          </div>
        )}

        {/* Sample Persona autofill shortcuts */}
        <div className="flex flex-wrap items-center justify-between gap-3 bg-white/70 backdrop-blur-sm border border-slate-200/80 rounded-2xl px-4 py-2.5 text-xs text-slate-600 shadow-sm">
          <div className="flex items-center space-x-2">
            <Lightbulb className="w-4 h-4 text-amber-500" />
            <span className="font-semibold text-slate-700">Sample Personas (Pre-fill Form):</span>
            <span className="hidden sm:inline text-slate-400">· Live SQLite & Kleene Engine Evaluation</span>
          </div>
          <div className="flex flex-wrap gap-2">
            <button
              onClick={() => handleLoadDemo('it_loan')}
              className="px-3 py-1 rounded-lg bg-blue-50 hover:bg-blue-100 text-blue-700 font-medium border border-blue-200 transition-colors"
              title="Populates form fields for IT Professional persona and evaluates against live backend database"
            >
              IT Professional (26y, Loan)
            </button>
            <button
              onClick={() => handleLoadDemo('farmer_subsidy')}
              className="px-3 py-1 rounded-lg bg-emerald-50 hover:bg-emerald-100 text-emerald-700 font-medium border border-emerald-200 transition-colors"
              title="Populates form fields for Farmer persona and evaluates against live backend database"
            >
              Rural Farmer (OBC, BPL)
            </button>
            <button
              onClick={() => handleLoadDemo('student_scholarship')}
              className="px-3 py-1 rounded-lg bg-purple-50 hover:bg-purple-100 text-purple-700 font-medium border border-purple-200 transition-colors"
              title="Populates form fields for Student persona and evaluates against live backend database"
            >
              Female Student (20y, Delhi)
            </button>
          </div>
        </div>

        {/* View Switch / Navigation Bar */}
        {matchResponse && (
          <div className="flex items-center justify-between bg-white rounded-2xl px-5 py-3 border border-slate-200 shadow-sm">
            <div className="flex items-center space-x-3">
              {activeStep === 'results' ? (
                <button
                  onClick={() => setActiveStep('intake')}
                  className="flex items-center space-x-1.5 text-xs sm:text-sm font-semibold text-slate-600 hover:text-blue-600 transition-colors"
                >
                  <ArrowLeft className="w-4 h-4" />
                  <span>Edit Profile / Intake</span>
                </button>
              ) : (
                <button
                  onClick={() => setActiveStep('results')}
                  className="flex items-center space-x-1.5 text-xs sm:text-sm font-semibold text-blue-600 hover:text-blue-800 transition-colors"
                >
                  <span>View Recommendations ({matchResponse.counts.eligible} Likely Eligible)</span>
                </button>
              )}
            </div>

            <div className="flex items-center space-x-3">
              <button
                onClick={() => handleFindSchemes()}
                disabled={isLoading}
                className="flex items-center space-x-1.5 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white font-medium text-xs sm:text-sm px-4 py-2 rounded-xl transition-all shadow-sm"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
                <span>Re-evaluate</span>
              </button>
            </div>
          </div>
        )}

        {/* Main Content Area */}
        {activeStep === 'intake' ? (
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
            {/* Left Column: Natural Language Chat Intake & Voice */}
            <div className="lg:col-span-7 space-y-6">
              <ChatIntake
                onExtractText={handleExtractText}
                onExtractAudio={handleExtractAudio}
                isLoading={isLoading}
                clarificationPrompt={clarificationPrompt}
                suggestedFields={suggestedFields}
                currentProfile={profile.age ? profile : null}
              />
            </div>

            {/* Right Column: Structured Profile Review Card */}
            <div className="lg:col-span-5 space-y-6">
              <ProfileReviewCard
                profile={profile}
                confidence={confidenceByField}
                onChange={setProfile}
                onConfirmAndMatch={(p) => {
                  setProfile(p);
                  handleFindSchemes(p);
                }}
                isLoading={isLoading}
              />
            </div>
          </div>
        ) : (
          <div className="space-y-6">
            {/* Dynamic Follow-Up Prompt to unlock more schemes */}
            {matchResponse && !dismissFollowups && matchResponse.followup_fields.length > 0 && (
              <FollowUpPrompt
                fields={matchResponse.followup_fields}
                profile={profile}
                onUpdateField={handleFollowUpAnswer}
                onDismiss={() => setDismissFollowups(true)}
              />
            )}

            {/* Recommendations Grid View */}
            {matchResponse && (
              <RecommendationsView
                matchResponse={matchResponse}
                onSelectScheme={(scheme) => setSelectedScheme(scheme)}
              />
            )}
          </div>
        )}
      </main>

      {/* Scheme Detail Inspection Modal */}
      {selectedScheme && (
        <SchemeDetailModal
          scheme={selectedScheme}
          profile={profile}
          onClose={() => setSelectedScheme(null)}
        />
      )}

      {/* Footer */}
      <footer className="mt-auto border-t border-slate-200/80 bg-white/50 backdrop-blur-sm py-4 text-center text-xs text-slate-500">
        <p>JanSevaAI &copy; {new Date().getFullYear()} — Evidence-backed, deterministic & contextual civic intelligence.</p>
      </footer>
    </div>
  );
};

export default App;
