import React, { useState, useEffect } from 'react';
import { CheckCircle2, Edit3, ArrowLeft, ArrowRight, UserCheck, FileCheck, Check } from 'lucide-react';
import { CitizenProfile, Gender, Qualification, OccupationSector, BenefitIntent, DocumentType } from '../types';

interface ProfileReviewCardProps {
  profile: CitizenProfile;
  confidence?: Record<string, number>;
  onChange?: (profile: CitizenProfile) => void;
  onConfirmAndMatch?: (confirmedProfile: CitizenProfile) => void;
  onBackToIntake?: () => void;
  isLoading: boolean;
}

const CANONICAL_DOCS: { id: DocumentType; label: string }[] = [
  { id: 'aadhaar', label: 'Aadhaar Card' },
  { id: 'ration_card', label: 'Ration Card' },
  { id: 'income_certificate', label: 'Income Certificate' },
  { id: 'caste_certificate', label: 'Caste Certificate' },
  { id: 'domicile_certificate', label: 'Domicile / Residence Certificate' },
  { id: 'bank_passbook', label: 'Bank Passbook / Account' },
  { id: 'birth_certificate', label: 'Birth Certificate / Age Proof' },
  { id: 'disability_certificate', label: 'Disability Certificate (UDID)' },
  { id: 'land_records', label: 'Land Records (Patta / 7-12)' },
  { id: 'school_or_college_id', label: 'Student / College ID' },
  { id: 'marksheet', label: 'Degree / Marksheet' },
  { id: 'passport_photo', label: 'Passport Photograph' },
];

const STATES_LIST = [
  'Andaman and Nicobar Islands', 'Andhra Pradesh', 'Arunachal Pradesh', 'Assam', 'Bihar',
  'Chandigarh', 'Chhattisgarh', 'Dadra and Nagar Haveli and Daman and Diu', 'Delhi', 'Goa',
  'Gujarat', 'Haryana', 'Himachal Pradesh', 'Jammu and Kashmir', 'Jharkhand', 'Karnataka',
  'Kerala', 'Ladakh', 'Lakshadweep', 'Madhya Pradesh', 'Maharashtra', 'Manipur', 'Meghalaya',
  'Mizoram', 'Nagaland', 'Odisha', 'Puducherry', 'Punjab', 'Rajasthan', 'Sikkim',
  'Tamil Nadu', 'Telangana', 'Tripura', 'Uttar Pradesh', 'Uttarakhand', 'West Bengal'
];

export const ProfileReviewCard: React.FC<ProfileReviewCardProps> = ({
  profile,
  confidence = {},
  onChange,
  onConfirmAndMatch,
  onBackToIntake,
  isLoading,
}) => {
  const [edited, setEdited] = useState<CitizenProfile>({ ...profile });
  const [isEditing, setIsEditing] = useState(false);

  useEffect(() => {
    setEdited({ ...profile });
  }, [profile]);

  const handleFieldChange = (field: keyof CitizenProfile, value: any) => {
    const updated = { ...edited, [field]: value };
    setEdited(updated);
    if (onChange) {
      onChange(updated);
    }
  };

  const toggleDocHeld = (docId: string) => {
    const current = edited.documents_held || [];
    const updatedDocs = current.includes(docId)
      ? current.filter((d) => d !== docId)
      : [...current, docId];
    handleFieldChange('documents_held', updatedDocs);
  };

  const getConfBadge = (field: string) => {
    const score = confidence?.[field];
    if (score === undefined) return null;
    if (score >= 0.9) {
      return <span className="text-[10px] bg-emerald-50 text-emerald-800 border border-emerald-200 font-semibold px-1.5 py-0.5 rounded-md">Verified</span>;
    }
    if (score >= 0.7) {
      return <span className="text-[10px] bg-amber-50 text-amber-800 border border-amber-200 font-semibold px-1.5 py-0.5 rounded-md">Moderate</span>;
    }
    return <span className="text-[10px] bg-zinc-100 text-zinc-600 border border-zinc-200 font-semibold px-1.5 py-0.5 rounded-md">Check</span>;
  };

  return (
    <div className="bg-white rounded-3xl p-6 sm:p-10 border border-zinc-200/80 shadow-[0_1px_3px_rgba(0,0,0,0.02)] space-y-8 animate-fadeIn max-w-3xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-zinc-100 pb-5">
        <div>
          <div className="inline-flex items-center space-x-1.5 px-3 py-1 bg-zinc-100 rounded-full text-zinc-700 text-xs font-medium border border-zinc-200/60 mb-2">
            <UserCheck className="w-3.5 h-3.5 text-zinc-600" />
            <span>Step 2 · Fact Review</span>
          </div>
          <h2 className="text-xl sm:text-2xl font-bold tracking-tight text-zinc-900">
            Review Your Extracted Profile
          </h2>
          <p className="text-xs text-zinc-500 mt-1">
            Rule E9 requires confirming your facts so no eligibility decision is made on inaccurate assumptions.
          </p>
        </div>

        <button
          type="button"
          onClick={() => setIsEditing(!isEditing)}
          className="self-start sm:self-center flex items-center space-x-1.5 text-xs font-semibold text-zinc-700 hover:text-zinc-900 bg-zinc-100 hover:bg-zinc-200/80 px-3 py-1.5 rounded-xl border border-zinc-200/60 transition-colors"
        >
          <Edit3 className="w-3.5 h-3.5" />
          <span>{isEditing ? 'Done Editing' : 'Edit Facts'}</span>
        </button>
      </div>

      {/* Grid of Profile Attributes */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3.5">
        {/* State */}
        <div className="p-4 rounded-2xl bg-zinc-50/70 border border-zinc-200/80 space-y-1">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-zinc-400">State / UT</span>
            {getConfBadge('state_ut')}
          </div>
          {isEditing ? (
            <select
              value={edited.state_ut || ''}
              onChange={(e) => handleFieldChange('state_ut', e.target.value || null)}
              className="w-full text-xs font-semibold bg-white p-1.5 border border-zinc-300 rounded-lg focus:outline-none focus:ring-1 focus:ring-zinc-800"
            >
              <option value="">Select State</option>
              {STATES_LIST.map((s) => (
                <option key={s} value={s}>{s}</option>
              ))}
            </select>
          ) : (
            <p className="text-sm font-semibold text-zinc-900">{edited.state_ut || <span className="text-zinc-400 font-normal">Not Specified</span>}</p>
          )}
        </div>

        {/* Age & Gender */}
        <div className="p-4 rounded-2xl bg-zinc-50/70 border border-zinc-200/80 space-y-1">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-zinc-400">Age & Gender</span>
            {getConfBadge('age')}
          </div>
          {isEditing ? (
            <div className="flex space-x-2">
              <input
                type="number"
                min="0"
                max="120"
                value={edited.age || ''}
                onChange={(e) => handleFieldChange('age', e.target.value ? parseInt(e.target.value) : null)}
                placeholder="Age"
                className="w-16 text-xs font-semibold bg-white p-1.5 border border-zinc-300 rounded-lg focus:outline-none focus:ring-1 focus:ring-zinc-800"
              />
              <select
                value={edited.gender || ''}
                onChange={(e) => handleFieldChange('gender', (e.target.value as Gender) || null)}
                className="flex-1 text-xs font-semibold bg-white p-1.5 border border-zinc-300 rounded-lg focus:outline-none focus:ring-1 focus:ring-zinc-800"
              >
                <option value="">Gender</option>
                <option value="male">Male</option>
                <option value="female">Female</option>
                <option value="transgender">Transgender</option>
              </select>
            </div>
          ) : (
            <p className="text-sm font-semibold text-zinc-900">
              {edited.age ? `${edited.age} yrs` : 'Age: ?'} · {edited.gender || 'Gender: ?'}
            </p>
          )}
        </div>

        {/* Education Milestone */}
        <div className="p-4 rounded-2xl bg-zinc-50/70 border border-zinc-200/80 space-y-1">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-zinc-400">Highest Education</span>
            {getConfBadge('qualification')}
          </div>
          {isEditing ? (
            <select
              value={edited.qualification || ''}
              onChange={(e) => handleFieldChange('qualification', (e.target.value as Qualification) || null)}
              className="w-full text-xs font-semibold bg-white p-1.5 border border-zinc-300 rounded-lg focus:outline-none focus:ring-1 focus:ring-zinc-800"
            >
              <option value="">Select Qualification</option>
              <option value="below_10th">Below 10th</option>
              <option value="10th_pass">10th Pass</option>
              <option value="12th_pass">12th Pass</option>
              <option value="diploma">Diploma / ITI</option>
              <option value="graduate">Bachelor's / Graduate</option>
              <option value="postgraduate">Postgraduate (Master's / Ph.D)</option>
            </select>
          ) : (
            <p className="text-sm font-semibold text-zinc-900">{edited.qualification?.replace('_', ' ').toUpperCase() || <span className="text-zinc-400 font-normal">Not Specified</span>}</p>
          )}
        </div>

        {/* Career Sector & Experience */}
        <div className="p-4 rounded-2xl bg-zinc-50/70 border border-zinc-200/80 space-y-1">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-zinc-400">Industry / Sector</span>
            {getConfBadge('current_sector')}
          </div>
          {isEditing ? (
            <select
              value={edited.current_sector || ''}
              onChange={(e) => handleFieldChange('current_sector', (e.target.value as OccupationSector) || null)}
              className="w-full text-xs font-semibold bg-white p-1.5 border border-zinc-300 rounded-lg focus:outline-none focus:ring-1 focus:ring-zinc-800"
            >
              <option value="">Select Sector</option>
              <option value="it_tech">IT & Technology</option>
              <option value="agriculture">Agriculture & Farming</option>
              <option value="artisan_craft">Artisan & Craft Trades</option>
              <option value="construction">Construction & Building</option>
              <option value="manufacturing">Manufacturing / MSME</option>
              <option value="services_retail">Services & Retail</option>
              <option value="healthcare">Healthcare & Sanitation</option>
              <option value="education">Education & Research</option>
              <option value="unorganized">Street Vendor / Daily Wage</option>
            </select>
          ) : (
            <p className="text-sm font-semibold text-zinc-900">
              {edited.current_sector?.replace('_', ' ').toUpperCase() || <span className="text-zinc-400 font-normal">General</span>}
              {edited.has_work_experience !== undefined && (
                <span className="text-xs font-normal text-zinc-500 ml-1.5">
                  ({edited.has_work_experience ? `${edited.years_of_experience || 'Some'} yrs exp` : 'Fresher'})
                </span>
              )}
            </p>
          )}
        </div>

        {/* Annual Income */}
        <div className="p-4 rounded-2xl bg-zinc-50/70 border border-zinc-200/80 space-y-1">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-zinc-400">Annual Family Income</span>
            {getConfBadge('annual_family_income_inr')}
          </div>
          {isEditing ? (
            <input
              type="number"
              min="0"
              value={edited.annual_family_income_inr || ''}
              onChange={(e) => handleFieldChange('annual_family_income_inr', e.target.value ? parseInt(e.target.value) : null)}
              placeholder="e.g. 150000"
              className="w-full text-xs font-semibold bg-white p-1.5 border border-zinc-300 rounded-lg focus:outline-none focus:ring-1 focus:ring-zinc-800"
            />
          ) : (
            <p className="text-sm font-semibold text-zinc-900">
              {edited.annual_family_income_inr ? `₹${edited.annual_family_income_inr.toLocaleString('en-IN')}` : <span className="text-zinc-400 font-normal">Not Specified</span>}
            </p>
          )}
        </div>

        {/* Benefit Intent (Loans, Scholarships, etc.) */}
        <div className="p-4 rounded-2xl bg-zinc-50/70 border border-zinc-200/80 space-y-1">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-zinc-400">Benefit Intent</span>
            {getConfBadge('benefit_intent')}
          </div>
          {isEditing ? (
            <select
              value={edited.benefit_intent || ''}
              onChange={(e) => handleFieldChange('benefit_intent', (e.target.value as BenefitIntent) || null)}
              className="w-full text-xs font-semibold bg-white p-1.5 border border-zinc-300 rounded-lg focus:outline-none focus:ring-1 focus:ring-zinc-800"
            >
              <option value="">Any Welfare Support</option>
              <option value="credit_loan">Business / Startup Loan</option>
              <option value="scholarship">Scholarship & Education Aid</option>
              <option value="subsidy_grant">Capital / Equipment Subsidy</option>
              <option value="pension">Pension Support</option>
              <option value="housing">Housing Assistance</option>
              <option value="skill_training">Upskilling / Apprenticeship</option>
            </select>
          ) : (
            <p className="text-sm font-semibold text-zinc-900">{edited.benefit_intent?.replace('_', ' ').toUpperCase() || 'General Welfare'}</p>
          )}
        </div>
      </div>

      {/* Section: Documents In My Possession */}
      <div className="p-5 rounded-2xl bg-zinc-50/70 border border-zinc-200/80 space-y-3">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1">
          <div className="flex items-center space-x-2">
            <FileCheck className="w-4 h-4 text-zinc-700" />
            <h3 className="text-xs font-semibold uppercase tracking-wider text-zinc-800">
              Documents Currently in Your Possession (Checklist)
            </h3>
          </div>
          <span className="text-[11px] text-zinc-500">
            {(edited.documents_held || []).length} marked ready
          </span>
        </div>
        <p className="text-xs text-zinc-500">
          Mark documents you have ready. JanSeva AI compares this against official scheme requirements. Unmarked documents will be highlighted as needing confirmation.
        </p>
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2 pt-1">
          {CANONICAL_DOCS.map((doc) => {
            const isHeld = (edited.documents_held || []).includes(doc.id);
            return (
              <button
                key={doc.id}
                type="button"
                onClick={() => toggleDocHeld(doc.id)}
                className={`flex items-center space-x-2 p-2.5 rounded-xl border text-xs text-left transition-all ${
                  isHeld
                    ? 'bg-emerald-50 border-emerald-300 text-emerald-950 font-medium'
                    : 'bg-white border-zinc-200/90 text-zinc-700 hover:bg-zinc-100/60'
                }`}
              >
                <div
                  className={`w-4 h-4 rounded flex items-center justify-center border shrink-0 ${
                    isHeld
                      ? 'bg-emerald-600 border-emerald-600 text-white'
                      : 'border-zinc-300 bg-white'
                  }`}
                >
                  {isHeld && <Check className="w-3 h-3 stroke-[3]" />}
                </div>
                <span className="truncate">{doc.label}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Confirmation Call to Action */}
      <div className="pt-4 flex flex-col sm:flex-row items-center justify-between gap-4 border-t border-zinc-100">
        {onBackToIntake && (
          <button
            type="button"
            onClick={onBackToIntake}
            className="flex items-center space-x-1.5 text-xs font-semibold text-zinc-600 hover:text-zinc-900 transition-colors"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Back to Intake</span>
          </button>
        )}

        <div className="flex items-center space-x-2 text-xs text-zinc-500">
          <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
          <span>I verify these extracted facts represent my current status.</span>
        </div>

        <button
          type="button"
          onClick={() => onConfirmAndMatch?.({ ...edited, confirmed: true })}
          disabled={isLoading}
          className="w-full sm:w-auto flex items-center justify-center space-x-2 px-6 py-2.5 bg-zinc-900 hover:bg-zinc-800 text-white text-xs font-semibold rounded-xl shadow-xs disabled:opacity-50 transition-all active:scale-[0.98]"
        >
          <span>{isLoading ? 'Evaluating Schemes…' : 'Confirm & Discover Schemes'}</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </button>
      </div>
    </div>
  );
};
