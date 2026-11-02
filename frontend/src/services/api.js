import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 120000,
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    const message = error.response?.data?.detail || error.message || 'An unexpected error occurred';
    return Promise.reject(new Error(message));
  }
);

export async function ingestRepo(repoUrl, branch = 'main') {
  const response = await api.post('/api/repos/ingest', { repo_url: repoUrl, branch });
  return response.data;
}

export async function getRepoStatus(repoId) {
  const response = await api.get(`/api/repos/${repoId}/status`);
  return response.data;
}

export async function listRepos() {
  const response = await api.get('/api/repos');
  return response.data;
}

export async function deleteRepo(repoId) {
  const response = await api.delete(`/api/repos/${repoId}`);
  return response.data;
}

export async function sendChat(repoId, question, retrievalMode = 'hybrid') {
  const response = await api.post('/api/chat', {
    repo_id: repoId,
    question,
    retrieval_mode: retrievalMode,
  });
  return response.data;
}

export async function getChatHistory(repoId) {
  const response = await api.get(`/api/chat/history/${repoId}`);
  return response.data;
}

export async function investigateBug(repoId, bugDescription, errorMessage = '', stackTrace = '') {
  const response = await api.post('/api/agent/investigate', {
    repo_id: repoId,
    bug_description: bugDescription,
    error_message: errorMessage,
    stack_trace: stackTrace,
  });
  return response.data;
}

export async function runEvaluation(repoId, benchmarkFile = null, retrievalModes = ['hybrid']) {
  const response = await api.post('/api/eval/run', {
    repo_id: repoId,
    benchmark_file: benchmarkFile,
    retrieval_modes: retrievalModes,
  });
  return response.data;
}

export async function getEvalResults() {
  const response = await api.get('/api/eval/results');
  return response.data;
}

export async function compareConfigs(repoId, configs) {
  const response = await api.post('/api/eval/compare', {
    repo_id: repoId,
    configs,
  });
  return response.data;
}

export default api;
