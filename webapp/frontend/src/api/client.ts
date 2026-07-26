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
  saveProblemStatement: async (problemDir: string, content: string) => {
    const res = await api.post('/workspace/problem_statement/save', { problem_dir: problemDir, content });
    return res.data;
  },
  trace: async (problemDir: string, testCaseInput?: string, breakpoints?: number[], watchExprs?: string[]) => {
    const res = await api.post('/trace/', { problem_dir: problemDir, test_case_input: testCaseInput, breakpoints, watch_exprs: watchExprs });
    return res.data;
  },
  getProblems: async () => {
    const res = await api.get('/workspace/problems');
    return res.data;
  },
  deleteProblem: async (problemDir: string) => {
    const res = await api.post('/workspace/delete', { problem_dir: problemDir });
    return res.data;
  },
  resetProblems: async () => {
    const res = await api.post('/workspace/reset');
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
  saveTestCase: async (problemDir: string, content: string) => {
    const res = await api.post('/workspace/testcase/save', { problem_dir: problemDir, content });
    return res.data;
  },
  saveExpected: async (problemDir: string, content: string) => {
    const res = await api.post('/workspace/expected/save', { problem_dir: problemDir, content });
    return res.data;
  }
};
