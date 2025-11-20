import api from './api';

export interface AIProvider {
  id?: number;
  provider_name: string;
  provider_display_name: string;
  api_endpoint: string;
  api_key: string;
  is_active: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface AIModel {
  id?: number;
  model_name: string;
  model_display_name: string;
  provider_id: number;
  system_prompt: string;
  user_prompt_template: string;
  max_tokens: number;
  temperature: number;
  is_active: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface ERPDatabase {
  id?: number;
  config_name: string;
  host: string;
  port: number;
  database_name: string;
  username: string;
  password: string;
  sql_query_for_sqls: string;
  is_active: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface CheckRequest {
  sql_statement: string;
  model_id: number;
  erp_config_id?: number;  // 用于自动执行EXPLAIN
  explain_result?: string;
}

export interface BatchCheckRequest {
  sql_statements: { sql: string; explain_result?: string }[];
  model_id: number;
  erp_config_id?: number;
}

export interface CheckAllRequest {
  erp_config_id: number;
  model_id: number;
  auto_explain?: boolean;
}

export interface CheckRecord {
  id: number;
  batch_id: string;
  original_sql: string;
  sql_hash: string;
  check_type: string;
  ai_model_id: number;
  ai_check_result?: string;
  explain_result?: string;
  performance_metrics?: any;
  check_status: string;
  error_message?: string;
  check_duration?: number;
  created_at: string;
  checked_at?: string;
}

export interface BatchProgress {
  batch_id: string;
  total_count: number;
  completed_count: number;
  success_count: number;
  failed_count: number;
  progress: number;
  remaining_time?: number;
  status: string;
}

// AI Provider APIs
export const getProviders = () => api.get<AIProvider[]>('/config/providers');
export const createProvider = (data: AIProvider) => api.post('/config/providers', data);
export const updateProvider = (id: number, data: AIProvider) => api.put(`/config/providers/${id}`, data);
export const deleteProvider = (id: number) => api.delete(`/config/providers/${id}`);

// AI Model APIs
export const getModels = () => api.get<AIModel[]>('/config/models');
export const createModel = (data: AIModel) => api.post('/config/models', data);
export const updateModel = (id: number, data: AIModel) => api.put(`/config/models/${id}`, data);
export const deleteModel = (id: number) => api.delete(`/config/models/${id}`);

// ERP Database APIs
export const getDatabases = () => api.get<ERPDatabase[]>('/config/erp-databases');
export const createDatabase = (data: ERPDatabase) => api.post('/config/erp-databases', data);
export const updateDatabase = (id: number, data: ERPDatabase) => api.put(`/config/erp-databases/${id}`, data);
export const deleteDatabase = (id: number) => api.delete(`/config/erp-databases/${id}`);
export const getERPSQLs = (configId: number) => api.get(`/config/erp-databases/${configId}/sqls`);
export const testERPConnection = (configId: number) => api.post(`/config/erp-databases/${configId}/test`);

// Check APIs
export const checkSQL = (data: CheckRequest) => api.post('/check/single', data);
export const batchCheck = (data: BatchCheckRequest) => api.post('/check/batch', data);
export const checkAllFromERP = (data: CheckAllRequest) => api.post('/check/all', data);
export const getBatchProgress = (batchId: string) => api.get<BatchProgress>(`/check/progress/${batchId}`);

// History APIs
export const getCheckRecords = (params?: any) => api.get<CheckRecord[]>('/history/records', { params });
export const getCheckRecord = (id: number) => api.get<CheckRecord>(`/history/records/${id}`);
export const getBatchRecords = (batchId: string) => api.get<CheckRecord[]>(`/history/batch/${batchId}`);

// Export APIs
export const exportToExcel = (batchId: string) => 
  api.get(`/export/excel/${batchId}`, { responseType: 'blob' });
export const exportToPDF = (batchId: string) => 
  api.get(`/export/pdf/${batchId}`, { responseType: 'blob' });
