# GenAI Code Review Platform

A modern, AI-powered code review platform built with **Pydantic AI**, **Next.js**, and **Azure OpenAI**. This platform provides intelligent code analysis, security reviews, performance optimization suggestions, and interactive code editing capabilities.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.8%2B-blue)
![TypeScript](https://img.shields.io/badge/typescript-5.0%2B-blue)
![Next.js](https://img.shields.io/badge/Next.js-15-black)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-green)

## ✨ Features

### 🤖 AI-Powered Code Analysis with Pydantic AI
- **Multi-Agent System**: Leverages specialized Pydantic AI agents for comprehensive code review
- **Real-time Analysis**: WebSocket-based streaming for instant feedback
- **Interactive Editing**: Review and apply AI suggestions with preview capabilities
- **Confidence Scoring**: Each recommendation comes with AI confidence levels
- **Session Management**: Persistent editing sessions with full history tracking

### 🔍 Analysis Capabilities
- **Code Quality**: Structure, complexity, naming conventions, and maintainability
- **Security Review**: Vulnerability detection, OWASP compliance, and security best practices
- **Performance Optimization**: Algorithm efficiency, resource usage, and bottleneck detection
- **Best Practices**: Framework-specific conventions, design patterns, and code standards
- **Documentation**: Comment quality, docstring compliance, and code clarity

### 🎨 Modern UI/UX
- **S-Tier SaaS Design**: Inspired by Stripe, Linear, and Airbnb design systems
- **Responsive Layout**: Optimized for desktop, tablet, and mobile devices
- **Dark/Light Mode**: System-aware theme with manual toggle
- **Interactive Components**: Real-time code editor with syntax highlighting
- **Accessibility**: WCAG 2.1 AA compliant

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Node.js 18+
- Azure OpenAI API access

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/genai_code_review.git
cd genai_code_review
```

2. **Set up the backend**
```bash
cd backend
pip install -r requirements.txt

# Create .env file with your Azure OpenAI credentials
cat > .env << EOF
REASONING_AZURE_API_VERSION=2024-12-01-preview
REASONING_AZURE_OPENAI_API_KEY=your_api_key_here
REASONING_AZURE_OPENAI_ENDPOINT=https://your-resource.cognitiveservices.azure.com
REASONING_MODEL=o4-mini
EOF
```

3. **Set up the frontend**
```bash
cd ../frontend
npm install
```

4. **Start the servers**

Backend:
```bash
cd backend
python start_server.py
# Server runs on http://localhost:8000
```

Frontend:
```bash
cd frontend
npm run dev
# Application runs on http://localhost:3000
```

## 🏗️ Architecture

### Technology Stack

#### Backend
- **FastAPI**: High-performance API framework
- **Pydantic AI**: Type-safe AI agent orchestration
- **Azure OpenAI**: Enterprise-grade LLM infrastructure
- **Python 3.8+**: Core programming language
- **WebSockets**: Real-time bidirectional communication

#### Frontend
- **Next.js 15**: React framework with App Router
- **TypeScript**: Type-safe JavaScript
- **Tailwind CSS**: Utility-first CSS framework
- **NextUI**: Modern component library
- **Monaco Editor**: VS Code's editor for the web

### System Architecture

```
┌─────────────────────────────────────────────────┐
│                   Frontend (Next.js)             │
│  ┌──────────┐  ┌──────────┐  ┌──────────────┐  │
│  │   UI     │  │  Editor  │  │   WebSocket  │  │
│  │Components│  │Component │  │    Client    │  │
│  └──────────┘  └──────────┘  └──────────────┘  │
└─────────────────────────────────────────────────┘
                         │
                    HTTP/WebSocket
                         │
┌─────────────────────────────────────────────────┐
│                  Backend (FastAPI)               │
│  ┌──────────┐  ┌──────────┐  ┌──────────────┐  │
│  │   API    │  │WebSocket │  │   Session    │  │
│  │Endpoints │  │ Handler  │  │   Manager    │  │
│  └──────────┘  └──────────┘  └──────────────┘  │
│                        │                         │
│              ┌─────────────────┐                │
│              │  Pydantic AI    │                │
│              │     Agents      │                │
│              └─────────────────┘                │
│                        │                         │
│              ┌─────────────────┐                │
│              │  Azure OpenAI   │                │
│              └─────────────────┘                │
└─────────────────────────────────────────────────┘
```

## 📚 API Documentation

### REST API Endpoints

#### Code Analysis
```http
POST /api/v2/analyze
Content-Type: application/json

{
  "code": "string",
  "language": "python",
  "analysis_type": "full"
}
```

#### Apply Recommendations
```http
POST /api/v2/recommendations/apply
Content-Type: application/json

{
  "code": "string",
  "recommendations": [/* CodeRecommendation objects */],
  "preview": false
}
```

#### Session Management
```http
POST /api/v2/session/create
GET /api/v2/session/{session_id}/status
POST /api/v2/session/{session_id}/action
```

#### Legacy API (v1)
```http
POST /review - Analyze pasted code
POST /review/github-pr - Analyze GitHub pull request
POST /upload - Analyze uploaded code file
POST /ask - Ask questions about previous review
```

### WebSocket API

Connect to real-time analysis:
```javascript
const ws = new WebSocket('ws://localhost:8000/api/v2/ws/analysis');

ws.send(JSON.stringify({
  type: 'start_analysis',
  code: 'your code here',
  language: 'python'
}));

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  // Handle analysis updates
};
```

## 🧪 Testing

### Backend Testing
```bash
cd backend
# Test Azure OpenAI integration
python test_azure_integration.py

# Run unit tests
python -m pytest tests/

# Test security agent specifically
python test_security_agent.py
```

### Frontend Testing
```bash
cd frontend
npm run test
npm run type-check
npm run lint
```

## 🔧 Configuration

### Environment Variables

Backend (`.env`):
```env
# Azure OpenAI Configuration
REASONING_AZURE_API_VERSION=2024-12-01-preview
REASONING_AZURE_OPENAI_API_KEY=your_key
REASONING_AZURE_OPENAI_ENDPOINT=your_endpoint
REASONING_MODEL=your_deployment_name

# Optional: API Settings
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=false
```

Frontend (`.env.local`):
```env
# API Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000

# Optional: Feature Flags
NEXT_PUBLIC_ENABLE_WEBSOCKET=true
NEXT_PUBLIC_ENABLE_DARK_MODE=true
```

## 📦 Project Structure

```
genai_code_review/
├── frontend/                 # Next.js frontend application
│   ├── app/                 # App router pages
│   ├── components/          # React components
│   │   ├── AgentCodeEditor.tsx  # Interactive AI editor
│   │   ├── CodeReviewer.tsx    # Main review component
│   │   └── ui/             # Reusable UI components
│   ├── lib/                # Utilities and hooks
│   └── public/             # Static assets
│
├── backend/                 # FastAPI backend application
│   ├── api/                # API endpoints
│   │   └── main.py        # Main FastAPI app
│   ├── agents/            # Pydantic AI agents
│   │   ├── code_analyzer.py
│   │   ├── security_reviewer.py
│   │   ├── performance_optimizer.py
│   │   └── best_practices.py
│   ├── config/            # Configuration
│   │   └── azure_config.py
│   ├── tools/             # Analysis tools
│   └── requirements.txt   # Python dependencies
│
├── context/               # Development context
│   └── design-principles.md
├── .claude/              # Claude AI configuration
└── CLAUDE.md            # AI assistant instructions
```

## 💡 Key Features Explained

### Pydantic AI Integration
The platform leverages Pydantic AI for type-safe, structured AI agent orchestration:
- **Type Safety**: All agent inputs/outputs are validated with Pydantic models
- **Streaming Support**: Real-time analysis with progress updates
- **Session Management**: Maintain context across multiple interactions
- **Confidence Scoring**: Each recommendation includes AI confidence levels

### Interactive Code Editor (AgentCodeEditor)
A powerful component for real-time code analysis and editing:
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

### AI Agent Systems

#### Pydantic AI Agents (v2)
1. **Code Analyzer Agent** - Advanced code quality analysis with pattern detection
2. **Security Analysis Agent** - Comprehensive vulnerability scanning
3. **Performance Analysis Agent** - Algorithmic efficiency and optimization detection
4. **Code Fix Agent** - Automated fix generation with validation
5. **Code Editor Agent** - Interactive editing with undo/redo support

### Supported Languages
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

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Pydantic AI](https://github.com/pydantic/pydantic-ai) for type-safe AI orchestration
- [Azure OpenAI](https://azure.microsoft.com/en-us/products/ai-services/openai-service) for enterprise LLM infrastructure
- [Next.js](https://nextjs.org/) for the React framework
- [FastAPI](https://fastapi.tiangolo.com/) for the backend framework
- [NextUI](https://nextui.org/) for the component library

## 📞 Support

For support, please open an issue in the GitHub repository or contact the maintainers.

## 🗺️ Roadmap

- [ ] Enhanced Pydantic AI agent capabilities
- [ ] Support for more programming languages
- [ ] IDE extensions (VS Code, JetBrains)
- [ ] GitHub Actions integration
- [ ] GitLab CI/CD integration
- [ ] Team collaboration features
- [ ] Custom rule configuration
- [ ] Enterprise SSO and audit logs
- [ ] On-premise deployment options

---

Built with ❤️ by the GenAI Code Review Team