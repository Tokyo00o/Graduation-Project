import axios from 'axios';

const api = axios.create({
  baseURL: '/api/v1',
  headers: { 'Content-Type': 'application/json' },
});

export default api;

export const projectsApi = {
  list: () => api.get('/projects').then(r => r.data),
  get: (id: string) => api.get(`/projects/${id}`).then(r => r.data),
  create: (data: { name: string; description?: string }) =>
    api.post('/projects', data).then(r => r.data),
  delete: (id: string) => api.delete(`/projects/${id}`),
};

export const seedsApi = {
  list: (projectId: string, params?: { tag?: string }) =>
    api.get(`/projects/${projectId}/seeds`, { params }).then(r => r.data),
  create: (projectId: string, data: { content: string; tags?: string[]; is_multi_turn?: boolean; conversation?: any[] }) =>
    api.post(`/projects/${projectId}/seeds`, data).then(r => r.data),
  delete: (projectId: string, seedId: string) =>
    api.delete(`/projects/${projectId}/seeds/${seedId}`),
  upload: (projectId: string, file: File) => {
    const fd = new FormData();
    fd.append('file', file);
    return api.post(`/projects/${projectId}/seeds/upload`, fd).then(r => r.data);
  },
  listWrappers: () => api.get('/projects/{projectId}/seeds/multi-turn/wrappers').then(r => r.data),
  convertToMultiTurn: (projectId: string, seedId: string, wrapper?: string) =>
    api.post(`/projects/${projectId}/seeds/${seedId}/convert-multi-turn`, null, {
      params: wrapper ? { wrapper } : {},
    }).then(r => r.data),
  convertBulkMultiTurn: (projectId: string, wrapper?: string, seedIds?: string[]) =>
    api.post(`/projects/${projectId}/seeds/multi-turn/convert-bulk`, null, {
      params: { wrapper: wrapper || '', seed_ids: seedIds?.join(',') || '' },
    }).then(r => r.data),
};

export const jobsApi = {
  list: (projectId: string) =>
    api.get(`/projects/${projectId}/jobs`).then(r => r.data),
  get: (jobId: string) => api.get(`/jobs/${jobId}`).then(r => r.data),
  create: (projectId: string, data: {
    strategy?: string;
    budget?: number;
    judge?: string;
    target_model?: string;
    seed_ids?: string[];
  }) => api.post(`/projects/${projectId}/jobs`, data).then(r => r.data),
  stop: (jobId: string) => api.post(`/jobs/${jobId}/stop`).then(r => r.data),
  results: (jobId: string, params?: { page?: number; limit?: number; sort?: string }) =>
    api.get(`/jobs/${jobId}/results`, { params }).then(r => r.data),
  mctsTree: (jobId: string) => api.get(`/jobs/${jobId}/mcts-tree`).then(r => r.data),
  report: (jobId: string) => api.get(`/jobs/${jobId}/report`).then(r => r.data),
};

export const judgesApi = {
  list: () => api.get('/judges').then(r => r.data),
  metrics: (jobId: string) => api.get(`/judges/metrics/${jobId}`).then(r => r.data),
};

export const benchmarksApi = {
  list: () => api.get('/benchmarks/public').then(r => r.data),
};

export const keysApi = {
  list: () => api.get('/keys').then(r => r.data),
  set: (provider: string, data: { api_key: string; label?: string }) =>
    api.put(`/keys/${provider}`, data).then(r => r.data),
  delete: (provider: string) => api.delete(`/keys/${provider}`),
  test: (provider: string) => api.post(`/keys/${provider}/test`).then(r => r.data),
};

export const providersApi = {
  list: () => api.get('/models/providers').then(r => r.data),
};

export const seedLibraryApi = {
  list: (params?: { category?: string; difficulty?: string; tag?: string; search?: string; preset_only?: boolean }) =>
    api.get('/seed-library', { params }).then(r => r.data),
  get: (id: string) => api.get(`/seed-library/${id}`).then(r => r.data),
  create: (data: { content: string; category: string; tags?: string[]; difficulty?: string; effectiveness?: number; source?: string }) =>
    api.post('/seed-library', data).then(r => r.data),
  update: (id: string, data: any) =>
    api.put(`/seed-library/${id}`, data).then(r => r.data),
  delete: (id: string) => api.delete(`/seed-library/${id}`),
  importToProject: (itemId: string, projectId: string) =>
    api.post(`/seed-library/${itemId}/import/${projectId}`).then(r => r.data),
  bulkImport: (items: any[]) =>
    api.post('/seed-library/bulk-import', { items }).then(r => r.data),
  bulkImportToProject: (projectId: string, items: any[]) =>
    api.post(`/seed-library/import-bulk/${projectId}`, { items }).then(r => r.data),
  categories: () => api.get('/seed-library/categories').then(r => r.data),
  loadPresets: () => api.post('/seed-library/load-presets').then(r => r.data),
  upload: (file: File) => {
    const fd = new FormData();
    fd.append('file', file);
    return api.post('/seed-library/upload', fd).then(r => r.data);
  },
};

export const schedulesApi = {
  list: (projectId: string) =>
    api.get(`/projects/${projectId}/schedules`).then(r => r.data),
  get: (id: string) => api.get(`/schedules/${id}`).then(r => r.data),
  create: (projectId: string, data: any) =>
    api.post(`/projects/${projectId}/schedules`, data).then(r => r.data),
  update: (id: string, data: any) =>
    api.put(`/schedules/${id}`, data).then(r => r.data),
  delete: (id: string) => api.delete(`/schedules/${id}`),
  toggle: (id: string) => api.post(`/schedules/${id}/toggle`).then(r => r.data),
  runNow: (id: string) => api.post(`/schedules/${id}/run-now`).then(r => r.data),
  testNotification: (id: string) => api.post(`/schedules/${id}/test-notification`).then(r => r.data),
};

export const alertsApi = {
  list: (params?: { project_id?: string; unread_only?: boolean; limit?: number }) =>
    api.get('/alerts', { params }).then(r => r.data),
  unreadCount: () => api.get('/alerts/unread-count').then(r => r.data),
  markRead: (id: string) => api.post(`/alerts/${id}/read`).then(r => r.data),
  markAllRead: () => api.post('/alerts/read-all').then(r => r.data),
  delete: (id: string) => api.delete(`/alerts/${id}`),
};

export const reportsApi = {
  get: (jobId: string) => api.get(`/reports/${jobId}`).then(r => r.data),
  summary: (params?: { limit?: number }) =>
    api.get('/reports/summary/all', { params }).then(r => r.data),
  compliance: (jobId: string) => api.get(`/reports/${jobId}/compliance`).then(r => r.data),
  frameworks: () => api.get('/reports/frameworks').then(r => r.data),
  exportJson: (jobId: string) =>
    api.get(`/reports/${jobId}/export/json`, { responseType: 'blob' }).then(r => r.data),
  exportCsv: (jobId: string) =>
    api.get(`/reports/${jobId}/export/csv`, { responseType: 'blob' }).then(r => r.data),
  exportHtml: (jobId: string) =>
    api.get(`/reports/${jobId}/export/html`, { responseType: 'blob' }).then(r => r.data),
  exportPdf: (jobId: string) =>
    api.get(`/reports/${jobId}/export/pdf`, { responseType: 'blob' }).then(r => r.data),
};
