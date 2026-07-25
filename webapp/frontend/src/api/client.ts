import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
  timeout: 10000,
});

export const apiClient = {
  run: async (problemDir: string, timeoutSec: number = 5) => {
    const res = await api.post('/run/', { problem_dir: problemDir, timeout_sec: timeoutSec });
    return res.data;
  },
  bench: async (problemDir: string, iterations: number = 1000) => {
    const res = await api.post('/bench/', { problem_dir: problemDir, iterations });
    return res.data;
  },
  stress: async (problemDir: string, iterations: number = 1000, seed?: number, timeout: number = 2) => {
    const res = await api.post('/stress/', { problem_dir: problemDir, iterations, seed, timeout });
    return res.data;
  },
  trace: async (problemDir: string, testCaseInput?: string, breakpoints?: number[], watchExprs?: string[]) => {
    const res = await api.post('/trace/', { problem_dir: problemDir, test_case_input: testCaseInput, breakpoints, watch_exprs: watchExprs });
    return res.data;
  },
  getFiles: async (problemDir: string) => {
    const res = await api.get('/workspace/files', { params: { problem_dir: problemDir } });
    return res.data;
  },
  getProblems: async () => {
    const res = await api.get('/workspace/problems');
    return res.data;
  },
  saveCode: async (problemDir: string, content: string) => {
    const res = await api.post('/workspace/save', { problem_dir: problemDir, content });
    return res.data;
  },
  fetchProblem: async (problemId: string) => {
    const res = await api.post('/workspace/fetch', { problem_id: problemId });
    return res.data;
  },
  getTestCase: async (problemDir: string) => {
    const res = await api.get('/workspace/testcase', { params: { problem_dir: problemDir } });
    return res.data;
  },
  saveTestCase: async (problemDir: string, content: string) => {
    const res = await api.post('/workspace/testcase/save', { problem_dir: problemDir, content });
    return res.data;
  },
  getBrute: async (problemDir: string) => {
    const res = await api.get('/workspace/brute', { params: { problem_dir: problemDir } });
    return res.data;
  },
  saveBrute: async (problemDir: string, content: string) => {
    const res = await api.post('/workspace/brute/save', { problem_dir: problemDir, content });
    return res.data;
  },
  getSummary: async () => {
    const res = await api.get('/analytics/summary');
    return res.data;
  }
};
