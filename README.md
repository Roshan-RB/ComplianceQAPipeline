# Child Safety Guardian AI

### _Azure Multi-modal Compliance Ingestion Engine using LangGraph_

An intelligent, multi-modal policy compliance agent designed to audit YouTube videos against the **YouTube Child Safety Policy Guidelines**. This project leverages the robust reasoning of Large Language Models (LLMs) combined with Retrieval-Augmented Generation (RAG) and Azure's managed AI infrastructure to automatically analyze video transcripts and on-screen text (OCR) for sensitive material.

---

## Architecture

The system is designed with a clear separation of concerns, orchestrating multiple powerful external services using **LangGraph**:

![Architecture Diagram](docs/architecture.png)
_(Note: Please ensure your architecture diagram is saved as `docs/architecture.png`)_

### 1. Entry Points

- **Streamlit Frontend (`streamlit_app.py`)**: An interactive web UI that provides a live video preview and detailed, expandable compliance reports.
- **FastAPI Backend (`server.py`)**: A production-ready REST API exposing the audit pipeline.
- **CLI Trigger (`main.py`)**: A command-line script for quick testing and debugging.

### 2. Orchestration (LangGraph Workflow)

- **Video Processor**: Downloads YouTube videos using `yt-dlp` and coordinates upload to Azure Video Indexer.
- **Retrieval Engine**: Embeds video transcripts and queries the vector database for relevant child safety rules.
- **Compliance Auditor**: Synthesizes the video transcripts, OCR text, and retrieved rules using an LLM to generate a structured review report and safety recommendation.

### 3. Azure Infra & Managed Services

- **Azure Blob Storage**: Temporary cloud storage for the downloaded video assets.
- **Azure Video Indexer**: Powerful service for transcribing audio and extracting visual OCR text from videos.
- **Azure AI Search**: Vector database enabling fast semantic retrieval of policy knowledge.

### 4. External Intelligence & Observability

- **Azure OpenAI**: Provides the core reasoning (LLM `gpt-4o`) and vector embeddings (`text-embedding-3-small`).
- **Azure Application Insights**: Rich OpenTelemetry tracing showing dependency maps, HTTP calls, and workflow node execution spans.
- **LangSmith**: Deep tracing and debugging specifically for the LangGraph and LangChain execution paths.

---

## Key Features

- **Multi-Modal Analysis**: Correlates audio transcripts with visual text (OCR) for robust compliance checks.
- **Intelligent Refusal Handling**: Gracefully handles Azure OpenAI content filter triggers (e.g., if a video contains sensitive material), reporting them as critical safety signals rather than system crashes.
- **Rich Reporting**: Provides structured findings including a video overview, rule-by-rule policy analysis, and actionable safety recommendations.
- **Transparent RAG**: The UI optionally displays the exact policy excerpts retrieved to ground the LLM's assessment.

---

## Setup & Installation

### 1. Prerequisites

You need active access to the following resources:

- Azure OpenAI (Chat & Embeddings models)
- Azure AI Search
- Azure Video Indexer (tied to an Azure portal account)
- LangSmith (for debugging and tracing)

### 2. Environment Variables

Create a `.env` file in the root directory and populate it with your credentials:

```env
# Azure OpenAI
AZURE_OPENAI_API_KEY="..."
AZURE_OPENAI_ENDPOINT="..."
AZURE_OPENAI_API_VERSION="..."
AZURE_OPENAI_CHAT_DEPLOYMENT="..."

# Azure AI Search
AZURE_SEARCH_ENDPOINT="..."
AZURE_SEARCH_API_KEY="..."
AZURE_SEARCH_INDEX_NAME="child-safety-rules"

# Azure Video Indexer
VI_ACCOUNT_ID="..."
VI_LOCATION="..."
VI_SUBSCRIPTION_KEY="..."

# Observability
LANGCHAIN_API_KEY="..."
LANGCHAIN_TRACING_V2="true"
APPLICATIONINSIGHTS_CONNECTION_STRING="..."
```

### 3. Install Dependencies

This project uses `uv` for lightning-fast dependency management:

```bash
uv pip install -r requirements.txt
```

_(Alternatively, standard `pip install` works as well)_

### 4. Knowledge Base Ingestion

Before running the app, index the child safety policies into Azure AI Search:

```bash
uv run python backend/scripts/index_documents.py
```

_Ensure you have the YouTube Child Safety Policy PDF placed inside `backend/data/`._

---

## Running the Application

### 1. Start the FastAPI Server

The backend exposes the core graph execution logic.

```bash
uv run uvicorn backend.src.api.server:app --reload
```

_The API will be available at `http://localhost:8000`. You can test the endpoints at `http://localhost:8000/docs`._

### 2. Launch the Streamlit Frontend

For the interactive visual experience:

```bash
uv run streamlit run streamlit_app.py
```

### 3. Command Line Execution (Optional)

Run a quick test directly from the terminal without starting servers:

```bash
uv run python main.py
```

---

## Telemetry & Tracing

This engine captures deep telemetry, visible in two primary platforms:

- **Application Map (Azure Monitor)**: Displays a rich layout of HTTP requests bridging your Python App to Azure Search, Video Indexer, and YouTube.
- **LangSmith**: Provides step-by-step traces of prompt templating, token usage, and graph transitions.

---

_Built utilizing LangGraph, Streamlit, and Microsoft Azure AI._
