'use client'

import React, { useState, useEffect } from 'react'
import { Container, Row, Col, Button, Card } from 'react-bootstrap'

interface HomePageProps {
  onStartReview: () => void
}

const agents = [
  {
    id: 'security',
    icon: 'bi-shield-check',
    title: 'Security Analysis',
    description: 'Advanced vulnerability detection and security flaw identification using AI-powered threat analysis',
    iconClass: 'security',
    stats: '99.7% Detection Rate'
  },
  {
    id: 'performance',
    icon: 'bi-lightning-charge',
    title: 'Performance Optimization',
    description: 'Intelligent bottleneck identification and algorithmic efficiency optimization',
    iconClass: 'performance',
    stats: '40% Faster Code'
  },
  {
    id: 'quality',
    icon: 'bi-gear',
    title: 'Code Quality',
    description: 'Comprehensive structure analysis and coding standards adherence verification',
    iconClass: 'quality',
    stats: '95% Quality Score'
  },
  {
    id: 'practices',
    icon: 'bi-stars',
    title: 'Best Practices',
    description: 'Industry-standard pattern recognition and architectural recommendation engine',
    iconClass: 'practices',
    stats: '1M+ Patterns'
  },
  {
    id: 'maintainability',
    icon: 'bi-layers',
    title: 'Maintainability',
    description: 'Long-term sustainability analysis and modular design assessment',
    iconClass: 'maintainability',
    stats: '10x Scalability'
  }
]

export default function HomePage({ onStartReview }: HomePageProps) {
  const [isVisible, setIsVisible] = useState(false)

  useEffect(() => {
    setIsVisible(true)
  }, [])

  return (
    <div>
      {/* Premium Hero Section */}
      <section className="hero-section">
        <Container className="position-relative">
          <Row className="justify-content-center text-center min-vh-100 align-items-center">
            <Col lg={10} xl={8}>
              <div className={`animate-fade-in ${isVisible ? 'visible' : ''}`}>
                {/* Premium Badge */}
                <div className="mb-4">
                  <span className="badge glass-card px-4 py-2 text-uppercase fw-bold tracking-wider">
                    <i className="bi bi-stars me-2"></i>
                    Next-Gen AI Code Analysis
                  </span>
                </div>
                
                {/* Hero Title with Gradient */}
                <h1 className="display-2 fw-bold mb-4 text-gradient">
                  AI-Powered Code Review
                </h1>
                
                {/* Premium Subtitle */}
                <p className="lead mb-5 text-secondary" style={{ 
                  fontSize: '1.4rem', 
                  lineHeight: '1.6',
                  maxWidth: '700px',
                  margin: '0 auto'
                }}>
                  Transform your codebase with <span className="text-gradient fw-semibold">5 specialized AI agents</span> that provide comprehensive analysis on security, performance, and architectural excellence.
                </p>
                
                {/* Premium Stats Bar */}
                <div className="row g-4 mb-5">
                  <div className="col-4">
                    <div className="glass-card p-3 h-100">
                      <div className="h4 mb-1 text-gradient fw-bold">10M+</div>
                      <small className="text-secondary">Lines Analyzed</small>
                    </div>
                  </div>
                  <div className="col-4">
                    <div className="glass-card p-3 h-100">
                      <div className="h4 mb-1 text-gradient fw-bold">99.7%</div>
                      <small className="text-secondary">Accuracy Rate</small>
                    </div>
                  </div>
                  <div className="col-4">
                    <div className="glass-card p-3 h-100">
                      <div className="h4 mb-1 text-gradient fw-bold">50K+</div>
                      <small className="text-secondary">Developers</small>
                    </div>
                  </div>
                </div>
                
                {/* Premium CTA Buttons */}
                <div className="d-flex flex-column flex-sm-row gap-4 justify-content-center">
                  <Button 
                    variant="primary" 
                    size="lg" 
                    onClick={onStartReview}
                    className="px-5 py-3 fw-bold animate-pulse-glow"
                    style={{ fontSize: '1.1rem' }}
                  >
                    <i className="bi bi-rocket-takeoff me-2"></i>
                    Start Analysis
                  </Button>
                  <Button 
                    variant="outline-primary" 
                    size="lg" 
                    className="px-5 py-3 fw-bold"
                    style={{ fontSize: '1.1rem' }}
                  >
                    <i className="bi bi-play-circle me-2"></i>
                    Watch Demo
                  </Button>
                </div>

                {/* Floating Code Preview */}
                <div className="position-absolute" style={{
                  top: '20%',
                  right: '-10%',
                  transform: 'rotate(15deg)',
                  opacity: 0.1,
                  zIndex: -1
                }}>
                  <div className="code-block animate-float">
                    <pre className="mb-0 text-sm">
{`// AI Analysis in progress...
function optimize(code) {
  return ai.analyze({
    security: true,
    performance: true,
    quality: true
  });
}`}
                    </pre>
                  </div>
                </div>
              </div>
            </Col>
          </Row>
        </Container>
      </section>

      {/* Premium AI Agents Section */}
      <section className="py-5">
        <Container>
          <Row className="justify-content-center text-center mb-5">
            <Col lg={10}>
              <div className="mb-4">
                <span className="badge glass-card px-3 py-2 text-uppercase fw-bold">
                  <i className="bi bi-cpu me-2"></i>
                  AI-Powered Analysis
                </span>
              </div>
              <h2 className="display-4 fw-bold mb-4 text-gradient">
                5 Specialized AI Agents
              </h2>
              <p className="lead text-secondary" style={{ fontSize: '1.2rem', maxWidth: '600px', margin: '0 auto' }}>
                Each agent is trained on millions of code patterns to deliver 
                <span className="text-gradient fw-semibold"> enterprise-grade analysis</span> across multiple dimensions.
              </p>
            </Col>
          </Row>

          {/* AI Agents Grid Container */}
          <div className="ai-agents-grid">
            {agents.map((agent, index) => (
              <div key={agent.id} className="ai-agent-card-wrapper animate-slide-up" style={{ 
                animationDelay: `${index * 0.15}s`
              }}>
                <Card className="agent-card glass-card h-100">
                  <Card.Body className="agent-card-body position-relative">
                    {/* Premium Stats Badge - Fixed Positioning */}
                    <div className="agent-stats-badge">
                      <span className="badge bg-primary">
                        {agent.stats}
                      </span>
                    </div>
                    
                    {/* Agent Icon Container */}
                    <div className="agent-icon-container">
                      <div className={`agent-icon ${agent.iconClass}`}>
                        <i className={agent.icon}></i>
                      </div>
                    </div>
                    
                    {/* Agent Content */}
                    <div className="agent-content">
                      <h5 className="agent-title">{agent.title}</h5>
                      <p className="agent-description">
                        {agent.description}
                      </p>
                    </div>
                    
                    {/* Premium Action Button - Auto margin to bottom */}
                    <div className="agent-action">
                      <Button 
                        variant="outline-primary" 
                        size="sm" 
                        className="agent-learn-btn"
                      >
                        Learn More <i className="bi bi-arrow-right ms-1"></i>
                      </Button>
                    </div>
                  </Card.Body>
                </Card>
              </div>
            ))}
          </div>

          {/* Technology Showcase */}
          <Row className="mt-5 pt-5">
            <Col className="text-center">
              <div className="glass-card p-5">
                <h4 className="fw-bold mb-4 text-gradient">Powered by Advanced AI Technology</h4>
                <Row className="g-4">
                  <Col md={3}>
                    <div className="mb-3">
                      <i className="bi bi-lightning-charge display-5 text-warning"></i>
                    </div>
                    <h6 className="fw-bold">Real-time Analysis</h6>
                    <small className="text-secondary">{'< 30 seconds'}</small>
                  </Col>
                  <Col md={3}>
                    <div className="mb-3">
                      <i className="bi bi-shield-check display-5 text-success"></i>
                    </div>
                    <h6 className="fw-bold">Enterprise Security</h6>
                    <small className="text-secondary">SOC 2 Compliant</small>
                  </Col>
                  <Col md={3}>
                    <div className="mb-3">
                      <i className="bi bi-globe display-5 text-info"></i>
                    </div>
                    <h6 className="fw-bold">Multi-Language</h6>
                    <small className="text-secondary">15+ Languages</small>
                  </Col>
                  <Col md={3}>
                    <div className="mb-3">
                      <i className="bi bi-graph-up-arrow display-5 text-primary"></i>
                    </div>
                    <h6 className="fw-bold">Continuous Learning</h6>
                    <small className="text-secondary">Self-Improving</small>
                  </Col>
                </Row>
              </div>
            </Col>
          </Row>
        </Container>
      </section>

      {/* Premium Features Section */}
      <section className="py-5">
        <Container>
          <Row className="align-items-center g-5">
            <Col lg={6} className="mb-4 mb-lg-0">
              <div className="mb-4">
                <span className="badge glass-card px-3 py-2 text-uppercase fw-bold">
                  <i className="bi bi-award me-2"></i>
                  Enterprise Features
                </span>
              </div>
              <h3 className="display-5 fw-bold mb-4 text-gradient">
                Why Developers Choose Us
              </h3>
              
              <div className="d-flex align-items-start mb-4">
                <div className="glass-card rounded-circle p-3 me-4" style={{ minWidth: '60px' }}>
                  <i className="bi bi-lightning-charge text-warning display-6"></i>
                </div>
                <div>
                  <h5 className="fw-bold mb-2 text-primary">Lightning Fast Analysis</h5>
                  <p className="text-secondary mb-0 fs-6">
                    Get comprehensive code reviews in under 30 seconds with our optimized AI infrastructure
                  </p>
                </div>
              </div>
              
              <div className="d-flex align-items-start mb-4">
                <div className="glass-card rounded-circle p-3 me-4" style={{ minWidth: '60px' }}>
                  <i className="bi bi-shield-check text-success display-6"></i>
                </div>
                <div>
                  <h5 className="fw-bold mb-2 text-primary">Enterprise Security</h5>
                  <p className="text-secondary mb-0 fs-6">
                    Military-grade encryption with zero data retention policy and SOC 2 compliance
                  </p>
                </div>
              </div>
              
              <div className="d-flex align-items-start mb-4">
                <div className="glass-card rounded-circle p-3 me-4" style={{ minWidth: '60px' }}>
                  <i className="bi bi-graph-up text-info display-6"></i>
                </div>
                <div>
                  <h5 className="fw-bold mb-2 text-primary">Performance Insights</h5>
                  <p className="text-secondary mb-0 fs-6">
                    Advanced profiling and optimization suggestions that improve code performance by 40%
                  </p>
                </div>
              </div>
            </Col>
            
            <Col lg={6}>
              <div className="glass-card p-4">
                <div className="d-flex align-items-center justify-content-between mb-3">
                  <h6 className="fw-bold mb-0 text-primary">
                    <i className="bi bi-code-slash me-2"></i>
                    AI Analysis Preview
                  </h6>
                  <span className="badge bg-success">LIVE</span>
                </div>
                <div className="code-block">
                  <pre className="mb-0" style={{ fontSize: '0.85rem' }}>
{`# Fibonacci Implementation Analysis
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

# AI Recommendations:
✅ Security: Add input validation for n
⚡ Performance: Use memoization (10000x faster)
🎯 Quality: Consider iterative approach
🔧 Maintainability: Add docstring and type hints
⭐ Best Practice: Handle negative inputs`}
                  </pre>
                </div>
                <div className="mt-3">
                  <div className="d-flex justify-content-between align-items-center">
                    <small className="text-secondary">Analysis completed in 0.3s</small>
                    <div className="d-flex gap-2">
                      <span className="badge bg-danger">2 Critical</span>
                      <span className="badge bg-warning">3 Medium</span>
                      <span className="badge bg-success">Score: 78/100</span>
                    </div>
                  </div>
                </div>
              </div>
            </Col>
          </Row>
        </Container>
      </section>

      {/* Premium CTA Section */}
      <section className="py-5 my-5">
        <Container>
          <Row className="justify-content-center">
            <Col lg={10} className="text-center">
              <div className="glass-card p-5">
                <div className="mb-4">
                  <span className="badge glass-card px-3 py-2 text-uppercase fw-bold">
                    <i className="bi bi-rocket me-2"></i>
                    Get Started Today
                  </span>
                </div>
                
                <h3 className="display-5 fw-bold mb-3 text-gradient">Ready to Transform Your Code?</h3>
                <p className="lead text-secondary mb-4" style={{ maxWidth: '500px', margin: '0 auto' }}>
                  Join thousands of developers who trust our AI-powered platform to enhance their code quality and accelerate development.
                </p>
                
                {/* Premium Stats */}
                <Row className="g-4 mb-4">
                  <Col md={4}>
                    <div className="text-center">
                      <div className="h3 mb-1 text-gradient fw-bold">50,000+</div>
                      <small className="text-secondary">Active Developers</small>
                    </div>
                  </Col>
                  <Col md={4}>
                    <div className="text-center">
                      <div className="h3 mb-1 text-gradient fw-bold">10M+</div>
                      <small className="text-secondary">Lines of Code Analyzed</small>
                    </div>
                  </Col>
                  <Col md={4}>
                    <div className="text-center">
                      <div className="h3 mb-1 text-gradient fw-bold">99.7%</div>
                      <small className="text-secondary">Accuracy Rate</small>
                    </div>
                  </Col>
                </Row>
                
                <div className="d-flex flex-column flex-sm-row gap-3 justify-content-center">
                  <Button 
                    variant="primary" 
                    size="lg" 
                    onClick={onStartReview}
                    className="px-5 py-3 fw-bold"
                  >
                    <i className="bi bi-play-fill me-2"></i>
                    Start Free Analysis
                  </Button>
                  <Button 
                    variant="outline-primary" 
                    size="lg" 
                    className="px-5 py-3 fw-bold"
                  >
                    <i className="bi bi-calendar me-2"></i>
                    Schedule Demo
                  </Button>
                </div>
                
                <p className="small text-secondary mt-3 mb-0">
                  <i className="bi bi-shield-check me-1"></i>
                  No credit card required • Enterprise-grade security • SOC 2 compliant
                </p>
              </div>
            </Col>
          </Row>
        </Container>
      </section>
    </div>
  )
}