export interface AuthResponse {
  access_token: string;
}

export interface DashboardStats {
  total_entries: number;
  recent_analyses: number;
  pending_reviews: number;
  active_users: number;
}

export interface DataDictionaryEntry {
  id: string;
  table_name: string;
  column_name: string;
  data_type: string;
  description: string;
  valid_values?: string[];
  relationships?: string[];
  source: string;
  version: string;
  created_at: string;
  updated_at: string;
}

export interface HistoryEntry {
  id: string;
  entry_id: string;
  changes: Record<string, any>;
  user: string;
  timestamp: string;
}

export interface Review {
  id: string;
  code_snippet: string;
  status: 'pending' | 'approved' | 'rejected';
  created_at: string;
  updated_at: string;
}

export interface ReviewDetail extends Review {
  comments: string[];
  ratings: number[];
  reviewer: string;
}

export interface AnalysisResult {
  data_dictionary: DataDictionaryEntry[];
  code_snippets: {
    file: string;
    line: number;
    snippet: string;
  }[];
  suggestions: string[];
} 