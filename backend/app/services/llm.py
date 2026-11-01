"""
Unified LLM Service Module
Provides multimodal audio extraction, multi-turn profile merging,
sparse information sufficiency checks, deterministic fallback extraction,
and grounded explanation generation. Supports Gemini and OpenRouter.
"""

import base64
import json
import logging
import re
import urllib.request
import urllib.error
from typing import Any, Dict, List, Optional, Tuple

from ..config import settings
from ..models.profile import CitizenProfile, ProfileExtractResponse
from ..models.states import STATES, STATE_ABBREVIATIONS

logger = logging.getLogger("janseva.llm")

ANCHOR_FIELDS = [
    "state_ut", "age", "gender", "qualification", "annual_family_income_inr",
    "caste_category", "current_sector", "aspiring_sector", "benefit_intent",
    "employment_status", "is_farmer", "is_differently_abled", "is_bpl"
]


def call_llm(
    system_prompt: str,
    user_prompt: str,
    response_schema: Optional[Dict[str, Any]] = None,
    temperature: float = 0.0,
    inline_audio: Optional[Dict[str, str]] = None
) -> Optional[str]:
    """Routes LLM request to Google Gemini (if configured) or OpenRouter."""
    # 1. Try Gemini
    if settings.GEMINI_API_KEY and not "your_" in settings.GEMINI_API_KEY.lower():
        try:
            return _call_gemini(system_prompt, user_prompt, response_schema, temperature, inline_audio)
        except Exception as e:
            logger.warning(f"Gemini call failed: {e}. Trying OpenRouter fallback.")

    # 2. Try OpenRouter
    if settings.OPENROUTER_API_KEY and not "your_" in settings.OPENROUTER_API_KEY.lower():
        try:
            return _call_openrouter(system_prompt, user_prompt, temperature)
        except Exception as e:
            logger.warning(f"OpenRouter call failed: {e}.")

    return None


def _call_gemini(
    system: str,
    user: str,
    schema: Optional[Dict[str, Any]] = None,
    temp: float = 0.0,
    inline_data: Optional[Dict[str, str]] = None
) -> str:
    endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{settings.GEMINI_MODEL}:generateContent?key={settings.GEMINI_API_KEY}"
    parts: List[Dict[str, Any]] = [{"text": user}]
    if inline_data:
        parts.append({"inlineData": inline_data})

    gen_config: Dict[str, Any] = {"temperature": temp}
    if schema:
        gen_config["responseMimeType"] = "application/json"
        gen_config["responseSchema"] = schema

    body = json.dumps({
        "systemInstruction": {"parts": [{"text": system}]},
        "contents": [{"role": "user", "parts": parts}],
        "generationConfig": gen_config
    }).encode("utf-8")

    req = urllib.request.Request(endpoint, data=body, headers={"Content-Type": "application/json"}, method="POST")
    # Cap timeout at 8s to stay well below Vercel's 10s serverless ceiling
    with urllib.request.urlopen(req, timeout=8) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        return data["candidates"][0]["content"]["parts"][0]["text"]


def _call_openrouter(system: str, user: str, temp: float = 0.0) -> Optional[str]:
    url = f"{settings.OPENROUTER_BASE_URL.rstrip('/')}/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/JanSevaAI",
        "X-Title": "JanSeva AI"
    }
    models = list(dict.fromkeys([
        settings.OPENROUTER_MODEL,
        "nvidia/nemotron-3.5-lightning:free",
        "google/gemma-4-31b-it:free"
    ]))

    for model in models:
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user}
            ],
            "temperature": temp
        }
        try:
            req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=5) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode("utf-8"))
                    content = data["choices"][0]["message"]["content"]
                    if content:
                        return content
        except Exception as e:
            logger.warning(f"OpenRouter model {model} failed: {e}")
            continue
    return None


def merge_profiles(existing: Optional[CitizenProfile], new_facts: CitizenProfile) -> CitizenProfile:
    """Multi-turn profile merging: preserves previously confirmed facts while overlaying new ones."""
    if not existing:
        return new_facts

    merged = existing.model_dump()
    new_data = new_facts.model_dump(exclude_none=True)

    for k, v in new_data.items():
        if k == "documents_held" and isinstance(v, list):
            existing_docs = set(merged.get("documents_held") or [])
            merged["documents_held"] = sorted(list(existing_docs.union(set(v))))
        elif v is not None:
            merged[k] = v

    return CitizenProfile(**merged)


def check_information_sufficiency(profile: CitizenProfile) -> Tuple[bool, Optional[str], List[str]]:
    """Evaluates if citizen provided enough anchor details to generate meaningful matches."""
    known_anchors = [f for f in ANCHOR_FIELDS if getattr(profile, f, None) is not None]

    if len(known_anchors) >= 2:
        return False, None, []

    suggested = [
        f for f in ["state_ut", "age", "gender", "qualification", "annual_family_income_inr", "current_sector"]
        if getattr(profile, f, None) is None
    ]

    if len(known_anchors) == 1:
        f = known_anchors[0]
        val = getattr(profile, f)
        if f == "state_ut":
            prompt = f"Great, I see you are based in {val}! To find the exact welfare and subsidy schemes you qualify for, could you also share your age, education, or occupation?"
        elif f == "age":
            prompt = f"Thanks for sharing your age ({val})! Which State or Union Territory do you live in, and what is your education qualification or work background?"
        else:
            prompt = "Thank you for sharing your details. To match you with specific welfare programs, could you also share your State, age, and occupation or education?"
    else:
        prompt = "Welcome to JanSeva AI! To discover government schemes you qualify for, tell us a bit about yourself—like your State, age, education, and what kind of support (loans, scholarships, pensions) you are seeking."

    return True, prompt, suggested


def extract_profile_deterministic(text: str) -> Tuple[CitizenProfile, Dict[str, float], Dict[str, str]]:
    """High-precision regex/keyword extractor for offline or fallback execution."""
    profile = CitizenProfile()
    conf: Dict[str, float] = {}
    phrases: Dict[str, str] = {}
    lower = text.lower()

    # 1. Age
    m_age = (
        re.search(r'\b(\d{1,2})\s*(?:years?\s*old|yo|yr|age)\b', lower) or
        re.search(r'\bage\s*(?:is|:)?\s*(\d{1,2})\b', lower) or
        re.search(r'\b(?:i am|i\'m|am|aged?)\s+(\d{1,2})\b', lower)
    )
    if m_age:
        profile.age = int(m_age.group(1))
        conf["age"] = 0.98
        phrases["age"] = m_age.group(0)

    # 2. Gender
    if re.search(r'\b(female|woman|girl|mother|widow|she)\b', lower):
        profile.gender = "female"
        conf["gender"] = 0.98
        phrases["gender"] = "female"
    elif re.search(r'\b(male|man|boy|father|fellow|he)\b', lower):
        profile.gender = "male"
        conf["gender"] = 0.95
        phrases["gender"] = "male"
    elif re.search(r'\b(transgender|trans)\b', lower):
        profile.gender = "transgender"
        conf["gender"] = 0.95
        phrases["gender"] = "transgender"

    # 3. Marital Status
    if re.search(r'\b(widow|widowed)\b', lower):
        profile.marital_status = "widowed"
        conf["marital_status"] = 0.98
        phrases["marital_status"] = "widowed"
    elif re.search(r'\b(unmarried|single|never married)\b', lower):
        profile.marital_status = "never_married"
        conf["marital_status"] = 0.95
        phrases["marital_status"] = "unmarried"
    elif re.search(r'\b(married)\b', lower):
        profile.marital_status = "married"
        conf["marital_status"] = 0.95
        phrases["marital_status"] = "married"

    # 4. State / UT
    for state in STATES:
        if state.lower() in lower:
            profile.state_ut = state
            conf["state_ut"] = 0.98
            phrases["state_ut"] = state
            break
    if not profile.state_ut:
        words = re.findall(r'\b[a-z]{2}\b', lower)
        for w in words:
            if w in STATE_ABBREVIATIONS:
                profile.state_ut = STATE_ABBREVIATIONS[w]
                conf["state_ut"] = 0.95
                phrases["state_ut"] = STATE_ABBREVIATIONS[w]
                break

    # 5. Qualification
    if re.search(r'\b(postgraduate|post graduate|masters? degree|pg|m\.?tech|m\.?sc|mba)\b', lower):
        profile.qualification = "postgraduate"
        conf["qualification"] = 0.95
        phrases["qualification"] = "postgraduate"
    elif re.search(r'\b(bachelor|graduate|college degree|b\.?tech|b\.?sc|b\.?com|b\.?a|bca)\b', lower):
        profile.qualification = "graduate"
        conf["qualification"] = 0.98
        phrases["qualification"] = "graduate"
    elif re.search(r'\b(diploma|polytechnic|iti)\b', lower):
        profile.qualification = "diploma"
        conf["qualification"] = 0.95
        phrases["qualification"] = "diploma"
    elif re.search(r'\b(12th|class 12|hsc|higher secondary|intermediate|10\+2)\b', lower):
        profile.qualification = "12th_pass"
        conf["qualification"] = 0.95
        phrases["qualification"] = "12th_pass"
    elif re.search(r'\b(10th|class 10|matriculation|matric|sslc)\b', lower):
        profile.qualification = "10th_pass"
        conf["qualification"] = 0.95
        phrases["qualification"] = "10th_pass"

    # 6. Sector & Career Experience
    if re.search(r'\b(it sector|software|developer|programmer|computer|tech|coding)\b', lower):
        profile.current_sector = "it_tech"
        conf["current_sector"] = 0.95
        phrases["current_sector"] = "it_tech"
    elif re.search(r'\b(farmer|farming|agriculture|kisan|cultivator)\b', lower):
        profile.current_sector = "agriculture"
        profile.is_farmer = True
        conf["current_sector"] = 0.98
        phrases["current_sector"] = "agriculture"
    elif re.search(r'\b(artisan|craft|handloom|weaver|potter|carpenter|craftsman)\b', lower):
        profile.current_sector = "artisan_craft"
        conf["current_sector"] = 0.95
        phrases["current_sector"] = "artisan_craft"

    # Experience
    if re.search(r'\b(some experience|have experience|working experience|worked for|experienced)\b', lower):
        profile.has_work_experience = True
        conf["has_work_experience"] = 0.90
        phrases["has_work_experience"] = "has experience"
    elif re.search(r'\b(fresher|no experience|never had a job|first job|looking for first)\b', lower):
        profile.has_work_experience = False
        profile.years_of_experience = 0
        conf["has_work_experience"] = 0.95
        phrases["has_work_experience"] = "first time job seeker"

    # 7. Benefit Intent
    if re.search(r'\b(loan|credit|subsidy loan|finance|capital|funding)\b', lower):
        profile.benefit_intent = "credit_loan"
        conf["benefit_intent"] = 0.95
        phrases["benefit_intent"] = "loan"
    elif re.search(r'\b(scholarship|fellowship|fee waiver|stipend)\b', lower):
        profile.benefit_intent = "scholarship"
        conf["benefit_intent"] = 0.98
        phrases["benefit_intent"] = "scholarship"
    elif re.search(r'\b(pension)\b', lower):
        profile.benefit_intent = "pension"
        conf["benefit_intent"] = 0.98
        phrases["benefit_intent"] = "pension"

    # 8. Income
    m_inc = re.search(r'(?:rs\.?|inr|₹)?\s*(\d+(?:\.\d+)?)\s*(lakh|lac|k|thousand|crore)\b', lower) or re.search(r'(?:income|earning)\s*(?:is|of|about)?\s*(?:rs\.?|inr|₹)?\s*(\d+(?:,\d+)*)\b', lower)
    if m_inc:
        raw_num = m_inc.group(1).replace(",", "")
        unit = (m_inc.group(2) if m_inc.lastindex and m_inc.lastindex >= 2 else "").lower()
        try:
            val = float(raw_num)
            mult = 100000 if "la" in unit else (1000 if unit in ("k", "thousand") else (10000000 if "crore" in unit else 1))
            profile.annual_family_income_inr = int(val * mult)
            conf["annual_family_income_inr"] = 0.92
            phrases["annual_family_income_inr"] = m_inc.group(0)
        except Exception:
            pass

    return profile, conf, phrases


def extract_profile_with_llm(text: str, existing_profile: Optional[CitizenProfile] = None) -> ProfileExtractResponse:
    """Primary extraction via LLM with automatic fallback to deterministic parser."""
    system_prompt = (
        "You are an expert civic intake parser. Extract citizen attributes from English text into strict JSON.\n"
        "Return a JSON object conforming strictly to this format:\n"
        "{\n"
        '  "profile": {\n'
        '    "name": "Citizen name or null",\n'
        '    "age": 26,\n'
        '    "gender": "female" | "male" | "transgender" | null,\n'
        '    "marital_status": "never_married" | "married" | "widowed" | "divorced" | null,\n'
        '    "state_ut": "Official State name e.g. Gujarat or null",\n'
        '    "residence": "rural" | "urban" | null,\n'
        '    "qualification": "below_10th" | "10th_pass" | "12th_pass" | "diploma" | "graduate" | "postgraduate" | null,\n'
        '    "employment_status": "employed" | "self_employed" | "unemployed" | null,\n'
        '    "has_work_experience": true | false | null,\n'
        '    "years_of_experience": integer or null,\n'
        '    "current_sector": "it_tech" | "agriculture" | "artisan_craft" | "construction" | "manufacturing" | "services_retail" | "healthcare" | "education" | "unorganized" | "other" | null,\n'
        '    "aspiring_sector": same as above or null,\n'
        '    "benefit_intent": "credit_loan" | "scholarship" | "pension" | "housing" | "health_insurance" | "skill_training" | "subsidy_grant" | "general" | null,\n'
        '    "is_farmer": true | false | null,\n'
        '    "land_holding_acres": number or null,\n'
        '    "caste_category": "general" | "obc" | "sc" | "st" | "pvtg" | "dnt" | null,\n'
        '    "is_bpl": true | false | null,\n'
        '    "is_minority": true | false | null,\n'
        '    "annual_family_income_inr": integer (e.g. 1.5 lakh -> 150000) or null\n'
        '  },\n'
        '  "confidence_by_field": {"field": 0.95},\n'
        '  "raw_phrases_by_field": {"field": "verbatim words"}\n'
        "}\n"
        "Note: 'bachelor in IT' means qualification='graduate', current_sector='it_tech'.\n"
        "Do not invent facts not explicitly stated or implied."
    )

    llm_output = call_llm(system_prompt, text, temperature=0.0)
    if llm_output:
        try:
            cleaned = re.sub(r"^```(?:json)?", "", llm_output.strip(), flags=re.MULTILINE)
            cleaned = re.sub(r"```$", "", cleaned.strip(), flags=re.MULTILINE).strip()
            data = json.loads(cleaned)
            profile_data = data.get("profile", {})
            profile_obj = CitizenProfile(**profile_data)

            # Augment any fields left None by the LLM using deterministic fallback
            det_profile, det_conf, det_phrases = extract_profile_deterministic(text)
            for f in CitizenProfile.model_fields.keys():
                if getattr(profile_obj, f) is None and getattr(det_profile, f) is not None:
                    setattr(profile_obj, f, getattr(det_profile, f))

            merged = merge_profiles(existing_profile, profile_obj)
            is_insufficient, prompt, suggested = check_information_sufficiency(merged)

            # Sanitize confidence & phrases so None or invalid types never trigger validation errors
            raw_conf = data.get("confidence_by_field") or {}
            clean_conf = {
                str(k): float(v)
                for k, v in raw_conf.items()
                if v is not None and isinstance(v, (int, float))
            }
            for k, v in det_conf.items():
                if k not in clean_conf:
                    clean_conf[k] = v

            raw_phrases = data.get("raw_phrases_by_field") or {}
            clean_phrases = {
                str(k): str(v)
                for k, v in raw_phrases.items()
                if v is not None and str(v).strip() != ""
            }
            for k, v in det_phrases.items():
                if k not in clean_phrases:
                    clean_phrases[k] = v

            return ProfileExtractResponse(
                profile=merged,
                confidence_by_field=clean_conf,
                raw_phrases_by_field=clean_phrases,
                transcript=text,
                is_insufficient=is_insufficient,
                clarification_prompt=prompt,
                suggested_fields=suggested
            )
        except Exception as e:
            logger.warning(f"Error parsing LLM response: {e}. Falling back to deterministic.")

    # Deterministic fallback
    profile_obj, conf, phrases = extract_profile_deterministic(text)
    merged = merge_profiles(existing_profile, profile_obj)
    is_insufficient, prompt, suggested = check_information_sufficiency(merged)
    return ProfileExtractResponse(
        profile=merged,
        confidence_by_field=conf,
        raw_phrases_by_field=phrases,
        transcript=text,
        is_insufficient=is_insufficient,
        clarification_prompt=prompt,
        suggested_fields=suggested
    )


def extract_profile_from_audio(audio_bytes: bytes, mime_type: str) -> ProfileExtractResponse:
    """Multimodal audio extraction using Google Gemini inlineData."""
    encoded = base64.b64encode(audio_bytes).decode("ascii")
    system = "Transcribe the audio recording of an Indian citizen describing their situation and extract profile attributes into JSON."
    user_prompt = "Transcribe audio and extract CitizenProfile facts according to standard schema."
    output = call_llm(system, user_prompt, inline_audio={"mimeType": mime_type, "data": encoded})
    if output:
        try:
            cleaned = re.sub(r"^```(?:json)?", "", output.strip(), flags=re.MULTILINE)
            cleaned = re.sub(r"```$", "", cleaned.strip(), flags=re.MULTILINE).strip()
            data = json.loads(cleaned)
            transcript = data.get("transcript", "")
            profile_obj = CitizenProfile(**data.get("profile", {}))
            is_insufficient, prompt, suggested = check_information_sufficiency(profile_obj)
            return ProfileExtractResponse(
                profile=profile_obj,
                confidence_by_field=data.get("confidence_by_field", {}),
                raw_phrases_by_field=data.get("raw_phrases_by_field", {}),
                transcript=transcript,
                is_insufficient=is_insufficient,
                clarification_prompt=prompt,
                suggested_fields=suggested
            )
        except Exception:
            pass
    # If audio extraction fails
    return ProfileExtractResponse(
        profile=CitizenProfile(),
        transcript="Audio transcription unavailable",
        is_insufficient=True,
        clarification_prompt="We could not clearly transcribe your audio recording. Please try speaking again or type your details."
    )


def generate_grounded_explanation(
    scheme_name: str,
    verdict: str,
    criteria_results: List[Dict[str, Any]],
    benefit_snippet: str,
    contextual_reason: Optional[str] = None
) -> str:
    """Generates a verifiable explanation citing only verbatim passed/failed clauses."""
    passed = [c["quote"] for c in criteria_results if c.get("result") == "pass"]
    failed = [c["quote"] for c in criteria_results if c.get("result") == "fail"]
    unknown = [c["quote"] for c in criteria_results if c.get("result") == "unknown"]

    if verdict == "eligible":
        citation = f"\"{passed[0]}\"" if passed else "all mandatory guidelines"
        summary = (
            f"You are likely eligible for {scheme_name}. Your profile satisfies the stated requirements, "
            f"such as meeting: {citation}. "
        )
        if contextual_reason:
            summary += f"Specific alignment: {contextual_reason} "
        summary += f"Under this scheme: {benefit_snippet[:150]}."
    elif verdict == "needs_more_info":
        missing_clause = f"\"{unknown[0]}\"" if unknown else "administrative clauses"
        summary = (
            f"You may qualify for {scheme_name}, but additional verification is needed. "
            f"Specifically: {missing_clause}. Once confirmed, you can receive: {benefit_snippet[:120]}."
        )
    else:
        disqualifier = f"\"{failed[0]}\"" if failed else "key eligibility clauses"
        summary = (
            f"You are currently ineligible for {scheme_name} because you do not meet the condition: {disqualifier}."
        )

    return summary[:450]
