import { useState, useCallback } from 'react';
import { runEvaluation as apiRunEval, getEvalResults as apiGetResults, compareConfigs as apiCompare } from '../services/api';

export function useEval() {
  const [results, setResults] = useState(null);
  const [summary, setSummary] = useState(null);
  const [comparisons, setComparisons] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const runEvaluation = useCallback(async (repoId, benchmarkFile = null, modes = ['hybrid']) => {
    setLoading(true);
    setError(null);
    try {
      const data = await apiRunEval(repoId, benchmarkFile, modes);
      setSummary(data.summaries || {});
      setResults(data.results || {});
      return data;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const compareConfigurations = useCallback(async (repoId, modes = ['vector', 'bm25', 'hybrid']) => {
    setLoading(true);
    setError(null);
    try {
      const data = await apiCompare(repoId, modes);
      setComparisons(data.comparisons || {});
      return data;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchPastResults = useCallback(async () => {
    try {
      const data = await apiGetResults();
      return data;
    } catch (err) {
      console.error('Failed to fetch past eval runs:', err);
      return [];
    }
  }, []);

  return {
    results,
    summary,
    comparisons,
    loading,
    error,
    runEvaluation,
    compareConfigurations,
    fetchPastResults,
  };
}

export default useEval;
