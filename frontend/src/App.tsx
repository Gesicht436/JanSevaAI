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
  Lightbulb,
  MessageSquare,
  UserCheck,
  Award
} from 'lucide-react';

const INITIAL_PROFILE: CitizenProfile = {
  confirmed: false,
};

type Step = 'intake' | 'review' | 'results';

export const App: React.FC = () => {
  const [profile, setProfile] = useState<CitizenProfile>(INITIAL_PROFILE);
  const [confidenceByField, setConfidenceByField] = useState<Record<string, number>>({});
  const [clarificationPrompt, setClarificationPrompt] = useState<string | null>(null);
  const [suggestedFields, setSuggestedFields] = useState<string[]>([]);
  const [matchResponse, setMatchResponse] = useState<MatchResponse | null>(null);
  const [selectedScheme, setSelectedScheme] = useState<SchemeVerdictResult | null>(null);
  const [activeStep, setActiveStep] = useState<Step>('intake');
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

  useEffect(() => {
    getCatalogStatus()
      .then((status) => setCatalogStatus(status))
      .catch((err) => console.warn('Could not fetch catalog status:', err));
  }, []);

  const handleExtractText = async (text: string) => {
    setIsLoading(true);
    setErrorMessage(null);
    try {
      const res = await extractProfile(text, profile);
      setProfile(res.profile);
      setConfidenceByField(res.confidence_by_field || {});
      setClarificationPrompt(res.clarification_prompt || null);
      setSuggestedFields(res.suggested_fields || []);
      // Step-by-Step: transition to fact review
      setActiveStep('review');
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
      // Step-by-Step: transition to fact review
      setActiveStep('review');
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to process voice recording.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleFindSchemes = async (overrideProfile?: CitizenProfile) => {
    const prof = overrideProfile || profile;
    setIsLoading(true);
    setErrorMessage(null);
    setDismissFollowups(false);

    try {
      const prevSlugs = matchResponse?.results.eligible.map((s) => s.slug) || [];
      const res = await matchSchemes(prof, prevSlugs);
      setMatchResponse(res);
      setActiveStep('results');
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to match schemes. Please verify your facts or network.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleFollowUpAnswer = async (field: string, value: any) => {
    const updated = { ...profile, [field]: value };
    setProfile(updated);
    await handleFindSchemes(updated);
  };

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
    <div className="min-h-screen bg-zinc-50 text-zinc-900 flex flex-col font-sans selection:bg-zinc-900 selection:text-white">
      <Navbar catalogStatus={catalogStatus} onReset={handleReset} />

      <main className="flex-1 max-w-6xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        
        {/* Error notification banner */}
        {errorMessage && (
          <div className="bg-zinc-900 text-white rounded-2xl p-4 flex items-center justify-between shadow-sm animate-fadeIn">
            <div className="flex items-center space-x-3">
              <AlertTriangle className="w-5 h-5 text-amber-400 shrink-0" />
              <p className="text-xs sm:text-sm font-medium">{errorMessage}</p>
            </div>
            <button
              onClick={() => setErrorMessage(null)}
              className="text-xs text-zinc-300 hover:text-white underline ml-4 font-semibold"
            >
              Dismiss
            </button>
          </div>
        )}

        {/* Apple-style Step Progress Stepper */}
        <nav aria-label="Workflow Steps" className="max-w-2xl mx-auto">
          <div className="flex items-center justify-between p-1.5 bg-zinc-100/80 rounded-2xl border border-zinc-200/60 text-xs">
            {/* Step 1 */}
            <button
              onClick={() => setActiveStep('intake')}
              className={`flex-1 flex items-center justify-center space-x-1.5 py-2 px-3 rounded-xl font-medium transition-all ${
                activeStep === 'intake'
                  ? 'bg-white text-zinc-900 shadow-xs font-semibold'
                  : 'text-zinc-500 hover:text-zinc-900'
              }`}
            >
              <MessageSquare className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">1.</span>
              <span>Conversational Intake</span>
            </button>

            {/* Step 2 */}
            <button
              onClick={() => setActiveStep('review')}
              className={`flex-1 flex items-center justify-center space-x-1.5 py-2 px-3 rounded-xl font-medium transition-all ${
                activeStep === 'review'
                  ? 'bg-white text-zinc-900 shadow-xs font-semibold'
                  : 'text-zinc-500 hover:text-zinc-900'
              }`}
            >
              <UserCheck className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">2.</span>
              <span>Review Your Extracted Profile</span>
            </button>

            {/* Step 3 */}
            <button
              onClick={() => {
                if (matchResponse) setActiveStep('results');
              }}
              disabled={!matchResponse}
              className={`flex-1 flex items-center justify-center space-x-1.5 py-2 px-3 rounded-xl font-medium transition-all ${
                activeStep === 'results'
                  ? 'bg-white text-zinc-900 shadow-xs font-semibold'
                  : matchResponse
                  ? 'text-zinc-500 hover:text-zinc-900'
                  : 'text-zinc-300 cursor-not-allowed'
              }`}
            >
              <Award className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">3.</span>
              <span>Recommendations</span>
              {matchResponse && (
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
              )}
            </button>
          </div>
        </nav>

        {/* Sample Persona autofill shortcuts */}
        <div className="flex flex-wrap items-center justify-between gap-3 bg-white p-3.5 rounded-2xl border border-zinc-200/80 shadow-2xs text-xs text-zinc-500">
          <div className="flex items-center space-x-2">
            <Lightbulb className="w-4 h-4 text-zinc-400" />
            <span className="font-medium text-zinc-700">Sample Personas:</span>
            <span className="hidden sm:inline text-zinc-400">Pre-fill facts & test matching</span>
          </div>
          <div className="flex flex-wrap gap-1.5">
            <button
              onClick={() => handleLoadDemo('it_loan')}
              className="px-3 py-1 rounded-xl bg-zinc-50 hover:bg-zinc-100 text-zinc-700 font-medium border border-zinc-200 transition-colors"
              title="Populates form fields for IT Professional persona"
            >
              IT Professional (26y, Loan)
            </button>
            <button
              onClick={() => handleLoadDemo('farmer_subsidy')}
              className="px-3 py-1 rounded-xl bg-zinc-50 hover:bg-zinc-100 text-zinc-700 font-medium border border-zinc-200 transition-colors"
              title="Populates form fields for Rural Farmer persona"
            >
              Rural Farmer (OBC, BPL)
            </button>
            <button
              onClick={() => handleLoadDemo('student_scholarship')}
              className="px-3 py-1 rounded-xl bg-zinc-50 hover:bg-zinc-100 text-zinc-700 font-medium border border-zinc-200 transition-colors"
              title="Populates form fields for Student persona"
            >
              Female Student (20y, Delhi)
            </button>
          </div>
        </div>

        {/* STEP-BY-STEP WORKSPACE CONTENT */}
        {activeStep === 'intake' && (
          <div className="space-y-6">
            <ChatIntake
              onExtractText={handleExtractText}
              onExtractAudio={handleExtractAudio}
              isLoading={isLoading}
              clarificationPrompt={clarificationPrompt}
              suggestedFields={suggestedFields}
              currentProfile={profile.age ? profile : null}
            />

            {profile.age && (
              <div className="text-center">
                <button
                  onClick={() => setActiveStep('review')}
                  className="inline-flex items-center space-x-1.5 text-xs text-zinc-500 hover:text-zinc-900 underline font-medium"
                >
                  <span>You have active profile data. Click here to review facts →</span>
                </button>
              </div>
            )}
          </div>
        )}

        {activeStep === 'review' && (
          <div className="space-y-6">
            <ProfileReviewCard
              profile={profile}
              confidence={confidenceByField}
              onChange={setProfile}
              onBackToIntake={() => setActiveStep('intake')}
              onConfirmAndMatch={(p) => {
                setProfile(p);
                handleFindSchemes(p);
              }}
              isLoading={isLoading}
            />
          </div>
        )}

        {activeStep === 'results' && matchResponse && (
          <div className="space-y-6">
            {/* Top Control Bar in Results */}
            <div className="flex items-center justify-between bg-white rounded-2xl px-5 py-3 border border-zinc-200/80 shadow-2xs">
              <button
                onClick={() => setActiveStep('review')}
                className="flex items-center space-x-1.5 text-xs font-semibold text-zinc-600 hover:text-zinc-900 transition-colors"
              >
                <ArrowLeft className="w-3.5 h-3.5" />
                <span>Edit Profile Facts</span>
              </button>

              <div className="flex items-center space-x-3">
                <span className="hidden sm:inline text-xs text-zinc-400">
                  {matchResponse.counts.eligible} Likely Eligible
                </span>
                <button
                  onClick={() => handleFindSchemes()}
                  disabled={isLoading}
                  className="flex items-center space-x-1.5 bg-zinc-900 hover:bg-zinc-800 disabled:opacity-50 text-white font-medium text-xs px-3.5 py-1.5 rounded-xl transition-all shadow-xs"
                >
                  <RefreshCw className={`w-3 h-3 ${isLoading ? 'animate-spin' : ''}`} />
                  <span>Re-evaluate</span>
                </button>
              </div>
            </div>

            {/* Dynamic Follow-Up Prompt to unlock more schemes */}
            {!dismissFollowups && matchResponse.followup_fields.length > 0 && (
              <FollowUpPrompt
                fields={matchResponse.followup_fields}
                profile={profile}
                onUpdateField={handleFollowUpAnswer}
                onDismiss={() => setDismissFollowups(true)}
              />
            )}

            {/* Full-width Recommendations Grid */}
            <RecommendationsView
              matchResponse={matchResponse}
              onSelectScheme={(scheme) => setSelectedScheme(scheme)}
            />
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

      {/* Minimalist Apple Footer */}
      <footer className="mt-auto border-t border-zinc-200/60 bg-white/50 backdrop-blur-sm py-6 text-center text-xs text-zinc-400">
        <p>JanSevaAI &copy; {new Date().getFullYear()} — Evidence-backed, deterministic & contextual civic intelligence.</p>
      </footer>
    </div>
  );
};

export default App;
