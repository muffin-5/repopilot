# RepoPilot – Autonomous AI Software Engineering Agent

RepoPilot is an end-to-end AI system designed to understand, investigate, and assist in fixing complex, unfamiliar codebases. Rather than acting as a shallow LLM wrapper over arbitrary text chunks, RepoPilot combines AST-aware syntax chunking, hybrid retrieval (BM25 + dense vector embeddings with Reciprocal Rank Fusion), and a tool-using ReAct debugging agent. It answers architectural questions with verified line-level source citations and generates candidate patches backed by related test discovery.

The project was built as an engineering project at IIT BHU to explore whether syntax-aware chunking combined with hybrid retrieval significantly improves code question answering and bug localization over conventional vector-only RAG pipelines.

---

## The Problem: Why Conventional RAG Fails on Code

Standard RAG architectures designed for text documents (PDFs, wikis) perform poorly on production codebases:

1. **Semantic Boundary Destruction**: Fixed token windows (e.g., 512 tokens with 50-token overlap) regularly slice functions, classes, and type definitions in half, severing local scope from signatures and decorators.
2. **Identifier Mismatch in Pure Dense Search**: Dense embeddings capture conceptual similarity well (e.g., "authentication logic") but struggle with exact code identifiers, method names, and import paths (e.g., `verify_jwt_token`, `app.middleware.cors`).
3. **Hallucinated Provenance**: Generative models frequently hallucinate non-existent line numbers or files unless constrained by verified citation bounds.
4. **Passive Generation vs. Active Investigation**: Solving bugs requires multi-step repository traversal (searching callers, checking definitions, locating regression tests) rather than single-turn text synthesis.

RepoPilot addresses these failures with a purpose-built code intelligence pipeline.

---

## Architecture & System Design

```
                     +---------------------------------------+
                     |       React 18 + Vite Web App         |
                     |  Repo Manager | Chat | Agent | Eval   |
                     +-------------------+-------------------+
                                         |
                                         | REST API (HTTP / JSON)
                                         v
                     +---------------------------------------+
                     |        FastAPI Backend Service        |
                     | Request Routing | Session State | DTO |
                     +-------------------+-------------------+
                                         |
     +-----------------------------------+-----------------------------------+
     |                                   |                                   |
     v                                   v                                   v
+------------------------+  +------------------------+  +------------------------+
|   Retrieval Pipeline   |  |   ReAct Debug Agent    |  |  Evaluation Framework  |
| - AST / Syntax Chunking|  | - search_code          |  | - Recall@5 & MRR       |
| - BM25Okapi (Lexical)  |  | - read_file_snippet    |  | - Citation Validity    |
| - Dense Vector Store   |  | - find_related_tests   |  | - Abstention Accuracy  |
| - Reciprocal Rank Fuse |  | - analyze_imports      |  | - Latency & Cost Track |
+------------------------+  | - synthesize_patch     |  +------------------------+
                            +------------------------+
                                         |
                                         v
                     +---------------------------------------+
                     |   LLM & Model Orchestration Layer     |
                     | Google Gemini / OpenAI Provider Proxy |
                     +---------------------------------------+
```

---

## Core Modules

### 1. Module A – Repository Intelligence & Hybrid RAG

* **AST-Aware Code Parsing**: Implements `ASTChunker` to extract whole function definitions, class declarations, and method bodies with complete start/end line provenance. A regex-based AST fallback ensures language support across Python, TypeScript, JavaScript, Go, and Rust without requiring native compiler bindings.
* **Hybrid Retrieval (RRF)**: Merges sparse lexical search (BM25Okapi tailored with camelCase and snake_case identifier tokenization) and dense semantic vectors using Reciprocal Rank Fusion:
  
  $$\text{RRF Score}(d) = \sum_{m \in \{\text{vector}, \text{bm25}\}} \frac{w_m}{k + \text{rank}_m(d)}$$

* **In-Memory & Qdrant Vector Stores**: Connects to Qdrant in production with an in-memory NumPy vector store fallback for self-contained local testing and zero-dependency benchmarking.
* **Verified Citation Engine**: Answers are constrained to retrieved snippets. The engine cross-checks cited line ranges against physical file bounds before returning responses to the user.

### 2. Module B – Bug Investigation Agent

An autonomous agent running a bounded ReAct (Reasoning + Action) loop to investigate issue reports and runtime traces:

* **Tool Registry**:
  * `search_code`: Executes hybrid queries to locate candidate modules.
  * `read_file_snippet`: Reads bounded line ranges with path traversal protection.
  * `find_related_tests`: Discovers test suites referencing the affected symbols.
  * `analyze_imports`: Maps module dependencies and call chains.
  * `synthesize_patch`: Generates unified diff proposals with root cause analysis.
* **Sandboxed Execution**: Prevents destructive repository rewrites by outputting structured patch proposals rather than applying unverified edits directly.

### 3. Module C – AI Quality & Ablation Dashboard

Rather than evaluating the system on subjective impressions, RepoPilot includes a quantitative evaluation runner:

* **Retrieval Metrics**: Measures Recall@5 and Mean Reciprocal Rank (MRR) across ground-truth multi-file questions.
* **Groundedness & Citation Accuracy**: Evaluates whether cited source ranges contain the supporting code logic.
* **Abstention Reliability**: Explicitly tests hallucination resistance by submitting unanswerable queries (e.g., asking for GraphQL configurations in a REST-only repo) and verifying that the system declines to fabricate facts.
* **Cost & Latency Tracking**: Profiles end-to-end response times and token expenditure per query.

---

## Empirical Benchmark & Ablation Study

We framed our evaluation around the core research question:

> *Does syntax-aware chunking combined with hybrid retrieval improve code question answering over conventional vector-only RAG?*

We benchmarked three configurations on our standardized evaluation set:

| Configuration | Chunking Strategy | Retrieval Mechanism | Recall@5 | MRR | Citation Validity | Median Latency |
|:---|:---|:---|:---:|:---:|:---:|:---:|
| **Baseline A** | Fixed Window (512 tokens) | Vector Only (Cosine) | 0.54 | 0.41 | 68.2% | 820 ms |
| **Baseline B** | AST-Aware (Function/Class) | Vector Only (Cosine) | 0.68 | 0.55 | 86.4% | 890 ms |
| **Proposed** | **AST-Aware (Function/Class)** | **Hybrid (BM25 + Vector RRF)** | **0.84** | **0.72** | **95.1%** | **1,020 ms** |

### Key Takeaways from the Experiments:
1. **AST Chunking prevents broken scope**: Preserving method bodies and docstrings improved baseline retrieval recall by +14 percentage points over sliding token windows.
2. **BM25 captures identifier lookups**: Questions querying specific symbols (e.g., `verify_token` or `@router.post`) failed frequently with pure vector search due to vector embedding dilution. Adding BM25 raised Recall@5 to 84%.
3. **Abstention prevents hallucinations**: On unanswerable benchmark questions, the grounding system achieved 90%+ abstention accuracy, acknowledging missing evidence instead of inventing implementation details.

---

## Tech Stack

| Layer | Technologies |
|:---|:---|
| **Backend** | Python 3.11+, FastAPI, Pydantic v2, Uvicorn, HTTPX |
| **Frontend** | React 18, Vite, Lucide Icons, React Markdown |
| **Parsing & Chunking** | Tree-sitter, Regex AST Grammar Parsers |
| **Search & Storage** | BM25Okapi (rank-bm25), NumPy In-Memory Store, Qdrant |
| **Embeddings & LLM** | Sentence-Transformers (`all-MiniLM-L6-v2`), Google Gemini (`gemini-3.5-flash-lite`, `gemini-1.5-pro`), OpenAI API interface |
| **Testing & CI** | Pytest, Pytest-AsyncIO, GitHub Actions |
| **Deployment** | Docker, Docker Compose, Nginx |

---

## Project Structure

```
repopilot/
|-- backend/
|   |-- app/
|   |   |-- agents/            # Bug investigation ReAct agent & tools
|   |   |-- api/               # FastAPI routers (repos, chat, agent, eval)
|   |   |-- core/              # Config, settings, dependency injection
|   |   |-- evaluation/        # Benchmark runner & metrics suite (Recall@k, MRR)
|   |   |-- models/            # Pydantic schemas for requests and responses
|   |   |-- retrieval/         # BM25, VectorStore, HybridRetriever, Embeddings
|   |   |-- services/          # RepoService, ChatService, LLMService
|   |   `-- utils/             # ASTChunker and FixedSizeChunker
|   |-- tests/                 # Unit & integration test suite (11 tests)
|   |-- Dockerfile
|   `-- requirements.txt
|-- frontend/
|   |-- src/
|   |   |-- components/        # Header, Sidebar, ChatMessage, CodeBlock, CitationCard
|   |   |-- hooks/             # useChat, useRepo, useEval
|   |   |-- pages/             # HomePage, ChatPage, AgentPage, EvalPage
|   |   `-- services/          # Axios API client
|   |-- Dockerfile
|   |-- nginx.conf
|   `-- package.json
|-- docs/
|   |-- ARCHITECTURE.md        # Detailed component diagrams and data flow
|   |-- EVALUATION.md          # Benchmark methodology and failure mode analysis
|   `-- RepoPilot_Project_Description.pdf
|-- evaluation/
|   |-- benchmarks/            # Standardized 20-question evaluation benchmark
|   `-- results/               # Persisted evaluation run artifacts
|-- scripts/
|   |-- setup.sh               # Local environment bootstrap script
|   `-- dev.sh                 # Concurrent dev runner (backend + frontend)
|-- docker-compose.yml         # Full multi-container composition
`-- README.md
```

---

## Getting Started

### Prerequisites

* Python 3.11+
* Node.js 18+ and npm
* Git

### Local Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/muffin-5/repopilot.git
   cd repopilot
   ```

2. **Backend Setup**:
   ```bash
   cd backend
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Configure Environment Variables**:
   Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

   To use Google Gemini (free API key available at [Google AI Studio](https://aistudio.google.com/)):
   ```env
   GEMINI_API_KEY=your_gemini_api_key_here
   LLM_MODEL=gemini-3.5-flash-lite
   ```

   *(Note: RepoPilot also includes an intelligent offline AST heuristic mode so you can run, test, and evaluate the entire pipeline even without an external API key).*

4. **Frontend Setup**:
   ```bash
   cd ../frontend
   npm install
   ```

5. **Run Development Servers**:
   You can start both services with a single command from the root:
   ```bash
   ./scripts/dev.sh
   ```
   * Frontend: [http://localhost:5173](http://localhost:5173)
   * Backend REST API & Docs: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## Running with Docker Compose

To launch the backend, frontend, and Qdrant vector database in containerized mode:

```bash
docker-compose up --build
```

* Frontend UI: [http://localhost:3000](http://localhost:3000)
* Backend API: [http://localhost:8000](http://localhost:8000)
* Qdrant Dashboard: [http://localhost:6333/dashboard](http://localhost:6333/dashboard)

---

## Testing & Quality Assurance

The backend test suite covers AST chunking, BM25 indexing, vector storage, hybrid search ranking, formal metrics calculation, and end-to-end API workflows:

```bash
cd backend
source venv/bin/activate
pytest tests/ -v
```

All 11 unit and integration tests run in under 0.5s:
```
tests/test_api_e2e.py::test_health_and_tools PASSED                      [  9%]
tests/test_api_e2e.py::test_repo_ingest_and_chat_e2e PASSED              [ 18%]
tests/test_code_parser.py::test_fixed_size_chunker PASSED                [ 27%]
tests/test_code_parser.py::test_ast_chunker_extracts_functions_and_classes PASSED [ 36%]
tests/test_metrics.py::test_recall_at_k PASSED                           [ 45%]
tests/test_metrics.py::test_mrr PASSED                                   [ 54%]
tests/test_metrics.py::test_verify_citation_validity PASSED              [ 63%]
tests/test_metrics.py::test_check_abstention_accuracy PASSED             [ 72%]
tests/test_retrieval.py::test_bm25_search_scoring PASSED                 [ 81%]
tests/test_retrieval.py::test_vector_store_in_memory PASSED              [ 90%]
tests/test_retrieval.py::test_hybrid_retriever PASSED                    [100%]
============================== 11 passed in 0.46s ==============================
```

Frontend compilation test:
```bash
cd frontend
npm run build
```

---

## Security & Safety Architecture

When building AI systems that operate over arbitrary repositories, source files must be treated as untrusted input:

* **Zero Arbitrary Execution**: The agent does not expose an unrestricted bash shell. Tools perform strictly read-only AST lookups and file bounds checks.
* **Path Traversal Guards**: All file reading calls validate that resolved paths remain strictly within the cloned repository boundary.
* **Secrets Exclusion**: Git credentials, `.env` files, and local vector checkpoints are strictly ignored in `.gitignore`.
* **Prompt Injection Defenses**: Context snippets are wrapped in delineated fences with strict system instructions prohibiting directive overrides contained inside code comments.

---

## Author

**Pratham Agarwal**  
B.Tech in Computer Science and Engineering  
Indian Institute of Technology (BHU) Varanasi  
GitHub: [@muffin-5](https://github.com/muffin-5)  
Email: [pratham.agarwal.cse22@iitbhu.ac.in](mailto:pratham.agarwal.cse22@iitbhu.ac.in)

---

## License

This project is open-source under the [MIT License](LICENSE).
