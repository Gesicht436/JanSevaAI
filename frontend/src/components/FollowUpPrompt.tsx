import React, { useState } from 'react';
import { CitizenProfile } from '../types';
import { ChevronRight, Sparkles, X } from 'lucide-react';

interface FollowUpPromptProps {
  fields: string[];
  profile: CitizenProfile;
  onUpdateField: (field: string, value: any) => void;
  onDismiss?: () => void;
}

interface FieldOption {
  label: string;
  value: any;
}

interface FieldConfig {
  label: string;
  question: string;
  options?: FieldOption[];
  inputType?: 'number' | 'text';
}

const FIELD_CONFIGS: Record<string, FieldConfig> = {
  marital_status: {
    label: 'Marital Status',
    question: 'What is your marital status?',
    options: [
      { label: 'Never Married', value: 'never_married' },
      { label: 'Married', value: 'married' },
      { label: 'Widowed', value: 'widowed' },
      { label: 'Divorced', value: 'divorced' },
    ],
  },
  residence: {
    label: 'Area of Residence',
    question: 'Do you live in a rural or urban area?',
    options: [
      { label: 'Rural (Village / Gram Panchayat)', value: 'rural' },
      { label: 'Urban (City / Town / Municipality)', value: 'urban' },
    ],
  },
  caste_category: {
    label: 'Social Category',
    question: 'What is your social / caste category for affirmative benefit reservation?',
    options: [
      { label: 'General', value: 'general' },
      { label: 'OBC', value: 'obc' },
      { label: 'SC', value: 'sc' },
      { label: 'ST', value: 'st' },
    ],
  },
  qualification: {
    label: 'Highest Qualification',
    question: 'What is your highest educational qualification?',
    options: [
      { label: 'Below 10th', value: 'below_10th' },
      { label: '10th Pass', value: '10th_pass' },
      { label: '12th Pass', value: '12th_pass' },
      { label: 'Diploma', value: 'diploma' },
      { label: 'Graduate', value: 'graduate' },
      { label: 'Postgraduate', value: 'postgraduate' },
    ],
  },
  is_student: {
    label: 'Student Status',
    question: 'Are you currently enrolled in school, college, or university?',
    options: [
      { label: 'Yes, Enrolled Student', value: true },
      { label: 'No, Not a Student', value: false },
    ],
  },
  is_farmer: {
    label: 'Agricultural Background',
    question: 'Are you engaged in agricultural or farming activities?',
    options: [
      { label: 'Yes, Farmer / Cultivator', value: true },
      { label: 'No', value: false },
    ],
  },
  is_bpl: {
    label: 'BPL Ration Card',
    question: 'Does your family hold a Below Poverty Line (BPL) or Antyodaya ration card?',
    options: [
      { label: 'Yes (BPL / Antyodaya)', value: true },
      { label: 'No', value: false },
    ],
  },
  has_work_experience: {
    label: 'Prior Work Experience',
    question: 'Do you have prior employment or business work experience?',
    options: [
      { label: 'Yes, have experience', value: true },
      { label: 'No, fresher / new seeker', value: false },
    ],
  },
  current_sector: {
    label: 'Field of Work / Industry',
    question: 'Which sector are you working in, or looking to work in?',
    options: [
      { label: 'IT & Technology', value: 'it_tech' },
      { label: 'Agriculture & Farming', value: 'agriculture' },
      { label: 'Handicrafts & Artisans', value: 'artisan_craft' },
      { label: 'Construction', value: 'construction' },
      { label: 'Manufacturing', value: 'manufacturing' },
      { label: 'Services & Retail', value: 'services_retail' },
      { label: 'Healthcare', value: 'healthcare' },
      { label: 'Education', value: 'education' },
      { label: 'Unorganized / Other', value: 'unorganized' },
    ],
  },
  benefit_intent: {
    label: 'Primary Benefit Needed',
    question: 'What kind of government support are you primarily seeking?',
    options: [
      { label: 'Loan / Business Credit', value: 'credit_loan' },
      { label: 'Scholarship / Education Support', value: 'scholarship' },
      { label: 'Pension / Senior Citizen', value: 'pension' },
      { label: 'Housing Assistance (Pucca Ghar)', value: 'housing' },
      { label: 'Health Insurance', value: 'health_insurance' },
      { label: 'Skill Training & Certification', value: 'skill_training' },
      { label: 'Grant / Direct Subsidy', value: 'subsidy_grant' },
    ],
  },
  annual_family_income_inr: {
    label: 'Annual Family Income',
    question: 'What is your approximate annual household income?',
    options: [
      { label: 'Below ₹1,00,000 / yr', value: 90000 },
      { label: '₹1,00,000 – ₹2,50,000', value: 200000 },
      { label: '₹2,50,000 – ₹5,00,000', value: 400000 },
      { label: '₹5,00,000 – ₹8,00,000', value: 700000 },
      { label: 'Above ₹8,00,000', value: 1000000 },
    ],
  },
};

export const FollowUpPrompt: React.FC<FollowUpPromptProps> = ({
  fields,
  profile,
  onUpdateField,
  onDismiss,
}) => {
  // Find fields that have configs and are still missing/null in the profile
  const missingConfigs = fields
    .filter((f) => {
      const val = (profile as any)[f];
      return val === undefined || val === null;
    })
    .map((f) => ({ key: f, config: FIELD_CONFIGS[f] }))
    .filter((item) => !!item.config);

  const [activeIdx, setActiveIdx] = useState(0);
  const [customInput, setCustomInput] = useState('');

  if (missingConfigs.length === 0) {
    return null;
  }

  const currentItem = missingConfigs[Math.min(activeIdx, missingConfigs.length - 1)];
  const { key, config } = currentItem;

  const handleSelect = (val: any) => {
    onUpdateField(key, val);
    if (activeIdx + 1 < missingConfigs.length) {
      setActiveIdx((prev) => prev + 1);
    }
  };

  const handleCustomSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!customInput.trim()) return;
    const val = config.inputType === 'number' ? Number(customInput) : customInput.trim();
    onUpdateField(key, val);
    setCustomInput('');
    if (activeIdx + 1 < missingConfigs.length) {
      setActiveIdx((prev) => prev + 1);
    }
  };

  return (
    <div className="bg-gradient-to-r from-amber-50 via-orange-50 to-amber-100/70 border border-amber-300 rounded-2xl p-5 shadow-sm relative overflow-hidden transition-all animate-fadeIn">
      <div className="flex items-start justify-between">
        <div className="flex items-center space-x-2 text-amber-800 font-bold text-sm">
          <Sparkles className="w-4 h-4 text-amber-600 animate-pulse" />
          <span>Unlock More Schemes ({activeIdx + 1} of {missingConfigs.length})</span>
        </div>
        {onDismiss && (
          <button
            onClick={onDismiss}
            className="text-slate-400 hover:text-slate-600 p-1 rounded-full hover:bg-white/50 transition-colors"
            title="Dismiss question"
          >
            <X className="w-4 h-4" />
          </button>
        )}
      </div>

      <div className="mt-2">
        <h4 className="text-base font-semibold text-slate-800">
          {config.question}
        </h4>
        <p className="text-xs text-slate-600 mt-0.5">
          Providing this helps verify your eligibility for several welfare schemes waiting for confirmation.
        </p>
      </div>

      {config.options && config.options.length > 0 ? (
        <div className="mt-3.5 flex flex-wrap gap-2">
          {config.options.map((opt, i) => (
            <button
              key={i}
              onClick={() => handleSelect(opt.value)}
              className="bg-white hover:bg-amber-600 hover:text-white text-slate-700 text-xs font-medium px-3.5 py-2 rounded-xl border border-amber-200 shadow-sm transition-all flex items-center space-x-1.5 active:scale-95"
            >
              <span>{opt.label}</span>
              <ChevronRight className="w-3.5 h-3.5 opacity-60" />
            </button>
          ))}
        </div>
      ) : (
        <form onSubmit={handleCustomSubmit} className="mt-3 flex items-center space-x-2 max-w-sm">
          <input
            type={config.inputType || 'text'}
            value={customInput}
            onChange={(e) => setCustomInput(e.target.value)}
            placeholder={`Enter ${config.label}`}
            className="flex-1 bg-white border border-amber-300 text-slate-800 text-xs rounded-xl px-3 py-2 outline-none focus:ring-2 focus:ring-amber-400"
          />
          <button
            type="submit"
            className="bg-amber-600 hover:bg-amber-700 text-white font-medium text-xs px-4 py-2 rounded-xl transition-all shadow-sm"
          >
            Save
          </button>
        </form>
      )}

      {missingConfigs.length > 1 && (
        <div className="mt-3 flex items-center justify-between text-xs text-slate-500 pt-2 border-t border-amber-200/60">
          <span>{missingConfigs.length - activeIdx - 1} more high-leverage question(s) left</span>
          {activeIdx + 1 < missingConfigs.length && (
            <button
              onClick={() => setActiveIdx((prev) => prev + 1)}
              className="text-amber-700 hover:text-amber-900 font-medium underline"
            >
              Skip this question
            </button>
          )}
        </div>
      )}
    </div>
  );
};
