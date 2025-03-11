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
  tables: Array<{
    name: string;
    fields: Array<{
      name: string;
      type: string;
      description: string;
    }>;
  }>;
  relationships: Array<{
    from: string;
    to: string;
    type: string;
  }>;
  code_snippets: Array<{
    file: string;
    line: number;
    code: string;
    description: string;
  }>;
}

export interface User {
  id: string;
  email: string;
  name: string;
  role: 'admin' | 'user';
} 