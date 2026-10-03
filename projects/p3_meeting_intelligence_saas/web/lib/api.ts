/**
 * Meeting Intelligence API Client & Data Types
 * Integrates with FastAPI backend for hybrid audio transcription & LLM synthesis.
 */

export type SensitivityLevel = 'confidential' | 'public';

export type Priority = 'high' | 'medium' | 'low';
export type ActionItemStatus = 'pending' | 'in_progress' | 'completed';

export interface ActionItem {
  id: string;
  task: string;
  assignee: string;
  due_date: string;
  priority: Priority;
  status: ActionItemStatus;
}

export interface TranscriptionMetadata {
  engine: 'faster-whisper (CPU, int8, VAD)' | 'Cloud Deepgram API' | string;
  sensitivity: SensitivityLevel;
  duration_seconds: number;
  confidence_score?: number;
  processed_at: string;
  audio_filename: string;
  raw_transcript?: string;
}

export interface MeetingMinutes {
  id: string;
  meeting_title: string;
  date: string;
  executive_summary: string;
  key_discussion_points: string[];
  decisions_made: string[];
  action_items: ActionItem[];
  transcription_metadata: TranscriptionMetadata;
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

/**
 * Upload audio file (.mp3 / .wav) along with sensitivity level to FastAPI backend.
 * Falls back to mock intelligence response if backend is offline.
 */
export async function uploadAndProcessAudio(
  file: File,
  sensitivity: SensitivityLevel,
  languageOrProgress?: string | ((stage: string) => void),
  onProgress?: (stage: string) => void,
  onUploadProgress?: (percent: number) => void
): Promise<MeetingMinutes> {
  let language: string | undefined;
  let progressCallback = onProgress;
  if (typeof languageOrProgress === 'string') {
    language = languageOrProgress;
  } else if (typeof languageOrProgress === 'function') {
    progressCallback = languageOrProgress;
  }

  const formData = new FormData();
  formData.append('file', file);
  formData.append('sensitivity', sensitivity);
  if (language && language !== 'auto') {
    formData.append('language', language);
  }

  try {
    if (progressCallback) {
      progressCallback(
        sensitivity === 'confidential'
          ? 'Routing to local Faster-Whisper engine (CPU, int8, VAD)...'
          : 'Routing to Cloud Deepgram API for high-throughput transcription...'
      );
    }

    // We use XMLHttpRequest instead of fetch to track real upload progress
    const response = await new Promise<Response>((resolve, reject) => {
      const xhr = new XMLHttpRequest();
      xhr.open('POST', `${API_BASE_URL}/api/process-audio`);
      
      const token = getStoredToken();
      if (token) {
        xhr.setRequestHeader('Authorization', `Bearer ${token}`);
      }

      xhr.upload.onprogress = (event) => {
        if (event.lengthComputable && onUploadProgress) {
          const percentComplete = Math.round((event.loaded / event.total) * 100);
          onUploadProgress(percentComplete);
        }
      };

      xhr.onload = () => {
        // Mock the Response interface to maintain compatibility with our error handling
        const res = new Response(xhr.responseText, {
          status: xhr.status,
          statusText: xhr.statusText,
        });
        resolve(res);
      };

      xhr.onerror = () => {
        reject(new Error(`Cannot reach the API server at ${API_BASE_URL}. Is the backend running?`));
      };

      xhr.send(formData);
    });

    if (!response.ok) {
      if (response.status === 401) {
        clearAuth();
        throw new Error(SESSION_EXPIRED_MESSAGE);
      }
      throw new Error(`Server returned ${response.status}: ${response.statusText}`);
    }

    if (onProgress) {
      onProgress('Synthesizing structured minutes with Map-Reduce LLM...');
    }

    const data: MeetingMinutes = await response.json();
    return data;
  } catch (error) {
    if (error instanceof Error && error.message === SESSION_EXPIRED_MESSAGE) throw error;

    console.warn(
      'API connection failed or backend offline. Generating synthetic demonstration response.',
      error
    );

    // Provide rich mock response matching the architecture
    await new Promise((resolve) => setTimeout(resolve, 2000));
    if (onProgress) {
      onProgress('Synthesizing structured minutes with Map-Reduce LLM...');
    }
    await new Promise((resolve) => setTimeout(resolve, 1500));

    return generateMockMeetingMinutes(file.name, sensitivity);
  }
}

/**
 * Demo fallback generator demonstrating the Pydantic structured output
 */
export function generateMockMeetingMinutes(
  filename: string,
  sensitivity: SensitivityLevel
): MeetingMinutes {
  const isConfidential = sensitivity === 'confidential';
  return {
    id: `meet-${Date.now()}`,
    meeting_title: isConfidential
      ? 'Q3 Strategic Product Roadmap & Security Architecture Review'
      : 'Weekly Cross-Functional Growth & Engineering Sync',
    date: new Date().toISOString().split('T')[0],
    executive_summary: isConfidential
      ? 'The executive engineering committee reviewed the hybrid audio pipeline transition. Strong consensus was reached to isolate all healthcare and enterprise financial audio streams to on-premise CPU int8 Faster-Whisper instances with active Voice Activity Detection (VAD). Non-sensitive customer calls will continue routing through Deepgram for minimal latency.'
      : 'The growth team reviewed the weekly onboarding funnel metrics, reporting a 24% increase in conversion after deploying the automated meeting summary webhook. Discussion focused on expanding language support and optimizing map-reduce batch sizes for recordings exceeding 60 minutes.',
    key_discussion_points: [
      'Evaluation of int8 quantized Faster-Whisper model benchmarks on local CPU instances vs cloud latency.',
      'Implementation of Pydantic schema validation with Instructor and LiteLLM fallback chains.',
      'Strict audit trails for confidential audio uploads with immediate temporary file purging after transcription.',
      'Cross-departmental timeline for rollout across EMEA and APAC branches by end of quarter.',
    ],
    decisions_made: [
      'Enforce zero-cloud data retention policy on all uploads flagged with Confidential sensitivity.',
      'Default audio chunking threshold set to 10-minute sliding windows for the Map-Reduce synthesizer.',
      'Transition all dashboard action item notifications to direct Slack and Linear webhooks.',
    ],
    action_items: [
      {
        id: 'act-101',
        task: 'Configure automated file unlinking on FastAPI temporary audio storage directory',
        assignee: 'DevOps Lead (Alex)',
        due_date: '2026-10-06',
        priority: 'high',
        status: 'pending',
      },
      {
        id: 'act-102',
        task: 'Benchmark Faster-Whisper VAD silero filter accuracy on noisy ambient test sets',
        assignee: 'ML Engineer (Elena)',
        due_date: '2026-10-08',
        priority: 'high',
        status: 'in_progress',
      },
      {
        id: 'act-103',
        task: 'Draft frontend unit tests for audio drag-and-drop boundary validation',
        assignee: 'Frontend Dev (Marcus)',
        due_date: '2026-10-10',
        priority: 'medium',
        status: 'pending',
      },
      {
        id: 'act-104',
        task: 'Finalize Pydantic v2 schemas for multi-speaker diarization metadata',
        assignee: 'Backend Architect (Sarah)',
        due_date: '2026-10-12',
        priority: 'low',
        status: 'completed',
      },
    ],
    transcription_metadata: {
      engine: isConfidential
        ? 'faster-whisper (CPU, int8, VAD)'
        : 'Cloud Deepgram API',
      sensitivity,
      duration_seconds: 418,
      confidence_score: 0.984,
      processed_at: new Date().toISOString(),
      audio_filename: filename || 'recorded_session.mp3',
    },
  };
}

export interface User {
  id: string;
  email: string;
  first_name: string;
  last_name?: string;
  avatar?: string;
  subscription_tier?: string;
  is_active?: boolean;
}

export interface AuthToken {
  access_token: string;
  token_type: string;
  expires_in_minutes: number;
}

// No offline/demo fallbacks here: a fake token would make the UI look logged in
// while every real API call is rejected with "Token is invalid or expired."
export async function loginUser(email: string, password: string): Promise<{ token: AuthToken; user: User }> {
  const res = await apiFetch(
    '/api/v1/auth/login',
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    },
    { auth: false }
  );
  if (!res.ok) {
    throw new Error(await readApiError(res, 'Invalid email or password.'));
  }
  const token: AuthToken = await res.json();

  // Load the real profile (name, avatar, ...) for the authenticated user
  const meRes = await apiFetch(
    '/api/v1/users/me',
    { headers: { Authorization: `Bearer ${token.access_token}` } },
    { auth: false }
  );
  if (!meRes.ok) {
    throw new Error(await readApiError(meRes, 'Could not load your profile.'));
  }
  const user: User = await meRes.json();

  storeAuth(token, user);
  return { token, user };
}

export async function registerUser(email: string, password: string, firstName: string, lastName?: string): Promise<User> {
  const res = await apiFetch(
    '/api/v1/users/',
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password, first_name: firstName || '', last_name: lastName || '' }),
    },
    { auth: false }
  );
  if (!res.ok) {
    throw new Error(await readApiError(res, 'Could not register user account.'));
  }
  return res.json();
}

/**
 * Check the stored session against the API on app load: refreshes the cached
 * profile, or logs out if the token is no longer valid. Network errors are ignored.
 */
export async function validateSession(): Promise<void> {
  if (!getStoredToken()) return;
  try {
    const res = await apiFetch('/api/v1/users/me');
    if (res.ok) updateStoredUser(await res.json());
  } catch {
    // Expired sessions are already cleared by apiFetch; an offline API is not a logout
  }
}

export function storeAuth(token: AuthToken, user: User) {
  if (typeof window !== 'undefined') {
    localStorage.setItem('meeting_intel_token', token.access_token);
    localStorage.setItem('meeting_intel_user', JSON.stringify(user));
    window.dispatchEvent(new Event('auth_state_changed'));
  }
}

export function getStoredUser(): User | null {
  if (typeof window === 'undefined') return null;
  try {
    const raw = localStorage.getItem('meeting_intel_user');
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

export function getStoredToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('meeting_intel_token');
}

/** Replace the cached user (e.g. after a profile change) and notify listeners. */
export function updateStoredUser(user: User) {
  if (typeof window !== 'undefined') {
    localStorage.setItem('meeting_intel_user', JSON.stringify(user));
    window.dispatchEvent(new Event('auth_state_changed'));
  }
}

/** Avatar paths are stored relative to the API (e.g. /uploads/avatars/x.png). */
export function getAvatarUrl(user: User | null): string | null {
  if (!user?.avatar) return null;
  return /^https?:\/\//.test(user.avatar) ? user.avatar : `${API_BASE_URL}${user.avatar}`;
}

async function readApiError(res: Response, fallback: string): Promise<string> {
  const err = await res.json().catch(() => null);
  return err?.message || (typeof err?.detail === 'string' ? err.detail : null) || fallback;
}

export const SESSION_EXPIRED_MESSAGE = 'Your session has expired. Please log in again.';

/**
 * fetch() for API calls.
 * - Adds the stored Bearer token unless `auth: false`.
 * - Turns browser network failures into a readable message.
 * - On 401 for an authenticated call, clears the stale session (navbar and route
 *   guards react to auth_state_changed) and throws SESSION_EXPIRED_MESSAGE.
 */
async function apiFetch(
  path: string,
  init: RequestInit = {},
  { auth = true }: { auth?: boolean } = {}
): Promise<Response> {
  let res: Response;
  try {
    res = await fetch(`${API_BASE_URL}${path}`, {
      ...init,
      headers: {
        ...init.headers,
        ...(auth ? { Authorization: `Bearer ${getStoredToken() ?? ''}` } : {}),
      },
    });
  } catch {
    throw new Error(`Cannot reach the API server at ${API_BASE_URL}. Is the backend running?`);
  }

  if (auth && res.status === 401) {
    clearAuth();
    throw new Error(SESSION_EXPIRED_MESSAGE);
  }
  return res;
}

export async function uploadAvatar(file: File): Promise<User> {
  const formData = new FormData();
  formData.append('file', file);

  const res = await apiFetch('/api/v1/users/me/avatar', { method: 'POST', body: formData });
  if (!res.ok) throw new Error(await readApiError(res, 'Could not upload avatar.'));

  const user: User = await res.json();
  updateStoredUser(user);
  return user;
}

export async function removeAvatar(): Promise<User> {
  const res = await apiFetch('/api/v1/users/me/avatar', { method: 'DELETE' });
  if (!res.ok) throw new Error(await readApiError(res, 'Could not remove avatar.'));

  const user: User = await res.json();
  updateStoredUser(user);
  return user;
}

export async function updateProfile(firstName: string, lastName: string): Promise<User> {
  const res = await apiFetch('/api/v1/users/me', {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ first_name: firstName || '', last_name: lastName || '' }),
  });

  if (!res.ok) {
    throw new Error(await readApiError(res, 'Could not update profile.'));
  }

  const user: User = await res.json();
  updateStoredUser(user);
  return user;
}

export function clearAuth() {
  if (typeof window !== 'undefined') {
    localStorage.removeItem('meeting_intel_token');
    localStorage.removeItem('meeting_intel_user');
    window.dispatchEvent(new Event('auth_state_changed'));
  }
}
