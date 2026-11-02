export type Gender = 'female' | 'male' | 'transgender';
export type CasteCategory = 'general' | 'obc' | 'sc' | 'st' | 'pvtg' | 'dnt';
export type Residence = 'rural' | 'urban';
export type MaritalStatus = 'never_married' | 'married' | 'widowed' | 'divorced' | 'separated';
export type Qualification = 'below_10th' | '10th_pass' | '12th_pass' | 'diploma' | 'graduate' | 'postgraduate';
export type EmploymentStatus = 'employed' | 'self_employed' | 'unemployed';
export type OccupationSector = 
  | 'agriculture'
  | 'artisan_craft'
  | 'it_tech'
  | 'construction'
  | 'manufacturing'
  | 'services_retail'
  | 'healthcare'
  | 'education'
  | 'unorganized'
  | 'other';

export type BenefitIntent = 
  | 'credit_loan'
  | 'scholarship'
  | 'pension'
  | 'housing'
  | 'health_insurance'
  | 'skill_training'
  | 'subsidy_grant'
  | 'general';

export type DocumentType =
  | 'aadhaar'
  | 'ration_card'
  | 'income_certificate'
  | 'caste_certificate'
  | 'domicile_certificate'
  | 'bank_passbook'
  | 'birth_certificate'
  | 'disability_certificate'
  | 'land_records'
  | 'school_or_college_id'
  | 'marksheet'
  | 'passport_photo';

export interface RequiredDocumentItem {
  type: DocumentType | null;
  text: string;
  source_line?: number;
}

export interface CitizenProfile {
  name?: string | null;
  age?: number | null;
  gender?: Gender | null;
  marital_status?: MaritalStatus | null;
  state_ut?: string | null;
  residence?: Residence | null;
  qualification?: Qualification | null;
  is_student?: boolean | null;
  employment_status?: EmploymentStatus | null;
  has_work_experience?: boolean | null;
  years_of_experience?: number | null;
  current_sector?: OccupationSector | null;
  aspiring_sector?: OccupationSector | null;
  benefit_intent?: BenefitIntent | null;
  is_farmer?: boolean | null;
  land_holding_acres?: number | null;
  caste_category?: CasteCategory | null;
  is_bpl?: boolean | null;
  is_minority?: boolean | null;
  annual_family_income_inr?: number | null;
  is_differently_abled?: boolean | null;
  disability_percentage?: number | null;
  is_govt_employee?: boolean | null;
  documents_held?: string[];
  confirmed: boolean;
}

export interface ProfileExtractResponse {
  profile: CitizenProfile;
  confidence_by_field: Record<string, number>;
  raw_phrases_by_field: Record<string, string>;
  transcript: string;
  is_insufficient: boolean;
  clarification_prompt?: string | null;
  suggested_fields: string[];
}

export interface CriterionResult {
  criterion_id: string;
  kind: string;
  group_id: number;
  field?: string | null;
  result: 'pass' | 'fail' | 'unknown';
  quote: string;
  quote_verified: boolean;
  source_line: number;
  source_section?: string | null;
  note?: string | null;
  is_specialized?: boolean;
}

export interface SchemeVerdictResult {
  slug: string;
  name: string;
  ministry_or_department: string;
  level: string;
  beneficiary_states: string[];
  categories: string[];
  close_date?: string | null;
  verdict: 'eligible' | 'needs_more_info' | 'ineligible' | 'closed';
  benefit_snippet: string;
  description?: string | null;
  myscheme_url?: string;
  required_documents?: (RequiredDocumentItem | string)[];
  specialized_criteria?: string[];
  verified_ratio: number;
  contextual_match_reason?: string | null;
  missing_fields: string[];
  criteria_results: CriterionResult[];
  unlocked_in_this_round?: boolean;
  requires_manual_review?: boolean;
}

export interface MatchCounts {
  eligible: number;
  needs_more_info: number;
  ineligible: number;
  closed: number;
  excluded_by_state: number;
}

export interface MatchResponse {
  state_filter_applied: boolean;
  counts: MatchCounts;
  followup_fields: string[];
  unlock_summary?: string | null;
  results: {
    eligible: SchemeVerdictResult[];
    needs_more_info: SchemeVerdictResult[];
    ineligible: SchemeVerdictResult[];
    closed: SchemeVerdictResult[];
  };
}

export interface CatalogStatus {
  status: string;
  total_schemes: number;
  compiled_schemes: number;
  total_criteria: number;
}
