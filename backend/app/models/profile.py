"""
Expanded Citizen Profile Schema
Session-only; lives in browser and request bodies; never stored on disk.
Captures demographics, education, career experience, industry sectors, and welfare intents.
"""

from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from .states import STATES, normalize_state

Gender = Literal["female", "male", "transgender"]
CasteCategory = Literal["general", "obc", "sc", "st", "pvtg", "dnt"]
Residence = Literal["rural", "urban"]
MaritalStatus = Literal["never_married", "married", "widowed", "divorced", "separated"]
Qualification = Literal["below_10th", "10th_pass", "12th_pass", "diploma", "graduate", "postgraduate"]
EmploymentStatus = Literal["employed", "self_employed", "unemployed"]

OccupationSector = Literal[
    "agriculture",      # Farming, dairy, fisheries, horticulture
    "artisan_craft",    # Handloom, carpentry, pottery, traditional trades
    "it_tech",          # Software, electronics, IT/ITeS, telecom
    "construction",     # Civil labor, plumbing, masonry, BOCW
    "manufacturing",    # Factory work, textiles, automotive, MSME
    "services_retail",  # Retail, hospitality, delivery, transport
    "healthcare",       # ASHA, nursing, medical support, sanitation
    "education",        # Teaching, research, coaching
    "unorganized",      # Daily wage, street vendor (PM-SVANidhi)
    "other"
]

BenefitIntent = Literal[
    "credit_loan",      # Business loan, working capital, startup funding
    "scholarship",      # Education fee waiver, stipend, fellowship
    "pension",          # Old age, widow, disability pension
    "housing",          # PMAY, shelter assistance
    "health_insurance", # Ayushman Bharat, medical coverage
    "skill_training",   # Vocational upskilling, apprenticeship
    "subsidy_grant",    # Equipment subsidy, agricultural input subsidy
    "general"
]

DocumentType = Literal[
    "aadhaar", "ration_card", "income_certificate", "caste_certificate",
    "domicile_certificate", "bank_passbook", "birth_certificate",
    "disability_certificate", "land_records", "school_or_college_id",
    "marksheet", "passport_photo"
]


class CitizenProfile(BaseModel):
    model_config = ConfigDict(extra="ignore")

    # Demographics
    name: Optional[str] = Field(None, description="Citizen full or given name if mentioned")
    age: Optional[int] = Field(None, ge=0, le=120, description="Age in completed whole years")
    gender: Optional[Gender] = Field(None, description="'female', 'male', or 'transgender'")
    marital_status: Optional[MaritalStatus] = Field(None, description="Marital status")

    # Geography
    state_ut: Optional[str] = Field(None, description="Canonical Indian State or UT")
    residence: Optional[Residence] = Field(None, description="'rural' or 'urban'")

    # Education & Learning
    qualification: Optional[Qualification] = Field(None, description="Educational milestone")
    is_student: Optional[bool] = Field(None, description="Enrolled student flag")

    # Employment & Career
    employment_status: Optional[EmploymentStatus] = Field(None, description="Current employment status")
    has_work_experience: Optional[bool] = Field(None, description="True if ever held a job, False if fresher")
    years_of_experience: Optional[int] = Field(None, ge=0, le=60, description="Total work experience in years")
    current_sector: Optional[OccupationSector] = Field(None, description="Current / past occupation sector")
    aspiring_sector: Optional[OccupationSector] = Field(None, description="Targeted sector for training/venture")
    benefit_intent: Optional[BenefitIntent] = Field(None, description="Specific assistance sought (credit, subsidy, etc.)")

    # Agriculture
    is_farmer: Optional[bool] = Field(None, description="Agricultural cultivator or landholder")
    land_holding_acres: Optional[float] = Field(None, ge=0, description="Cultivated land in acres")

    # Socio-Economic
    caste_category: Optional[CasteCategory] = Field(None, description="Reservation category")
    is_bpl: Optional[bool] = Field(None, description="Below Poverty Line cardholder")
    is_minority: Optional[bool] = Field(None, description="Minority community member")
    annual_family_income_inr: Optional[int] = Field(None, ge=0, description="Household annual income in INR")

    # Disability & Government Affiliation
    is_differently_abled: Optional[bool] = Field(None, description="Person with disability")
    disability_percentage: Optional[int] = Field(None, ge=0, le=100, description="Disability percentage if applicable")
    is_govt_employee: Optional[bool] = Field(None, description="Government employee flag")

    # Documents & Confirmation
    documents_held: Optional[List[str]] = Field(default_factory=list, description="List of held DocumentType IDs")
    confirmed: bool = Field(False, description="Must be true for /api/match submission")

    @field_validator("state_ut")
    @classmethod
    def validate_state(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        normalized = normalize_state(value)
        if normalized not in STATES:
            return None
        return normalized

    @model_validator(mode="after")
    def validate_consistency(self) -> "CitizenProfile":
        if self.years_of_experience is not None and self.years_of_experience > 0:
            self.has_work_experience = True
        if self.has_work_experience is False:
            self.years_of_experience = 0
        if self.disability_percentage is not None and not self.is_differently_abled:
            self.is_differently_abled = True
        if self.is_farmer and not self.current_sector:
            self.current_sector = "agriculture"
        return self


class ProfileExtractRequest(BaseModel):
    text: Optional[str] = Field(None, max_length=5000, description="Citizen intake conversational text")
    transcript: Optional[str] = Field(None, max_length=5000, description="Speech transcript")
    existing_profile: Optional[CitizenProfile] = None


class ProfileExtractResponse(BaseModel):
    profile: CitizenProfile
    confidence_by_field: Dict[str, Optional[float]] = {}
    raw_phrases_by_field: Dict[str, Optional[str]] = {}
    transcript: str = ""
    is_insufficient: bool = False
    clarification_prompt: Optional[str] = None
    suggested_fields: List[str] = []
