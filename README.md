# Agentic AI Code Review System

An advanced AI-powered code review system that uses multiple specialized agents to provide comprehensive code analysis. Built with LangGraph, FastAPI, and Next.js.

## Features

### 🤖 Multiple Specialized Agents
- **Code Quality Agent**: Analyzes code structure, readability, and maintainability
- **Security Agent**: Identifies vulnerabilities and security issues (OWASP Top 10)
- **Performance Agent**: Detects bottlenecks and optimization opportunities
- **Best Practices Agent**: Checks against framework conventions and design patterns
- **Q&A Agent**: Answers questions about your code interactively

### 🛠 Powerful Tools
Each agent has access to specialized tools:
- **Code Navigator**: Find functions, classes, and navigate code structure
- **AST Analyzer**: Deep code analysis using Abstract Syntax Trees
- **GitHub Tools**: Direct integration with GitHub PRs and repositories
- **Dependency Checker**: Analyze dependencies and check for vulnerabilities
- **Documentation Reader**: Extract and validate code documentation

### 🔄 Real-time Analysis
- WebSocket connections for live progress updates
- Parallel agent execution for fast results
- Interactive Q&A system for deeper insights

### 📊 Comprehensive Reporting
- Severity-based issue classification
- Confidence scoring for findings
- Actionable recommendations
- Overall code quality score

## Getting Started

### Prerequisites
- Docker and Docker Compose
- OpenAI API key (for LLM agents)
- Optional: Anthropic API key, GitHub token

### Quick Start

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd genai_code_review
   ```

2. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

3. **Start the application**
   ```bash
   docker-compose up -d
   ```

4. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

### Manual Setup

#### Backend Setup
```bash
cd backend
pip install -r requirements.txt
export OPENAI_API_KEY=your_key_here
uvicorn api.main:app --reload
```

#### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

## Usage

### 1. Submit Code for Review
- **Paste Code**: Directly paste code snippets
- **Upload Files**: Upload source code files
- **GitHub PR**: Review pull requests directly from GitHub

### 2. View Results
- **Findings**: Detailed issues with severity levels
- **Recommendations**: Actionable improvement suggestions
- **Metrics**: Code quality scores and statistics

### 3. Interactive Q&A
- Ask questions about your code
- Get intelligent answers from specialized agents
- Understand implementation decisions and edge cases

## API Endpoints

### Core Endpoints
- `POST /review` - Submit code for review
- `POST /review/github-pr` - Review GitHub pull request
- `POST /upload` - Upload and review files
- `POST /ask` - Ask questions about reviewed code
- `GET /review/{thread_id}/status` - Get review status

### WebSocket
- `WS /ws/review/{thread_id}` - Real-time review updates

## Architecture

### Backend Components
- **FastAPI**: REST API server
- **LangGraph**: Agent workflow orchestration
- **LangChain**: LLM integration and tool management
- **Redis**: Caching and session management

### Frontend Components
- **Next.js 14**: React framework with App Router
- **Tailwind CSS**: Styling and responsive design
- **Framer Motion**: Animations and interactions
- **WebSocket**: Real-time updates

### Agent Architecture
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Code Quality   │    │    Security     │    │  Performance    │
│     Agent       │    │     Agent       │    │     Agent       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │   LangGraph     │
                    │   Workflow      │
                    └─────────────────┘
                                 │
         ┌───────────────────────┼───────────────────────┐
         │                       │                       │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Best Practices  │    │      Q&A        │    │     Tools       │
│     Agent       │    │     Agent       │    │   (Shared)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Supported Languages

- Python
- JavaScript/TypeScript
- Java
- C/C++
- C#
- Go
- Rust
- PHP
- Ruby
- And more...

## Configuration

### Environment Variables
- `OPENAI_API_KEY`: Required for LLM agents
- `ANTHROPIC_API_KEY`: Optional, for Claude models
- `GITHUB_TOKEN`: Optional, for private repository access
- `NEXT_PUBLIC_API_URL`: Frontend API endpoint

### Agent Configuration
Agents can be configured in `backend/agents/` with:
- Custom prompts
- Tool selection
- Model parameters
- Retry logic

## Development

### Adding New Agents
1. Create agent class in `backend/agents/`
2. Implement required methods: `analyze()`
3. Add tools in `_create_tools()`
4. Register in workflow: `backend/langgraph/workflow.py`

### Adding New Tools
1. Create tool class in `backend/tools/`
2. Implement tool functions
3. Add to agent tool lists
4. Test with existing agents

### Frontend Components
- Components in `frontend/components/`
- Custom hooks in `frontend/lib/hooks/`
- Utilities in `frontend/lib/`

## Testing

### Backend Tests
```bash
cd backend
pytest tests/
```

### Frontend Tests
```bash
cd frontend
npm test
```

### Integration Tests
```bash
docker-compose -f docker-compose.test.yml up
```

## Deployment

### Production Docker
```bash
docker-compose -f docker-compose.prod.yml up -d
```

### Environment Variables for Production
- Set secure API keys
- Configure CORS origins
- Set production database URLs
- Enable SSL/TLS

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License - see LICENSE file for details

## Support

- Issues: GitHub Issues
- Documentation: [Link to docs]
- Community: [Link to community]

## Roadmap

- [ ] Support for more programming languages
- [ ] Integration with popular IDEs
- [ ] Advanced security scanning
- [ ] Team collaboration features
- [ ] Custom rule configuration
- [ ] Enterprise deployment options