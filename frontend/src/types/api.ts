export interface ApiError {
  message: string;
  code: string;
  details?: any;
}

export interface ApiErrorResponse {
  response?: {
    data?: ApiError;
    status?: number;
    statusText?: string;
  };
}

export interface AuthResponse {
  token: string;
  user: User;
}

export interface DashboardStats {
  total_entries: number;
  recent_analyses: number;
  pending_reviews: number;
  active_users: number;
}

export interface DataDictionaryEntry {
  id: number;
  analysis_id?: number;
  table_name: string;
  column_name: string;
  data_type: string;
  description: string;
  valid_values?: any;
  relationships?: any;
  source?: string;
  version?: string;
  created_at: string;
  updated_at: string;
  created_by: number;
}

export interface HistoryEntry {
  id: number;
  timestamp: string;
  user: string;
  changes: {
    type: string;
    fields: string[];
  };
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

export interface TableField {
  name: string;
  type: string;
  description: string;
}

export interface TableInfo {
  name: string;
  fields: TableField[];
}

export interface Relationship {
  from: string;
  to: string;
  type: string;
}

export interface CodeSnippet {
  file: string;
  line: number;
  code: string;
  description: string;
}

export interface AnalysisResult {
  id: number;
  tables: Array<{
    name: string;
    fields: Array<{
      name: string;
      type: string;
      description: string;
    }>;
  }>;
  data_relationships: Array<{
    from: string;
    to: string;
    type: string;
  }>;
  important_code_snippets: Array<{
    snippet: string;
    explanation: string;
  }>;
  data_sources: Array<{
    name: string;
    type: string;
    description: string;
  }>;
  data_transformations: Array<{
    description: string;
    code?: string;
  }>;
  potential_reuse_opportunities: string[];
  documentation_summary: string;
  model_used?: string;
}

export interface User {
  id: number;
  email: string;
  name: string;
  role: 'admin' | 'user';
}

export interface QueryExecution {
  id: number;
  user_id: number;
  analysis_id?: number;
  execution_time: string;
  execution_status: 'success' | 'failed';
  execution_duration: number;
  error_message?: string;
}

export interface QueryStats {
  total_queries: number;
  successful_queries: number;
  failed_queries: number;
  average_duration_ms: number;
} 