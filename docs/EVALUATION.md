# Evaluation Guide

## Overview

RepoPilot includes a comprehensive evaluation framework for measuring retrieval quality, answer accuracy, and system efficiency. This guide explains how to create benchmarks, run evaluations, and interpret results.

## Research Question

> Does syntax-aware chunking combined with hybrid retrieval improve code-question answering compared with conventional vector-only RAG?

## Creating a Benchmark

### Question Format

Each benchmark is a JSON file with an array of questions:

```json
{
  "benchmark_name": "my_benchmark",
  "repository": "owner/repo-name",
  "questions": [
    {
      "id": "unique_id",
      "question": "Your question here",
      "expected_files": ["path/to/relevant/file.py"],
      "expected_answer_contains": ["keyword1", "keyword2"],
      "category": "architecture|function_location|dependency|test|multi_file|unanswerable",
      "difficulty": "easy|medium|hard"
    }
  ]
}
```

### Question Categories

| Category | Description | Example |
|----------|-------------|---------|
| `architecture` | Project structure & design patterns | "What design pattern is used for X?" |
| `function_location` | Finding specific functions | "Where is function X defined?" |
| `dependency` | Module dependencies & imports | "What does module X import?" |
| `test` | Test-related questions | "What tests exist for X?" |
| `multi_file` | Cross-file understanding | "Trace the data flow from A to B" |
| `unanswerable` | Features that don't exist | "How does GraphQL work here?" |

### Guidelines for Good Questions

1. **Be specific**: "Where is the user authentication function?" not "How does auth work?"
2. **Include unanswerable questions**: 20-25% should have no answer in the repo
3. **Cover multiple files**: Include questions requiring cross-file reasoning
4. **Vary difficulty**: Mix easy lookups with complex architectural questions
5. **Ground truth**: Manually verify expected_files before running

## Running Evaluations

### Single Configuration

```bash
# Via API
curl -X POST http://localhost:8000/api/eval/run \
  -H "Content-Type: application/json" \
  -d '{"repo_id": "repo_123", "benchmark_file": "sample_benchmark.json", "retrieval_modes": ["hybrid"]}'
```

### Comparison Mode

```bash
# Compare all three configurations
curl -X POST http://localhost:8000/api/eval/compare \
  -H "Content-Type: application/json" \
  -d '{"repo_id": "repo_123", "configs": ["vector", "bm25", "hybrid"]}'
```

## Metrics Explained

### Retrieval Metrics

**Recall@5**: Of the relevant files for a question, what fraction appears in the top 5 retrieved chunks?

$$\text{Recall@5} = \frac{|\text{relevant files} \cap \text{top-5 retrieved files}|}{|\text{relevant files}|}$$

**MRR (Mean Reciprocal Rank)**: Average of 1/rank for the first relevant result.

$$\text{MRR} = \frac{1}{|Q|} \sum_{i=1}^{|Q|} \frac{1}{\text{rank}_i}$$

### Answer Quality Metrics

**Citation Validity**: Does the cited file path and line range exist in the repository, and does the content at those lines match the citation?

**Groundedness**: Is the answer supported by the retrieved context? (Automated check: are key claims traceable to retrieved chunks?)

### Efficiency Metrics

**Latency**: End-to-end time from question submission to answer receipt.
- p50 (median) and p95 reported
- Breakdown: retrieval time vs. LLM generation time

**Token Usage**: Total prompt + completion tokens per query.

**Cost**: Estimated API cost per query based on model pricing.

## Interpreting Results

### What Good Looks Like

| Metric | Good | Acceptable | Poor |
|--------|------|------------|------|
| Recall@5 | > 0.8 | 0.5 - 0.8 | < 0.5 |
| MRR | > 0.6 | 0.3 - 0.6 | < 0.3 |
| Citation Validity | > 0.9 | 0.7 - 0.9 | < 0.7 |
| Latency (p50) | < 3s | 3-10s | > 10s |

### Common Failure Patterns

1. **Low Recall, High MRR**: System finds the right file but misses others → chunk size may be too large
2. **High Recall, Low MRR**: Relevant chunks retrieved but ranked poorly → improve reranking
3. **High Citation Invalid**: LLM hallucinating file paths → strengthen prompt instructions
4. **Poor on Multi-file**: System can't connect information across files → consider larger context windows

## Sample Output

```
Evaluation Summary
==================
Total Questions: 20
Retrieval Mode: hybrid

Retrieval Metrics:
  Recall@5:          0.72
  MRR:               0.58

Answer Quality:
  Citation Accuracy:  0.85
  Unanswerable Correct: 0.75

Efficiency:
  Median Latency:    2.3s
  Avg Tokens/Query:  1,847
  Avg Cost/Query:    $0.003

By Category:
  architecture:      Recall@5=0.80, MRR=0.67
  function_location: Recall@5=0.85, MRR=0.75
  dependency:        Recall@5=0.70, MRR=0.50
  test:              Recall@5=0.65, MRR=0.45
  multi_file:        Recall@5=0.55, MRR=0.40
  unanswerable:      Abstention=0.75
```
