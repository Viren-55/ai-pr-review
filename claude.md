# GenAI Code Review Project - Quick Reference

## Project Structure & Navigation

### Frontend (`/frontend`)
```
frontend/
├── app/                    # Next.js app directory
│   ├── page.tsx           # Main landing page
│   ├── layout.tsx         # Root layout
│   └── globals.css        # Global styles
├── components/            # React components
│   ├── CodeInput.tsx      # Code input form
│   ├── CodeReviewer.tsx   # Main review component
│   ├── FeatureSection.tsx # Feature showcase
│   ├── Header.tsx         # Navigation header
│   ├── Footer.tsx         # Page footer
│   ├── PRQuestionBox.tsx  # PR question input
│   ├── ReviewResults.tsx  # Review output display
│   ├── AgentCodeEditor.tsx # **NEW** - Pydantic AI interactive editor
│   └── ui/               # Reusable UI components
├── lib/hooks/            # Custom React hooks
└── package.json          # Dependencies & scripts
```

#### New Component: AgentCodeEditor

The `AgentCodeEditor` component provides an interactive code editing experience with AI-powered analysis:

```tsx
import AgentCodeEditor from './components/AgentCodeEditor'

function MyPage() {
  return (
    <AgentCodeEditor 
      initialCode="def hello():\n    print('Hello, World!')"
      language="python"
      onCodeChange={(code) => console.log('Code changed:', code)}
    />
  )
}
```

**Features:**
- Real-time code analysis via WebSocket or HTTP API
- Interactive recommendation preview and application
- Syntax highlighting for multiple languages
- Confidence scoring for AI recommendations
- Undo/redo support for applied fixes
- Progress tracking during analysis

### Backend (`/backend`)
```
backend/
├── api/                   # FastAPI application
│   └── main.py           # Main API server
├── agents/               # AI agents for code review
│   ├── code_analyzer.py  # Code quality agent
│   ├── security_reviewer.py # Security analysis agent
│   ├── performance_optimizer.py # Performance agent
│   ├── best_practices.py # Best practices agent
│   └── qa_agent.py      # Q&A agent
├── config/              # Configuration modules
│   ├── azure_config.py  # Azure OpenAI configuration
│   └── __init__.py
├── langgraph/          # LangGraph workflow orchestration
│   └── workflow.py     # Multi-agent workflow
├── tools/              # Analysis tools
│   ├── ast_analyzer.py # AST analysis tools
│   ├── code_navigator.py # Code navigation
│   ├── dependency_checker.py # Dependency analysis
│   ├── documentation_reader.py # Doc analysis
│   └── github_tools.py # GitHub integration
├── requirements.txt    # Python dependencies
├── start_server.py    # Server startup script
└── test_azure_integration.py # Azure OpenAI test
```

## Development Commands

### Frontend
```bash
cd frontend
npm install        # Install dependencies
npm run dev       # Start dev server (usually port 3000/3001)
npm run build     # Build for production
npm run lint      # Run linter
npm run type-check # TypeScript checking
```

### Backend
```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Test Azure OpenAI integration
python test_azure_integration.py

# Start development server (recommended)
python start_server.py

# Alternative: Direct uvicorn start
cd api && uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Run tests (if available)
python -m pytest
```

## Visual Development & Testing

### Design System

The project follows S-Tier SaaS design standards inspired by Stripe, Airbnb, and Linear. All UI development must adhere to:

- **Design Principles**: `/context/design-principles.md` - Comprehensive checklist for world-class UI
- **Component Library**: NextUI with custom Tailwind configuration

### Quick Visual Check

**IMMEDIATELY after implementing any front-end change:**

1. **Identify what changed** - Review the modified components/pages
2. **Navigate to affected pages** - Use `mcp__playwright__browser_navigate` to visit each changed view
3. **Verify design compliance** - Compare against `/context/design-principles.md`
4. **Validate feature implementation** - Ensure the change fulfills the user's specific request
5. **Check acceptance criteria** - Review any provided context files or requirements
6. **Capture evidence** - Take full page screenshot at desktop viewport (1440px) of each changed view
7. **Check for errors** - Run `mcp__playwright__browser_console_messages` ⚠️

This verification ensures changes meet design standards and user requirements.

### Comprehensive Design Review

For significant UI changes or before merging PRs, use the design review agent:

```bash
# Option 1: Use the slash command
/design-review

# Option 2: Invoke the agent directly
@agent-design-review
```

The design review agent will:

- Test all interactive states and user flows
- Verify responsiveness (desktop/tablet/mobile)
- Check accessibility (WCAG 2.1 AA compliance)
- Validate visual polish and consistency
- Test edge cases and error states
- Provide categorized feedback (Blockers/High/Medium/Nitpicks)

### Playwright MCP Integration

#### Essential Commands for UI Testing

```javascript
// Navigation & Screenshots
mcp__playwright__browser_navigate(url); // Navigate to page
mcp__playwright__browser_take_screenshot(); // Capture visual evidence
mcp__playwright__browser_resize(
  width,
  height
); // Test responsiveness

// Interaction Testing
mcp__playwright__browser_click(element); // Test clicks
mcp__playwright__browser_type(
  element,
  text
); // Test input
mcp__playwright__browser_hover(element); // Test hover states

// Validation
mcp__playwright__browser_console_messages(); // Check for errors
mcp__playwright__browser_snapshot(); // Accessibility check
mcp__playwright__browser_wait_for(
  text / element
); // Ensure loading
```

### Design Compliance Checklist

When implementing UI features, verify:

- [ ] **Visual Hierarchy**: Clear focus flow, appropriate spacing
- [ ] **Consistency**: Uses design tokens, follows patterns
- [ ] **Responsiveness**: Works on mobile (375px), tablet (768px), desktop (1440px)
- [ ] **Accessibility**: Keyboard navigable, proper contrast, semantic HTML
- [ ] **Performance**: Fast load times, smooth animations (150-300ms)
- [ ] **Error Handling**: Clear error states, helpful messages
- [ ] **Polish**: Micro-interactions, loading states, empty states

## When to Use Automated Visual Testing

### Use Quick Visual Check for:

- Every front-end change, no matter how small
- After implementing new components or features
- When modifying existing UI elements
- After fixing visual bugs
- Before committing UI changes

### Use Comprehensive Design Review for:

- Major feature implementations
- Before creating pull requests with UI changes
- When refactoring component architecture
- After significant design system updates
- When accessibility compliance is critical

### Skip Visual Testing for:

- Backend-only changes (API, database)
- Configuration file updates
- Documentation changes
- Test file modifications
- Non-visual utility functions

## Azure OpenAI Configuration

### Environment Variables

The backend uses Azure OpenAI for all AI agents. Required environment variables in `.env`:

```bash
# Azure OpenAI Configuration
REASONING_AZURE_API_VERSION=2024-12-01-preview
REASONING_AZURE_OPENAI_API_KEY=your_api_key_here
REASONING_AZURE_OPENAI_ENDPOINT=https://your-resource.cognitiveservices.azure.com
REASONING_MODEL=o4-mini  # Your Azure deployment name
```

### Health Checks

- **General Health**: `GET /health` - Check server status and agents
- **Azure OpenAI Health**: `GET /health/azure` - Test Azure connection
- **Pydantic AI Health**: `GET /api/v2/health` - Test v2 agent system

### AI Agent Systems

The platform now supports two agent architectures:

#### Legacy AI Agents (v1)
1. **Code Quality Agent** - Analyzes code structure, complexity, naming conventions
2. **Security Agent** - Identifies vulnerabilities, security patterns, risks
3. **Performance Agent** - Detects performance issues, optimization opportunities
4. **Best Practices Agent** - Checks framework conventions, design patterns
5. **Q&A Agent** - Answers questions about code and provides explanations

#### Pydantic AI Agents (v2) - **NEW**
Enhanced agent system with type safety, streaming, and interactive editing:

1. **Code Analyzer Agent** - Advanced code quality analysis with pattern detection
2. **Security Analysis Agent** - Comprehensive vulnerability scanning
3. **Performance Analysis Agent** - Algorithmic efficiency and optimization detection
4. **Code Fix Agent** - Automated fix generation with validation
5. **Code Editor Agent** - Interactive editing with undo/redo support

**Key v2 Features:**
- **Type-Safe Operations** - Full Pydantic validation for all agent interactions
- **Streaming Analysis** - Real-time progress updates via WebSocket
- **Interactive Editing** - Review and apply fixes with preview
- **Session Management** - Persistent editing sessions with history
- **Confidence Scoring** - AI confidence levels for all recommendations

### Testing Azure Integration

```bash
# Quick test of Azure OpenAI connectivity
python test_azure_integration.py

# Start server with built-in validation
python start_server.py
```

### API Endpoints

#### Legacy API (v1)
- **POST /review** - Analyze pasted code
- **POST /review/github-pr** - Analyze GitHub pull request
- **POST /upload** - Analyze uploaded code file
- **POST /ask** - Ask questions about previous review
- **GET /languages** - Get supported programming languages

#### Pydantic AI API (v2) - **NEW**
- **POST /api/v2/analyze** - Enhanced code analysis with recommendations
- **POST /api/v2/recommendations/apply** - Apply selected recommendations
- **POST /api/v2/session/create** - Create interactive editing session
- **GET /api/v2/session/{id}/status** - Get session status and diff
- **POST /api/v2/validate** - Validate code syntax and semantics
- **WebSocket /api/v2/ws/analysis** - Real-time analysis streaming
- **WebSocket /api/v2/ws/session/{id}** - Interactive editing WebSocket

#### WebSocket Events
```javascript
// Analysis WebSocket
{
  "type": "start_analysis",
  "code": "def example():\n    pass",
  "language": "python"
}

// Session WebSocket
{
  "type": "apply_recommendation",
  "recommendation": { /* CodeRecommendation object */ }
}
```

## Additional Context

- Design review agent configuration: `/.claude/agents/design-review-agent.md`
- Design principles checklist: `/context/design-principles.md`
- Custom slash commands: `/context/design-review-slash-command.md`