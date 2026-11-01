import { CatalogStatus, CitizenProfile, MatchResponse, ProfileExtractResponse } from '../types';

const API_BASE = (import.meta as any).env?.VITE_API_BASE_URL || '/api';

async function fetchWithTimeout(
  url: string,
  options: RequestInit = {},
  timeoutMs: number = 12000
): Promise<Response> {
  const controller = new AbortController();
  const id = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const res = await fetch(url, {
      ...options,
      signal: controller.signal,
    });
    return res;
  } catch (err: any) {
    if (err.name === 'AbortError') {
      throw new Error(`Request to ${url} timed out after ${timeoutMs / 1000}s. Server may be cold-starting or unreachable.`);
    }
    throw err;
  } finally {
    clearTimeout(id);
  }
}

async function parseJsonResponse<T>(res: Response, fallbackError: string): Promise<T> {
  const contentType = (res.headers && typeof res.headers.get === 'function')
    ? (res.headers.get('content-type') || '')
    : 'application/json';
  if (!res.ok) {
    let errMessage = fallbackError;
    if (contentType.includes('application/json')) {
      const err = await res.json().catch(() => ({}));
      errMessage = err.error?.message || err.detail || `${fallbackError} (${res.status})`;
    } else {
      errMessage = `${fallbackError} (Status ${res.status})`;
    }
    throw new Error(errMessage);
  }

  if (!contentType.includes('application/json')) {
    throw new Error('Received non-JSON response from server. Check API routing or deployment configuration.');
  }

  return res.json();
}

export async function getCatalogStatus(): Promise<CatalogStatus> {
  const res = await fetchWithTimeout(`${API_BASE}/catalog/status`, {}, 8000);
  return parseJsonResponse<CatalogStatus>(res, 'Failed to fetch catalog status');
}

export async function extractProfile(
  text: string,
  existingProfile?: CitizenProfile | null
): Promise<ProfileExtractResponse> {
  const res = await fetchWithTimeout(
    `${API_BASE}/profile/extract`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        text,
        existing_profile: existingProfile || null,
      }),
    },
    10000
  );
  return parseJsonResponse<ProfileExtractResponse>(res, 'Failed to extract profile');
}

export async function extractProfileAudio(
  audioBlob: Blob,
  existingProfile?: CitizenProfile | null
): Promise<ProfileExtractResponse> {
  const formData = new FormData();
  formData.append('audio', audioBlob, 'recording.webm');
  if (existingProfile) {
    formData.append('existing_profile_json', JSON.stringify(existingProfile));
  }

  const res = await fetchWithTimeout(
    `${API_BASE}/profile/extract-audio`,
    {
      method: 'POST',
      body: formData,
    },
    12000
  );
  return parseJsonResponse<ProfileExtractResponse>(res, 'Failed to transcribe audio');
}

export async function matchSchemes(
  profile: CitizenProfile,
  previousUnlockedSlugs?: string[]
): Promise<MatchResponse> {
  const payload = {
    profile: { ...profile, confirmed: true },
    previous_unlocked_slugs: previousUnlockedSlugs || [],
  };

  const res = await fetchWithTimeout(
    `${API_BASE}/match`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    },
    12000
  );
  return parseJsonResponse<MatchResponse>(res, 'Failed to match schemes');
}

export async function explainScheme(slug: string, profile: CitizenProfile) {
  const res = await fetchWithTimeout(
    `${API_BASE}/explain`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ slug, profile }),
    },
    10000
  );
  return parseJsonResponse<any>(res, 'Failed to generate explanation');
}

export async function fetchSpeechAudio(text: string): Promise<Blob> {
  const res = await fetchWithTimeout(
    `${API_BASE}/tts`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text }),
    },
    8000
  );
  if (!res.ok) throw new Error('Audio synthesis failed');
  return res.blob();
}
