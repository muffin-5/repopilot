import { useState, useEffect, useCallback } from 'react';
import { listRepos, ingestRepo as apiIngestRepo, deleteRepo as apiDeleteRepo, getRepoStatus } from '../services/api';

export function useRepo() {
  const [repos, setRepos] = useState([]);
  const [activeRepo, setActiveRepo] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const refreshRepos = useCallback(async () => {
    try {
      const data = await listRepos();
      setRepos(data || []);
      if (data && data.length > 0 && !activeRepo) {
        const readyRepo = data.find((r) => r.status === 'ready' && r.chunk_count > 0) || data[0];
        setActiveRepo(readyRepo);
      }
    } catch (err) {
      console.error('Failed to load repositories:', err);
    }
  }, [activeRepo]);

  useEffect(() => {
    refreshRepos();
  }, [refreshRepos]);

  const selectRepo = useCallback((repoId) => {
    const found = repos.find((r) => r.repo_id === repoId);
    if (found) {
      setActiveRepo(found);
    }
  }, [repos]);

  const ingestRepo = useCallback(async (url, branch = 'main') => {
    setLoading(true);
    setError(null);
    try {
      const res = await apiIngestRepo(url, branch);
      await refreshRepos();
      if (res && res.repo_id) {
        selectRepo(res.repo_id);
      }
      return res;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [refreshRepos, selectRepo]);

  const deleteRepo = useCallback(async (repoId) => {
    setLoading(true);
    try {
      await apiDeleteRepo(repoId);
      setRepos((prev) => prev.filter((r) => r.repo_id !== repoId));
      if (activeRepo && activeRepo.repo_id === repoId) {
        setActiveRepo(repos.find((r) => r.repo_id !== repoId) || null);
      }
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [activeRepo, repos]);

  return {
    repos,
    activeRepo,
    loading,
    error,
    refreshRepos,
    selectRepo,
    ingestRepo,
    deleteRepo,
  };
}

export default useRepo;
