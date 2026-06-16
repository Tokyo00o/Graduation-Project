export interface Project {
  id: string;
  name: string;
  description: string;
  owner_id: string;
  created_at: string;
  updated_at: string;
}

export interface ConversationTurn {
  role: 'user' | 'assistant';
  content: string;
}

export interface Seed {
  id: string;
  project_id: string;
  content: string;
  version: number;
  tags: string;
  is_multi_turn: boolean;
  conversation: string;
  created_at: string;
  updated_at: string;
}

export interface SeedLibraryItem {
  id: string;
  content: string;
  category: string;
  tags: string;
  difficulty: string;
  effectiveness: number;
  source: string;
  is_preset: boolean;
  is_multi_turn: boolean;
  conversation: string;
  version: number;
  created_at: string;
  updated_at: string;
}

export interface Job {
  id: string;
  project_id: string;
  strategy: string;
  status: string;
  budget: number;
  queries_used: number;
  asr: number;
  target_model: string;
  judge: string;
  created_at: string;
  updated_at: string;
  completed_at: string | null;
}

export interface MutationInfo {
  id: string;
  iteration_id: string;
  parent_seed_id: string;
  mutation_type: string;
  content: string;
  conversation?: ConversationTurn[];
  created_at: string;
}

export interface ResponseInfo {
  id: string;
  iteration_id: string;
  template_id: string;
  response: string;
  latency: number;
  status_code: string;
  created_at: string;
}

export interface JudgmentInfo {
  id: string;
  iteration_id: string;
  response_id: string;
  classification: string;
  confidence: number;
  explanation: string;
  judge_model: string;
  created_at: string;
}

export interface IterationResult {
  id: string;
  job_id: string;
  iteration_number: number;
  reward: number;
  status: string;
  created_at: string;
  mutation: MutationInfo | null;
  response: ResponseInfo | null;
  judgment: JudgmentInfo | null;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  limit: number;
}

export interface Benchmarks {
  benchmarks: { id: string; name: string; description: string }[];
}
