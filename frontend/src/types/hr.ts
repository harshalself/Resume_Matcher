export interface Job {
  id: string;
  position: string;
  description: string;
  company: string;
  location: string;
  salary: string;
  last_date_to_apply: string;
  requirements?: string;
  created_at: string;
  is_active: boolean;
}

export interface JobApplication {
  id: string;
  candidate_id: string;
  job_id: string;
  status: string;
  match_percentage: number;
  skills: string;
  experience_years: number;
  applied_at: string;
  cover_letter?: string;
  resume_url?: string;
  profiles: {
    full_name: string;
    email: string;
  };
}

export interface JobFormData {
  position: string;
  description: string;
  company: string;
  location: string;
  salary: string;
  last_date_to_apply: string;
  requirements: string;
}
