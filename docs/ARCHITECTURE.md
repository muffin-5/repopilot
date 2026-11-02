# Architecture Documentation

## System Overview

RepoPilot is designed as a modular, extensible system with clear separation of concerns.

## Data Flow

### 1. Repository Ingestion Flow

```
User submits GitHub URL
        │
        ▼
┌─────────────────┐
│   Clone Repo    │  (GitPython)
│   to temp dir   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Parse Files    │  (Tree-sitter / regex)
│  into Chunks    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐     ┌──────────────┐
│  Generate       │────▶│ Vector Store  │
│  Embeddings     │     │ (Qdrant/Mem)  │
└────────┬────────┘     └──────────────┘
         │
         ▼
┌─────────────────┐     ┌──────────────┐
│  Build BM25     │────▶│ BM25 Index   │
│  Index          │     │ (In-memory)  │
└─────────────────┘     └──────────────┘
```

### 2. Question Answering Flow

```
User asks a question
        │
        ▼
┌─────────────────────┐
│  Select Retrieval   │  (vector / bm25 / hybrid)
│  Strategy           │
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  Retrieve Relevant  │  Top-K chunks
│  Code Chunks        │
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  Build Context      │  System prompt + retrieved code
│  Prompt             │
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  LLM Generation     │  OpenAI-compatible API
│                     │
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  Parse & Validate   │  Extract citations, validate
│  Response           │  file paths and line numbers
└────────┬────────────┘
         │
         ▼
   Return answer with
   citations & metrics
```

### 3. Bug Investigation Flow

```
User submits bug report
        │
        ▼
┌─────────────────────┐
│  Parse Bug Report   │  Extract keywords, error type
│                     │
└────────┬────────────┘
         │
         ▼
┌─────────────────────────────────┐
│  ReAct Loop (max 10 iterations) │
│                                  │
│  Think: What should I look at?   │
│    │                             │
│    ▼                             │
│  Act: Call a tool                │
│  ┌─ search_code                  │
│  ├─ read_file                    │
│  ├─ find_tests                   │
│  ├─ analyze_dependencies         │
│  └─ suggest_patch                │
│    │                             │
│    ▼                             │
│  Observe: Process tool output    │
│    │                             │
│    ▼                             │
│  Decide: Continue or conclude    │
└────────────┬────────────────────┘
             │
             ▼
    Return analysis with
    patches & test suggestions
```

## Retrieval Strategy Comparison

### Baseline A: Fixed-Size + Vector

- **Chunking**: Split files into 512-token windows with 50-token overlap
- **Search**: Cosine similarity against embedded query
- **Pros**: Simple, no language-specific logic needed
- **Cons**: Chunks may split functions, lose structural context

### Baseline B: AST-Aware + Vector

- **Chunking**: Extract function/class definitions using AST/regex
- **Search**: Cosine similarity against embedded query
- **Pros**: Preserves semantic units, chunks are meaningful
- **Cons**: Misses cross-function patterns, no keyword matching

### Proposed: AST-Aware + Hybrid (BM25 + Vector)

- **Chunking**: Extract function/class definitions using AST/regex
- **Search**: Reciprocal Rank Fusion of BM25 and vector results
- **Pros**: Combines exact keyword matching with semantic similarity
- **Cons**: More complex, slightly higher latency

## Security Considerations

1. **Untrusted Input**: Repository content is treated as untrusted. File contents are never executed.
2. **Prompt Injection**: System prompts include defenses against manipulation via repository content.
3. **Sandboxed Execution**: Agent test execution runs only approved commands.
4. **API Key Protection**: LLM API keys are stored in environment variables, never committed.
5. **Input Validation**: All API inputs are validated via Pydantic schemas.
