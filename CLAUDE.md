# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Common Development Commands

### Local Development
- **Frontend development**: `cd frontend && yarn && yarn run dev` (runs on port 8080)
- **Backend development**: `cd backend && python -m venv envName && source envName/bin/activate && pip install -r requirements.txt && uvicorn score:app --reload` (runs on port 8000)
- **Docker development**: `docker-compose up` (full stack with database)

### Frontend Commands
- **Build**: `cd frontend && yarn build`
- **Lint**: `cd frontend && yarn lint`
- **Format**: `cd frontend && yarn format`
- **Type check**: `cd frontend && tsc`

### Backend Commands
- **Run server**: `cd backend && uvicorn score:app --reload`
- **Python environment**: Use virtual environment and install from `requirements.txt`
- **Main entry point**: `backend/score.py` (FastAPI application)

## Architecture Overview

### Tech Stack
- **Backend**: Python FastAPI with Neo4j database integration
- **Frontend**: React + TypeScript with Vite build system
- **Database**: Neo4j (required for knowledge graph operations)
- **LLM Integration**: Multiple providers (OpenAI, Gemini, Diffbot, Azure, Anthropic, etc.)

### Key Backend Components
- `backend/src/main.py`: Core knowledge graph extraction logic
- `backend/score.py`: FastAPI application entry point with all API endpoints
- `backend/src/graphDB_dataAccess.py`: Database operations and graph management
- `backend/src/llm.py`: LLM model integrations and entity extraction
- `backend/src/document_sources/`: Handlers for different input sources (local, S3, GCS, YouTube, Wikipedia, web)
- `backend/src/QA_integration.py`: Question-answering and chat functionality
- `backend/src/shared/`: Common utilities, constants, and custom exceptions

### Key Frontend Components  
- `frontend/src/App.tsx`: Main application routing with authentication
- `frontend/src/Home.tsx`: Primary application interface
- `frontend/src/components/`: Reusable UI components organized by feature
- `frontend/src/services/`: API calls to backend endpoints
- `frontend/src/context/`: React context providers for state management

### Data Flow
1. Documents uploaded through frontend (local files, cloud storage, or web sources)
2. Backend processes documents using LLMs to extract entities and relationships
3. Knowledge graph stored in Neo4j database with vector embeddings
4. Frontend provides chat interface for querying the knowledge graph
5. Multiple retrieval modes: vector search, graph traversal, hybrid approaches

## Environment Configuration

### Required Environment Variables
- **Backend**: Copy `backend/example.env` to `backend/.env`
  - `NEO4J_URI`, `NEO4J_USERNAME`, `NEO4J_PASSWORD`: Database connection
  - `OPENAI_API_KEY`, `DIFFBOT_API_KEY`: LLM model access
  - Various model configurations for different providers
- **Frontend**: Copy `frontend/example.env` to `frontend/.env`
  - `VITE_BACKEND_API_URL`: Backend API endpoint
  - `VITE_LLM_MODELS_PROD`: Available models for production
  - `VITE_REACT_APP_SOURCES`: Enabled input sources

### Docker Configuration
- Uses `docker-compose.yml` for local development
- Backend runs on port 8000, frontend on port 8080
- Requires external Neo4j database (not included in docker-compose)

## Key Development Patterns

### Backend API Structure
- All endpoints in `score.py` follow FastAPI patterns with Form data
- Async endpoints using `asyncio.to_thread()` for blocking operations
- Consistent error handling with custom `LLMGraphBuilderException`
- API responses use `create_api_response()` helper for standardization

### Frontend State Management
- React Context for global state (user credentials, files, alerts)
- Custom hooks for reusable logic (`useSse`, `useSpeech`, etc.)
- Material-UI and Neo4j NDL components for consistent design

### Database Operations
- `graphDBdataAccess` class centralizes all Neo4j operations
- Vector similarity search for embeddings
- Graph traversal for entity relationships
- Community detection for knowledge clustering

## Testing and Quality

### Frontend
- ESLint and Prettier configured for code formatting
- TypeScript for type safety
- Husky pre-commit hooks for linting

### Backend  
- Python virtual environment required
- Type hints throughout codebase
- Logging configured for debugging and monitoring

## File Processing Pipeline

1. **Upload**: Files chunked and uploaded through `/upload` endpoint
2. **Source Creation**: Document metadata stored via `/url/scan`  
3. **Extraction**: Knowledge graph generation via `/extract` endpoint
4. **Post-processing**: Optional community detection, similarity updates via `/post_processing`
5. **Querying**: Chat interface uses `/chat_bot` endpoint with multiple retrieval modes

## Authentication & Security

- Optional Auth0 integration (can be skipped with `VITE_SKIP_AUTH=true`)
- Input sanitization for file paths and user data
- CORS middleware configured for cross-origin requests
- Security headers applied (XContentTypeOptions, XFrame)

## Cloud Deployment

- Google Cloud Platform deployment supported
- Separate build and deployment commands for frontend/backend
- Environment-specific configuration via build args and environment variables

## Implementation Plan

### Overview
The project includes a comprehensive implementation plan for enhancing the LLM Graph Builder with advanced mortgage document processing capabilities. The plan is organized in the `/implementation-plan` directory.

### Implementation Phases

#### Phase 1: Document Package Foundation
- **Focus**: Document package management and hierarchical processing
- **Backend**: Package architecture, hierarchical chunking, navigation extraction
- **Frontend**: Package management UI, enhanced upload flow, navigation viewer
- **Timeline**: Weeks 1-2 + frontend integration at week 2.5

#### Phase 2: Matrix Intelligence
- **Focus**: Matrix processing and cross-document intelligence
- **Backend**: Multi-type classification, range extraction, matrix-guidelines mapping
- **Frontend**: Matrix visualization, classification displays, relationship viewers
- **Timeline**: Weeks 3-4 + frontend integration at week 4.5

#### Phase 3: Knowledge Graph Enhancement
- **Focus**: Multi-layer Neo4j architecture and hybrid retrieval
- **Backend**: Multi-layer schema, hybrid retrieval, advanced query processing
- **Frontend**: Query composer, multi-modal visualization, navigation assistant
- **Timeline**: Weeks 5-6 + frontend integration at week 6.5

#### Phase 4: Production Features
- **Focus**: Enterprise capabilities and AI enhancement
- **Backend**: AI automation, webhooks, exports, monitoring, audit framework
- **Frontend**: Management consoles, monitoring dashboards, admin panels
- **Timeline**: Weeks 7-8 + frontend integration at week 8.5

### Key Innovations
- **Hierarchical Document Understanding**: Navigation-aware processing maintaining document structure
- **Bidirectional Guidelines-Matrix Integration**: Automatic consistency validation between document types
- **Complete Decision Tree Extraction**: Full traceability from policy to outcome
- **Multi-Modal Retrieval**: Navigation, entity, matrix, and decision-based search

### Implementation Approach
Each phase follows an iterative pattern:
1. Backend implementation of core functionality
2. Frontend integration with existing UI patterns
3. Comprehensive testing and validation
4. User feedback incorporation before next phase

### Technical Specifications
- Detailed specifications in `/implementation-plan/technical-specs/`
- API documentation in `/implementation-plan/api-specs/`
- Phase-specific details in respective phase directories

### Success Metrics
- **Backend**: >95% navigation accuracy, >90% entity completeness, <100ms query performance
- **Frontend**: 100% design consistency, <3 clicks for major tasks, <2s load times
- **Production**: >99.9% uptime, 10,000+ concurrent users, 100% security compliance

## Development Best Practices

### Version Control
- We should make it a rule to create a git commit and push after every successful step completion this way we have an easy way to restore if things get messed up