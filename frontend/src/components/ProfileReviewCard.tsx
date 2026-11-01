import React, { useState, useEffect } from 'react';
import { CheckCircle2, Edit3, Sparkles, UserCheck } from 'lucide-react';
import { CitizenProfile, Gender, Qualification, OccupationSector, BenefitIntent } from '../types';

interface ProfileReviewCardProps {
  profile: CitizenProfile;
  confidence?: Record<string, number>;
  onChange?: (profile: CitizenProfile) => void;
  onConfirmAndMatch?: (confirmedProfile: CitizenProfile) => void;
  isLoading: boolean;
}

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

  const getConfBadge = (field: string) => {
    const score = confidence?.[field];
    if (score === undefined) return null;
    if (score >= 0.9) {
      return <span className="text-[10px] bg-emerald-100 text-emerald-800 font-semibold px-1.5 py-0.5 rounded">High Conf</span>;
    }
    if (score >= 0.7) {
      return <span className="text-[10px] bg-amber-100 text-amber-800 font-semibold px-1.5 py-0.5 rounded">Moderate</span>;
    }
    return <span className="text-[10px] bg-rose-100 text-rose-800 font-semibold px-1.5 py-0.5 rounded">Check</span>;
  };

  return (
    <div className="bg-white rounded-3xl p-6 sm:p-8 shadow-sm border border-slate-200 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <div className="inline-flex items-center space-x-1.5 px-3 py-1 bg-emerald-50 border border-emerald-200 rounded-full text-emerald-800 text-xs font-bold uppercase tracking-wider mb-2">
            <UserCheck className="w-3.5 h-3.5" />
            <span>Step 2 · Human-in-the-Loop Review</span>
          </div>
          <h2 className="text-xl sm:text-2xl font-extrabold text-slate-900 tracking-tight">
            Please Review Your Extracted Profile
          </h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Rule E9 requires confirming your facts so no eligibility decision is made on inaccurate assumptions.
          </p>
        </div>

        <button
          type="button"
          onClick={() => setIsEditing(!isEditing)}
          className="flex items-center space-x-1.5 text-xs font-semibold text-blue-600 hover:text-blue-800 bg-blue-50 px-3 py-1.5 rounded-xl border border-blue-200 transition-colors"
        >
          <Edit3 className="w-3.5 h-3.5" />
          <span>{isEditing ? 'Done Editing' : 'Edit Details'}</span>
        </button>
      </div>

      {/* Grid of Profile Attributes */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {/* State */}
        <div className="p-3.5 rounded-2xl bg-slate-50 border border-slate-200 space-y-1">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500">State / UT</span>
            {getConfBadge('state_ut')}
          </div>
          {isEditing ? (
            <select
              value={edited.state_ut || ''}
              onChange={(e) => handleFieldChange('state_ut', e.target.value || null)}
              className="w-full text-xs font-bold bg-white p-1.5 border border-slate-300 rounded-lg"
            >
              <option value="">Select State</option>
              {STATES_LIST.map((s) => (
                <option key={s} value={s}>{s}</option>
              ))}
            </select>
          ) : (
            <p className="text-sm font-bold text-slate-900">{edited.state_ut || <span className="text-slate-400 font-normal">Not Specified</span>}</p>
          )}
        </div>

        {/* Age & Gender */}
        <div className="p-3.5 rounded-2xl bg-slate-50 border border-slate-200 space-y-1">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500">Age & Gender</span>
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
                className="w-16 text-xs font-bold bg-white p-1.5 border border-slate-300 rounded-lg"
              />
              <select
                value={edited.gender || ''}
                onChange={(e) => handleFieldChange('gender', (e.target.value as Gender) || null)}
                className="flex-1 text-xs font-bold bg-white p-1.5 border border-slate-300 rounded-lg"
              >
                <option value="">Gender</option>
                <option value="male">Male</option>
                <option value="female">Female</option>
                <option value="transgender">Transgender</option>
              </select>
            </div>
          ) : (
            <p className="text-sm font-bold text-slate-900">
              {edited.age ? `${edited.age} yrs` : 'Age: ?'} · {edited.gender || 'Gender: ?'}
            </p>
          )}
        </div>

        {/* Education Milestone */}
        <div className="p-3.5 rounded-2xl bg-slate-50 border border-slate-200 space-y-1">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500">Highest Education</span>
            {getConfBadge('qualification')}
          </div>
          {isEditing ? (
            <select
              value={edited.qualification || ''}
              onChange={(e) => handleFieldChange('qualification', (e.target.value as Qualification) || null)}
              className="w-full text-xs font-bold bg-white p-1.5 border border-slate-300 rounded-lg"
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
            <p className="text-sm font-bold text-slate-900">{edited.qualification?.replace('_', ' ').toUpperCase() || <span className="text-slate-400 font-normal">Not Specified</span>}</p>
          )}
        </div>

        {/* Career Sector & Experience */}
        <div className="p-3.5 rounded-2xl bg-slate-50 border border-slate-200 space-y-1">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500">Industry / Sector</span>
            {getConfBadge('current_sector')}
          </div>
          {isEditing ? (
            <select
              value={edited.current_sector || ''}
              onChange={(e) => handleFieldChange('current_sector', (e.target.value as OccupationSector) || null)}
              className="w-full text-xs font-bold bg-white p-1.5 border border-slate-300 rounded-lg"
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
            <p className="text-sm font-bold text-slate-900">
              {edited.current_sector?.replace('_', ' ').toUpperCase() || <span className="text-slate-400 font-normal">General</span>}
              {edited.has_work_experience !== undefined && (
                <span className="text-xs font-normal text-slate-500 ml-1.5">
                  ({edited.has_work_experience ? `${edited.years_of_experience || 'Some'} yrs exp` : 'Fresher'})
                </span>
              )}
            </p>
          )}
        </div>

        {/* Annual Income */}
        <div className="p-3.5 rounded-2xl bg-slate-50 border border-slate-200 space-y-1">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500">Annual Family Income</span>
            {getConfBadge('annual_family_income_inr')}
          </div>
          {isEditing ? (
            <input
              type="number"
              min="0"
              value={edited.annual_family_income_inr || ''}
              onChange={(e) => handleFieldChange('annual_family_income_inr', e.target.value ? parseInt(e.target.value) : null)}
              placeholder="e.g. 150000"
              className="w-full text-xs font-bold bg-white p-1.5 border border-slate-300 rounded-lg"
            />
          ) : (
            <p className="text-sm font-bold text-slate-900">
              {edited.annual_family_income_inr ? `₹${edited.annual_family_income_inr.toLocaleString('en-IN')}` : <span className="text-slate-400 font-normal">Not Specified</span>}
            </p>
          )}
        </div>

        {/* Benefit Intent (Loans, Scholarships, etc.) */}
        <div className="p-3.5 rounded-2xl bg-slate-50 border border-slate-200 space-y-1">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500">Assistance / Goal</span>
            {getConfBadge('benefit_intent')}
          </div>
          {isEditing ? (
            <select
              value={edited.benefit_intent || ''}
              onChange={(e) => handleFieldChange('benefit_intent', (e.target.value as BenefitIntent) || null)}
              className="w-full text-xs font-bold bg-white p-1.5 border border-slate-300 rounded-lg"
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
            <p className="text-sm font-bold text-slate-900">{edited.benefit_intent?.replace('_', ' ').toUpperCase() || 'General Welfare'}</p>
          )}
        </div>
      </div>

      {/* Confirmation Call to Action */}
      <div className="pt-2 flex flex-col sm:flex-row items-center justify-between gap-3 border-t border-slate-100">
        <p className="text-xs text-slate-500 flex items-center space-x-1.5">
          <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
          <span>I verify these facts represent my current circumstances.</span>
        </p>

        <button
          type="button"
          onClick={() => onConfirmAndMatch?.({ ...edited, confirmed: true })}
          disabled={isLoading}
          className="w-full sm:w-auto flex items-center justify-center space-x-2 px-6 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold uppercase tracking-wider rounded-xl shadow-md shadow-emerald-600/20 disabled:opacity-50 transition-all"
        >
          <Sparkles className="w-4 h-4" />
          <span>{isLoading ? 'Evaluating Schemes…' : 'Confirm & Discover My Schemes'}</span>
        </button>
      </div>
    </div>
  );
};
