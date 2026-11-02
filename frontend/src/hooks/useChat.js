import { useState, useCallback, useRef, useEffect } from 'react';
import { sendChat, getChatHistory } from '../services/api';

export function useChat(activeRepoId) {
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const abortControllerRef = useRef(null);

  useEffect(() => {
    if (activeRepoId) {
      loadHistory(activeRepoId);
    } else {
      setMessages([]);
    }
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, [activeRepoId]);

  const loadHistory = useCallback(async (repoId) => {
    try {
      const data = await getChatHistory(repoId);
      if (data && Array.isArray(data.messages)) {
        setMessages(data.messages);
      }
    } catch (err) {
      // History may not exist yet, that's fine
      setMessages([]);
    }
  }, []);

  const sendMessage = useCallback(async (question, retrievalMode = 'hybrid') => {
    if (!activeRepoId || !question.trim()) return;

    const userMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: question.trim(),
      timestamp: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setLoading(true);
    setError(null);

    try {
      abortControllerRef.current = new AbortController();
      const startTime = performance.now();
      const response = await sendChat(activeRepoId, question.trim(), retrievalMode);
      const latency = Math.round(performance.now() - startTime);

      const assistantMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.answer || response.content || 'No response received.',
        citations: response.citations || [],
        metadata: {
          confidence: response.confidence ?? null,
          retrievalMode: retrievalMode,
          latency: response.latency_ms || latency,
          tokensUsed: response.tokens_used ?? null,
        },
        timestamp: new Date().toISOString(),
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err) {
      setError(err.message);
      const errorMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: `I encountered an error processing your request: ${err.message}`,
        isError: true,
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setLoading(false);
      abortControllerRef.current = null;
    }
  }, [activeRepoId]);

  const clearMessages = useCallback(() => {
    setMessages([]);
    setError(null);
  }, []);

  return {
    messages,
    loading,
    error,
    sendMessage,
    clearMessages,
  };
}

export default useChat;
