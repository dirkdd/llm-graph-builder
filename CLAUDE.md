# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Common Development Commands

### Local Development
- **Frontend development**: `cd frontend && npm install && npm run dev` (runs on port 8080)
- **Backend development**: `cd backend && ./activate_env.sh && source venv/bin/activate && uvicorn score:app --reload` (runs on port 8000)
- **Docker development**: `docker-compose up` (full stack with database)

### Running Backend and Frontend Separately for Testing/Development

When developing and testing, you often need to run frontend and backend servers independently:

#### **Frontend Server (for UI development and testing)**
```bash
cd frontend
npm install                    # Install dependencies
npm run dev           # Start development server on port 8080
```

#### **Backend Server (for API development and testing)**
```bash
cd backend
source venv/bin/activate                           # Activate existing virtual environment
uvicorn score:app --reload                         # Start backend server on port 8000
```

**Environment Setup Notes**:
- The backend uses the existing `venv/` virtual environment with all packages pre-installed
- No need to create new virtual environment - use `source venv/bin/activate`
- For first-time setup, use `./activate_env.sh` to initialize the environment

**Testing with Both Services**:
1. Start backend: `cd backend && source venv/bin/activate && uvicorn score:app --reload`
2. Start frontend: `cd frontend && npm run dev`  
3. Access application at `http://localhost:5173` (frontend proxies API calls to backend on port 8000)

### Frontend Commands
- **Build**: `cd frontend && npm run build`
- **Lint**: `cd frontend && npm run lint`
- **Format**: `cd frontend && npm run format`
- **Type check**: `cd frontend && npx tsc --noEmit`

### Backend Commands
- **Environment setup**: `cd backend && ./activate_env.sh` (one-time setup)
- **Activate environment**: `cd backend && source venv/bin/activate` (before each session)
- **Run server**: `uvicorn score:app --reload`
- **Run tests**: `pytest tests/ -v`
- **Install new packages**: `pip install package_name && pip freeze > requirements.txt`
- **Python environment**: Virtual environment with all dependencies from `requirements.txt` + `constraints.txt`
- **Main entry point**: `backend/score.py` (FastAPI application)

### IMPORTANT: Python Command Usage for Claude Code
**CRITICAL**: Always use the following patterns to avoid command errors and reduce retry attempts:

1. **Use `python3` instead of `python`**: This system requires `python3` command
2. **Always activate venv first**: Never run Python commands without activating the virtual environment
3. **Proper command patterns**:
   ```bash
   # CORRECT: Always use this pattern
   cd backend && source venv/bin/activate && python3 script.py
   
   # WRONG: These will fail
   python script.py                    # Missing python3
   cd backend && python3 script.py     # Missing venv activation
   ```

4. **Testing commands**:
   ```bash
   # CORRECT
   cd backend && source venv/bin/activate && python3 -m pytest tests/ -v
   
   # CORRECT (shorthand when venv is active)
   pytest tests/ -v
   ```

5. **Running Python scripts**:
   ```bash
   # CORRECT
   cd backend && source venv/bin/activate && python3 -c "import langchain; print('OK')"
   
   # CORRECT for module execution
   cd backend && source venv/bin/activate && python3 -m uvicorn score:app --reload
   ```

**Remember**: Every Python command must be prefixed with `cd backend && source venv/bin/activate &&` unless venv is already activated in the current session.

### Claude Code Timeout Management
**For long-running operations** (tests, package installs, builds), use these strategies:

1. **Bash Tool Timeout Parameter**: Set explicit timeouts for long operations
   ```bash
   # For package installation (up to 10 minutes)
   timeout: 600000  # milliseconds
   
   # For test runs (up to 5 minutes) 
   timeout: 300000  # milliseconds
   ```

2. **Break Down Long Operations**: Split complex tasks into smaller chunks
   ```bash
   # Instead of: pip install -r requirements.txt (might timeout)
   # Do: Install in batches
   pip install fastapi uvicorn pytest
   pip install langchain langchain-openai
   pip install neo4j-rust-ext graphdatascience
   ```

3. **Use Pre-built Environment**: Keep `venv/` directory to avoid reinstalling
   ```bash
   # First time only
   ./activate_env.sh
   
   # Subsequent times (faster)
   source venv/bin/activate
   ```

4. **Test Subset Strategy**: Run specific test files instead of entire suite
   ```bash
   # Instead of: pytest tests/ -v (might timeout)
   # Run specific tests:
   pytest tests/test_specific.py -v
   pytest tests/test_navigation.py::test_function -v
   ```

5. **Environment Variables**: Set timeout preferences
   ```bash
   # In your shell session
   export CLAUDE_TIMEOUT=600000  # 10 minutes
   ```

### Manual Testing Strategy for Server Operations
**IMPORTANT**: Due to local system performance and timeout constraints, Claude Code should request manual testing when server operations are needed.

#### When to Request Manual Testing
- **Server startup verification**: Instead of running `uvicorn score:app --reload` to test if backend starts
- **Frontend development server**: Instead of running `npm run dev` to test if frontend compiles
- **End-to-end functionality testing**: When testing API endpoints, UI interactions, or full workflows
- **Performance testing**: When testing server response times or load handling
- **Integration testing**: When testing frontend-backend communication

#### How to Request Manual Testing
When server testing is needed, Claude Code should:

1. **Request specific testing steps**:
   ```
   Please manually test the following:
   1. Start backend server: `cd backend && source venv/bin/activate && uvicorn score:app --reload`
   2. Verify server starts without errors on port 8000
   3. Test specific endpoint: POST /api/endpoint with sample data
   4. Report any errors or unexpected behavior
   ```

2. **Provide clear testing instructions**:
   ```
   To test the frontend changes:
   1. Start frontend: `cd frontend && npm run dev`
   2. Navigate to http://localhost:5173
   3. Test the new feature by [specific steps]
   4. Verify [expected behavior]
   ```

3. **Request compilation verification only**:
   ```
   Please verify code compiles without starting servers:
   - Backend: `cd backend && source venv/bin/activate && python3 -c "import score; print('Backend imports successfully')"`
   - Frontend: `cd frontend && npx tsc --noEmit` (type checking only)
   ```

#### Benefits of Manual Testing Approach
- **Faster feedback**: No timeouts waiting for slow server startup
- **Better error reporting**: Human can provide detailed error messages and context
- **Real-world testing**: Human can test actual user workflows and edge cases
- **Performance insight**: Human can report on actual performance and responsiveness
- **Debugging capability**: Human can investigate issues that automated tools might miss

#### Testing Collaboration Pattern
1. **Claude Code**: Implements features, writes tests, requests manual verification
2. **Human**: Runs servers, tests functionality, reports results
3. **Claude Code**: Addresses any issues found during manual testing
4. **Human**: Confirms fixes work as expected

This approach maximizes development efficiency while ensuring thorough testing of server-dependent functionality.

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

### Test-Driven Development (TDD) Methodology

**CRITICAL**: Always follow TDD principles when developing new features or fixing bugs in this codebase.

#### 🔴 **RED Phase: Write Failing Tests First**
```bash
# 1. Create test file for new functionality
# Example: tests/test_new_feature.py

# 2. Write failing test that defines expected behavior
cd backend && source venv/bin/activate && python3 -m pytest tests/test_new_feature.py -v
# Expected: Test should FAIL (red phase)
```

#### 🟢 **GREEN Phase: Make Tests Pass**
```bash
# 1. Implement minimal code to make tests pass
# 2. Run tests to verify they pass
cd backend && source venv/bin/activate && python3 -m pytest tests/test_new_feature.py -v
# Expected: Test should PASS (green phase)
```

#### 🔵 **REFACTOR Phase: Improve Code Quality**
```bash
# 1. Refactor implementation while keeping tests green
# 2. Run full test suite to ensure no regressions
cd backend && source venv/bin/activate && python3 -m pytest tests/ -v
# Expected: All tests should continue to PASS
```

#### **TDD Workflow for New Features**

1. **Write Test First** (Red Phase):
   ```python
   # tests/test_new_feature.py
   def test_new_feature_functionality():
       # Arrange: Set up test data
       # Act: Call the function/method
       # Assert: Verify expected behavior
       assert expected_result == actual_result
   ```

2. **Run Test to Confirm Failure**:
   ```bash
   cd backend && source venv/bin/activate && python3 -m pytest tests/test_new_feature.py::test_new_feature_functionality -v
   # Should fail - this confirms test is testing the right thing
   ```

3. **Implement Minimal Code** (Green Phase):
   ```python
   # src/new_feature.py
   def new_feature_functionality():
       # Minimal implementation to make test pass
       return expected_result
   ```

4. **Run Test to Confirm Pass**:
   ```bash
   cd backend && source venv/bin/activate && python3 -m pytest tests/test_new_feature.py::test_new_feature_functionality -v
   # Should pass - green phase achieved
   ```

5. **Refactor and Run All Tests** (Blue Phase):
   ```bash
   cd backend && source venv/bin/activate && python3 -m pytest tests/ -v
   # All tests should pass after refactoring
   ```

#### **TDD for Bug Fixes**

1. **Write Test that Reproduces Bug**:
   ```python
   def test_bug_reproduction():
       # Create test that fails due to the bug
       result = buggy_function(input_that_causes_bug)
       assert result == expected_correct_result  # This should fail
   ```

2. **Confirm Test Fails**:
   ```bash
   cd backend && source venv/bin/activate && python3 -m pytest tests/test_bug_fix.py::test_bug_reproduction -v
   ```

3. **Fix Bug and Verify Test Passes**:
   ```bash
   cd backend && source venv/bin/activate && python3 -m pytest tests/test_bug_fix.py::test_bug_reproduction -v
   ```

#### **TDD Test Categories**

1. **Unit Tests**: Test individual functions/classes
   ```bash
   # Test single function
   pytest tests/test_navigation_extractor.py::TestNavigationExtractor::test_initialization -v
   ```

2. **Integration Tests**: Test component interactions
   ```bash
   # Test multiple components working together
   pytest tests/test_task_11_integration.py -v
   ```

3. **Validation Tests**: Test acceptance criteria
   ```bash
   # Run validation scripts
   python3 validate_task_14.py
   ```

#### **TDD Best Practices for This Codebase**

1. **Follow Existing Test Patterns**:
   - Use `unittest.TestCase` for consistency
   - Mock external dependencies (LLM, database)
   - Create sample data in `setUp()` methods

2. **Test File Naming Convention**:
   ```
   tests/test_[module_name].py
   tests/test_[feature_name].py
   tests/[integration_test_name].py
   ```

3. **Test Method Naming**:
   ```python
   def test_[function_name]_[scenario]_[expected_outcome]():
       # Example: test_extract_entities_with_valid_input_returns_entities()
   ```

4. **Use Appropriate Assertions**:
   ```python
   # Specific assertions for different scenarios
   self.assertEqual(actual, expected)          # Exact match
   self.assertTrue(condition)                  # Boolean check
   self.assertIsNotNone(result)               # Null check
   self.assertRaises(Exception, function)     # Exception testing
   ```

5. **Mock External Dependencies**:
   ```python
   @patch('src.module.external_dependency')
   def test_with_mocked_dependency(self, mock_dependency):
       # Test internal logic without external calls
   ```

#### **TDD Commands Quick Reference**

```bash
# Run single test (fastest feedback)
cd backend && source venv/bin/activate && python3 -m pytest tests/test_file.py::test_method -v

# Run test file
cd backend && source venv/bin/activate && python3 -m pytest tests/test_file.py -v

# Run all tests (before committing)
cd backend && source venv/bin/activate && python3 -m pytest tests/ -v

# Run tests with coverage
cd backend && source venv/bin/activate && python3 -m pytest tests/ --cov=src --cov-report=html

# Run tests for specific feature
cd backend && source venv/bin/activate && python3 -m pytest tests/ -k "navigation" -v
```

#### **TDD Validation Workflow**

1. **Before Starting Development**:
   ```bash
   # Ensure all existing tests pass
   cd backend && source venv/bin/activate && python3 -m pytest tests/ -v
   ```

2. **During Development** (Red-Green-Refactor cycle):
   ```bash
   # Write failing test
   python3 -m pytest tests/test_new.py::test_feature -v  # Should FAIL
   
   # Implement feature
   python3 -m pytest tests/test_new.py::test_feature -v  # Should PASS
   
   # Run full suite after refactoring
   python3 -m pytest tests/ -v  # All should PASS
   ```

3. **Before Committing**:
   ```bash
   # Ensure no regressions
   cd backend && source venv/bin/activate && python3 -m pytest tests/ -v
   
   # Run validation scripts
   python3 validate_task_12.py
   python3 validate_task_13.py
   python3 validate_task_14.py
   ```

### Frontend
- ESLint and Prettier configured for code formatting
- TypeScript for type safety
- Husky pre-commit hooks for linting
- Jest/Vitest for unit testing (follow TDD principles)

### Backend  
- Python virtual environment required
- Type hints throughout codebase
- Logging configured for debugging and monitoring
- Pytest for testing framework (mandatory TDD approach)
- Mock external dependencies for unit tests

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
- **Commit frequently**: Create git commits after completing discrete tasks or milestones
- **Descriptive messages**: Use clear, descriptive commit messages following conventional format
- **Feature branches**: Use feature branches for new development, merge to main when stable
- **Push regularly**: Push commits to maintain backup and enable collaboration
- **Atomic commits**: Keep commits focused on single logical changes for easier debugging and rollback

## UI Implementation Standards

### Frontend UI Library Standards

**CRITICAL**: Follow these UI implementation standards for all frontend development to maintain consistency and avoid integration issues.

#### Required UI Libraries
- **Primary UI Framework**: `@neo4j-ndl/react` - Neo4j Design Language components
- **Secondary UI Framework**: `@mui/material` - Material-UI components for extended functionality
- **Icon Library**: `@mui/icons-material` - Material-UI icons (DO NOT use other icon libraries)
- **Styling**: Material-UI `sx` prop and `styled` components for custom styling

#### UI Component Hierarchy
1. **First Priority**: Use `@neo4j-ndl/react` components when available
   ```typescript
   import { Button, Typography, DataGrid } from '@neo4j-ndl/react';
   ```

2. **Second Priority**: Use `@mui/material` components for extended functionality
   ```typescript
   import { Box, Paper, Alert, LinearProgress } from '@mui/material';
   ```

3. **Icons**: ALWAYS use `@mui/icons-material` for all icons
   ```typescript
   import { 
     PlayArrow as PlayArrowIcon,
     Folder as FolderIcon,
     FolderOpen as FolderOpenIcon,
     Description as DocumentIcon 
   } from '@mui/icons-material';
   ```

#### Icon Usage Standards
- **Import Pattern**: Always import with descriptive alias using `IconName as DescriptiveIcon`
- **Size Consistency**: Use consistent icon sizes (`sx={{ width: 16, height: 16 }}` for small, `sx={{ width: 24, height: 24 }}` for medium)
- **Color Integration**: Use theme colors via `sx` prop for consistent theming
- **Never Use**: Font Awesome, Heroicons, or other icon libraries

#### Theme Integration
- **Theme Provider**: Use `ThemeWrapper` for consistent theming across Neo4j NDL and Material-UI
- **Color Variables**: Use CSS custom properties for theme colors
   ```typescript
   style={{ color: 'var(--theme-palette-text-secondary)' }}
   ```
- **Dark Mode**: Ensure all components support both light and dark themes

#### Layout and Spacing Standards
- **Container Spacing**: Use consistent padding and margins (`p: 2`, `mb: 2`, etc.)
- **Component Gaps**: Use `gap` prop for flex layouts (`gap={2}`)
- **Responsive Design**: Use breakpoints and responsive props where needed
- **Absolute Positioning**: Account for header (100px) and footer (120px) when using absolute positioning

#### Component Architecture
- **File Structure**: Organize components by feature in `src/components/FeatureName/`
- **Props Interface**: Always define TypeScript interfaces for component props
- **Event Handlers**: Use `useCallback` for event handlers to prevent unnecessary re-renders
- **State Management**: Use React Context for shared state, local state for component-specific data

#### Code Quality Standards
- **TypeScript**: All components must be written in TypeScript with proper types
- **Error Handling**: Implement proper error boundaries and error states
- **Accessibility**: Follow WCAG guidelines for accessible UI components
- **Performance**: Use React.memo, useMemo, and useCallback for performance optimization

#### Common Patterns
```typescript
// Standard component structure
import React, { useState, useCallback } from 'react';
import { Button, Typography } from '@neo4j-ndl/react';
import { Box, Paper } from '@mui/material';
import { PlayArrow as PlayArrowIcon } from '@mui/icons-material';

interface ComponentProps {
  title: string;
  onAction: () => void;
  disabled?: boolean;
}

export const Component: React.FC<ComponentProps> = ({
  title,
  onAction,
  disabled = false
}) => {
  const [isProcessing, setIsProcessing] = useState(false);

  const handleAction = useCallback(() => {
    setIsProcessing(true);
    onAction();
  }, [onAction]);

  return (
    <Paper sx={{ p: 2, mb: 2 }}>
      <Typography variant="h6" sx={{ mb: 1 }}>
        {title}
      </Typography>
      <Button
        variant="contained"
        startIcon={<PlayArrowIcon sx={{ width: 16, height: 16 }} />}
        onClick={handleAction}
        disabled={disabled || isProcessing}
      >
        {isProcessing ? 'Processing...' : 'Start Process'}
      </Button>
    </Paper>
  );
};
```

#### Testing Standards
- **Component Testing**: Write unit tests for all new components
- **Integration Testing**: Test component interactions and data flow
- **Visual Testing**: Ensure consistent styling across light/dark themes
- **Accessibility Testing**: Verify keyboard navigation and screen reader compatibility

**Remember**: Consistency is key. Always follow these patterns to maintain a cohesive user experience across the application.