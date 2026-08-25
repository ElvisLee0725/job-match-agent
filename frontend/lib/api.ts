const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export interface StructuredProfile {
  skills: string[];
  experience_years: number;
  seniority: string;
  domains: string[];
  summary: string;
}

export interface ProfileResponse {
  id: number;
  raw_resume_text: string;
  background_text: string;
  behavioral_answers: string[];
  structured_profile: StructuredProfile;
  us_only: boolean;
  preferred_states: string[];
  created_at: string;
  updated_at: string;
}

export interface JobStructuredData {
  requirements: string[];
  responsibilities: string[];
  seniority: string;
  domain: string;
}

export interface JobPostingResponse {
  id: number;
  company: string;
  source_type: "scraped" | "manual_url";
  source_url: string;
  external_id: string | null;
  title: string;
  location: string | null;
  raw_description: string;
  structured: JobStructuredData;
  scraped_at: string;
}

export interface MatchPickResponse {
  job_posting_id: number;
  rank: number;
  fit_score: number;
  rationale: string;
  title: string;
  company: string;
  location: string | null;
  source_url: string;
}

export interface MatchRunResponse {
  match_run_id: number;
  company: string;
  run_at: string;
  results: MatchPickResponse[];
}

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, init);
  if (!response.ok) {
    let detail = response.statusText;
    try {
      const body = await response.json();
      detail = body.detail ?? detail;
    } catch {
      // response wasn't JSON — fall back to statusText
    }
    throw new ApiError(response.status, detail);
  }
  return (await response.json()) as T;
}

export async function getProfile(): Promise<ProfileResponse | null> {
  try {
    return await request<ProfileResponse>("/api/profile");
  } catch (err) {
    if (err instanceof ApiError && err.status === 404) return null;
    throw err;
  }
}

export async function uploadProfile(
  resumeFile: File,
  backgroundText: string,
  behavioralAnswers: string[],
  usOnly: boolean = true,
  preferredStates: string[] = []
): Promise<ProfileResponse> {
  const formData = new FormData();
  formData.append("resume_file", resumeFile);
  formData.append("background_text", backgroundText);
  for (const answer of behavioralAnswers) {
    formData.append("behavioral_answers", answer);
  }
  formData.append("us_only", String(usOnly));
  for (const state of preferredStates) {
    formData.append("preferred_states", state);
  }
  return request<ProfileResponse>("/api/profile/upload", {
    method: "POST",
    body: formData,
  });
}

export async function updateProfile(payload: {
  background_text?: string;
  behavioral_answers?: string[];
  us_only?: boolean;
  preferred_states?: string[];
}): Promise<ProfileResponse> {
  return request<ProfileResponse>("/api/profile", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export async function scrapeJobs(payload: {
  company_name: string;
  query?: string;
  limit?: number;
}): Promise<JobPostingResponse[]> {
  return request<JobPostingResponse[]>("/api/jobs/scrape", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export async function listJobs(company: string): Promise<JobPostingResponse[]> {
  return request<JobPostingResponse[]>(`/api/jobs?company=${encodeURIComponent(company)}`);
}

export async function parseJobUrl(payload: {
  url: string;
  company: string;
}): Promise<JobPostingResponse> {
  return request<JobPostingResponse>("/api/jobs/parse-url", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export async function runMatch(payload: {
  company_name: string;
  top_n?: number;
}): Promise<MatchRunResponse> {
  return request<MatchRunResponse>("/api/match/run", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export async function getLatestMatch(company: string): Promise<MatchRunResponse | null> {
  try {
    return await request<MatchRunResponse>(`/api/match/latest?company=${encodeURIComponent(company)}`);
  } catch (err) {
    if (err instanceof ApiError && err.status === 404) return null;
    throw err;
  }
}
