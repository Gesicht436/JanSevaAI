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
    question: 'What is your social / caste category for affirmative benefits?',
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
      { label: 'Diploma / ITI', value: 'diploma' },
      { label: 'Graduate', value: 'graduate' },
      { label: 'Postgraduate', value: 'postgraduate' },
    ],
  },
  is_student: {
    label: 'Student Status',
    question: 'Are you currently enrolled in school or higher education?',
    options: [
      { label: 'Yes, Enrolled Student', value: true },
      { label: 'No, Not a Student', value: false },
    ],
  },
  is_farmer: {
    label: 'Agricultural Background',
    question: 'Are you engaged in farming or agricultural cultivation?',
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
    question: 'Which sector are you working in or seeking to work in?',
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
      { label: 'Scholarship / Education Aid', value: 'scholarship' },
      { label: 'Pension Support', value: 'pension' },
      { label: 'Housing Assistance', value: 'housing' },
      { label: 'Health Insurance', value: 'health_insurance' },
      { label: 'Skill Training & Certification', value: 'skill_training' },
      { label: 'Direct Subsidy / Grant', value: 'subsidy_grant' },
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
    <div className="bg-white border border-zinc-200/90 rounded-3xl p-6 shadow-xs relative overflow-hidden transition-all animate-fadeIn">
      <div className="flex items-start justify-between">
        <div className="flex items-center space-x-2 text-zinc-800 font-semibold text-xs uppercase tracking-wide">
          <Sparkles className="w-3.5 h-3.5 text-zinc-600" />
          <span>High-Leverage Question ({activeIdx + 1} of {missingConfigs.length})</span>
        </div>
        {onDismiss && (
          <button
            onClick={onDismiss}
            className="text-zinc-400 hover:text-zinc-700 p-1 rounded-full hover:bg-zinc-100 transition-colors"
            title="Dismiss question"
          >
            <X className="w-4 h-4" />
          </button>
        )}
      </div>

      <div className="mt-2.5">
        <h4 className="text-base font-semibold text-zinc-900 leading-snug">
          {config.question}
        </h4>
        <p className="text-xs text-zinc-500 mt-1">
          Answering this clarifies pending criteria for schemes in your queue.
        </p>
      </div>

      {config.options && config.options.length > 0 ? (
        <div className="mt-4 flex flex-wrap gap-2">
          {config.options.map((opt, i) => (
            <button
              key={i}
              onClick={() => handleSelect(opt.value)}
              className="bg-zinc-50 hover:bg-zinc-900 hover:text-white text-zinc-800 text-xs font-medium px-4 py-2 rounded-xl border border-zinc-200 transition-all flex items-center space-x-1.5 active:scale-[0.98]"
            >
              <span>{opt.label}</span>
              <ChevronRight className="w-3 h-3 opacity-40" />
            </button>
          ))}
        </div>
      ) : (
        <form onSubmit={handleCustomSubmit} className="mt-4 flex items-center space-x-2 max-w-sm">
          <input
            type={config.inputType || 'text'}
            value={customInput}
            onChange={(e) => setCustomInput(e.target.value)}
            placeholder={`Enter ${config.label}`}
            className="flex-1 bg-zinc-50 border border-zinc-300 text-zinc-900 text-xs rounded-xl px-3.5 py-2 outline-none focus:ring-1 focus:ring-zinc-800"
          />
          <button
            type="submit"
            className="bg-zinc-900 hover:bg-zinc-800 text-white font-medium text-xs px-4 py-2 rounded-xl transition-all shadow-xs"
          >
            Save
          </button>
        </form>
      )}

      {missingConfigs.length > 1 && (
        <div className="mt-4 flex items-center justify-between text-xs text-zinc-400 pt-3 border-t border-zinc-100">
          <span>{missingConfigs.length - activeIdx - 1} more follow-up(s) remaining</span>
          {activeIdx + 1 < missingConfigs.length && (
            <button
              onClick={() => setActiveIdx((prev) => prev + 1)}
              className="text-zinc-600 hover:text-zinc-900 font-medium hover:underline"
            >
              Skip
            </button>
          )}
        </div>
      )}
    </div>
  );
};
