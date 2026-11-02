# RepoPilot – An AI Software Engineering Agent

## Project Overview

RepoPilot is a production-style GenAI system that understands, investigates, and helps fix unfamiliar codebases. It combines LLM + RAG, AI Agents, Evaluation, and Backend Engineering into a comprehensive AI software engineering tool.

### What It Does

Given a GitHub repository with hundreds of files, RepoPilot can answer questions like:

- "How does authentication work in this project?"
- "Why does this API return a 500 error?"
- "Which files would I need to change to add a new feature?"
- "Find the tests related to this function."
- "Suggest a fix for this bug and verify it by running the relevant tests."

RepoPilot inspects the actual repository, retrieves relevant code, calls tools to investigate problems, and produces answers backed by file paths and line numbers. For bugs, it can propose patches and run approved tests in an isolated environment.

---

## 1. Why This Is a Strong Choice for AI Engineer Placements

### Skills Demonstrated

| Skill | What the Implementation Demonstrates |
|-------|--------------------------------------|
| LLM application development | Prompting, structured output, model integration |
| RAG | Finding relevant code and documentation |
| Agentic workflows | Selecting and calling tools to investigate bugs |
| Information retrieval | Hybrid search, reranking, retrieval evaluation |
| AI reliability | Citations, abstention, hallucination tests |
| AI evaluation | Benchmarks, regression testing, comparisons |
| Software engineering | API design, security, deployment, automated tests |

---

## 2. Core Modules

### Module A – Repository Intelligence

The user submits a public GitHub repository. The system indexes its source code, README files, and documentation. It answers questions with links to the relevant files and line ranges.

**Core concepts:** AST-based code chunking, embeddings, hybrid search, citations.

### Module B – Bug Investigation Agent

Given a bug report, it searches for relevant functions, traces dependencies, locates tests, and produces a proposed fix. The initial implementation suggests patches rather than autonomously rewriting the repository.

**Core concepts:** Tool calling, workflow orchestration, state management, controlled execution.

### Module C – AI Quality Dashboard

Shows which questions the system answers correctly, whether citations are valid, response latency, and query cost. Compares different retrieval configurations and model choices.

**Core concepts:** Recall@k, MRR, groundedness, latency, cost, and automated regression tests.

---

## 3. Technical Architecture

```
React Frontend
├── Repository input
├── Chat interface
├── Code citations
└── Evaluation dashboard

Python + FastAPI Backend
├── Authentication
├── Request routing
└── API and workflow orchestration

Retrieval Pipeline
├── AST parsing (Tree-sitter)
├── BM25 (lexical search)
├── Vector search (embeddings)
└── Reranking

Agent Tools
├── Symbol search
├── File reading
├── Test discovery
└── Sandboxed test runs

Storage and Model Layer
├── PostgreSQL/pgvector or Qdrant
├── LLM API
├── Embeddings
└── Logs and evaluations
```

### Technology Stack

| Component | Technology |
|-----------|-----------|
| Frontend | React + Vite + CSS |
| Backend | Python + FastAPI |
| Code parsing | Tree-sitter |
| Search | BM25 + vector retrieval + optional reranker |
| Vector storage | Qdrant (or PostgreSQL with pgvector) |
| LLM | Hosted model behind a provider-independent interface |
| Agent workflow | Python functions; LangGraph if needed |
| Testing | Pytest + GitHub Actions |
| Deployment | Docker + hosted application service |

---

## 4. Research Component

### Research Question

> "Does syntax-aware chunking combined with hybrid retrieval improve code-question answering compared with conventional vector-only RAG?"

### Experimental Baselines

| Experiment | Configuration |
|-----------|---------------|
| Baseline A | Fixed-size chunks + vector search |
| Baseline B | Function/class-aware chunks + vector search |
| Proposed system | Function/class-aware chunks + BM25 and vector search + optional reranking |

### Evaluation Metrics

- **Retrieval:** Recall@5 and Mean Reciprocal Rank (MRR)
- **Answer quality:** Correctness, relevance, and support from retrieved evidence
- **Citation quality:** Whether the cited file and lines actually support the claim
- **Reliability:** Whether the system correctly declines to answer unanswerable questions
- **Efficiency:** Median latency, token usage, and approximate cost per query

---

## 5. Implementation Phases

### Phase 1 – Working RAG System
Ingest one public repository, parse files into meaningful chunks, index them, and answer questions with file-and-line citations. Implement the React UI and FastAPI service.

### Phase 2 – Improve Retrieval
Add lexical search, hybrid retrieval, and optionally reranking. Run initial benchmark and compare each configuration.

### Phase 3 – Add Debugging Workflow
Give the agent a small set of controlled tools. It should inspect the repository, find relevant tests, propose a patch, and run only explicitly approved commands in an isolated environment.

### Phase 4 – Make It Portfolio-Ready
Add automated evaluation and regression tests, structured logs, latency/cost tracking, Docker deployment, a clean README, an architecture diagram, and a short recorded demo.

---

## 6. Resume Entry Template

**RepoPilot – Repository-Aware AI Software Engineering Agent** | Python, FastAPI, React, RAG, Vector Search, LLMs

- Built an LLM-powered codebase assistant using AST-aware chunking and hybrid retrieval to answer repository questions with source-level citations.
- Developed a tool-using debugging workflow to identify relevant code, locate tests, and generate candidate patches with controlled test execution.
- Designed an evaluation benchmark of [N] questions and compared retrieval pipelines, achieving [measured Recall@5 / MRR] while tracking citation validity, latency, and inference cost.
- Implemented automated regression tests and containerized deployment to improve reproducibility and reliability.

---

## 7. What to Avoid

- Generic PDF chatbots
- Simple LLM API wrappers
- Multi-agent systems that only pass text between agents
- Training your own LLM (retrieval quality, tool design, evaluation, security, and deployment are better investments)

---

*This project complements traditional ML/computer vision projects by demonstrating modern LLM systems engineering.*
