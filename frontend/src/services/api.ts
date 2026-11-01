import { CatalogStatus, CitizenProfile, MatchResponse, ProfileExtractResponse } from '../types';

const API_BASE = '/api';

export async function getCatalogStatus(): Promise<CatalogStatus> {
  const res = await fetch(`${API_BASE}/catalog/status`);
  if (!res.ok) throw new Error('Failed to fetch catalog status');
  return res.json();
}

export async function extractProfile(
  text: string,
  existingProfile?: CitizenProfile | null
): Promise<ProfileExtractResponse> {
  const res = await fetch(`${API_BASE}/profile/extract`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      text,
      existing_profile: existingProfile || null,
    }),
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.error?.message || errorData.detail || 'Failed to extract profile');
  }
  return res.json();
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

  const res = await fetch(`${API_BASE}/profile/extract-audio`, {
    method: 'POST',
    body: formData,
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.error?.message || errorData.detail || 'Failed to transcribe audio');
  }
  return res.json();
}

export async function matchSchemes(
  profile: CitizenProfile,
  previousUnlockedSlugs?: string[]
): Promise<MatchResponse> {
  const payload = {
    profile: { ...profile, confirmed: true },
    previous_unlocked_slugs: previousUnlockedSlugs || [],
  };

  const res = await fetch(`${API_BASE}/match`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.error?.message || err.detail || 'Matching failed');
  }
  return res.json();
}

export async function explainScheme(slug: string, profile: CitizenProfile) {
  const res = await fetch(`${API_BASE}/explain`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ slug, profile }),
  });
  if (!res.ok) throw new Error('Failed to generate explanation');
  return res.json();
}

export async function fetchSpeechAudio(text: string): Promise<Blob> {
  const res = await fetch(`${API_BASE}/tts`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text }),
  });
  if (!res.ok) throw new Error('Audio synthesis failed');
  return res.blob();
}
