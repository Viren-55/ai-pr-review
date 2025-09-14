'use client'

import React, { useState, useMemo, useEffect } from 'react'
import { Container, Row, Col, Card, Button, Accordion, Tab, Tabs, Badge, ListGroup } from 'react-bootstrap'

interface DetailedFindingsPageProps {
  reviewData: any
  onNewReview: () => void
}

interface ParsedContent {
  overallAssessment: string
  issuesFound: string[]
  bestPractices: string[]
  securityConcerns: string[]
  performance: string[]
  recommendations: string[]
}

export default function DetailedFindingsPage({ reviewData, onNewReview }: DetailedFindingsPageProps) {
  const [activeTab, setActiveTab] = useState('assessment')
  const [isVisible, setIsVisible] = useState(false)

  useEffect(() => {
    setIsVisible(true)
  }, [])

  // Parse the review content into structured sections
  const parsedContent = useMemo(() => {
    const reviewText = reviewData.review || ''
    const content: ParsedContent = {
      overallAssessment: '',
      issuesFound: [],
      bestPractices: [],
      securityConcerns: [],
      performance: [],
      recommendations: []
    }

    // Extract Overall Assessment
    const assessmentMatch = reviewText.match(/Overall Assessment\s*(.*?)(?=\n\n|\nIssues Found|\n\d+\.|\nBest Practices)/s)
    if (assessmentMatch) {
      content.overallAssessment = assessmentMatch[1].trim()
    } else {
      content.overallAssessment = reviewText.substring(0, 200) + '...'
    }

    // Extract Issues Found
    const issuesMatch = reviewText.match(/Issues Found\s*(.*?)(?=\nBest Practices|\nSecurity|\nPerformance|\nRecommendations|$)/s)
    if (issuesMatch) {
      content.issuesFound = issuesMatch[1]
        .split(/\n\d+\./)
        .filter(item => item.trim())
        .map(item => item.replace(/^\d+\.\s*/, '').trim())
    } else {
      // Extract numbered items
      const numberedMatches = reviewText.match(/(\d+)\.\s*(.+?)(?=\n\d+\.|\nBest Practices|\nSecurity|\nPerformance|\nRecommendations|$)/gs)
      if (numberedMatches) {
        content.issuesFound = numberedMatches.map(item => item.replace(/^\d+\.\s*/, '').trim())
      }
    }

    // Extract Best Practices
    const practicesMatch = reviewText.match(/Best Practices\s*(.*?)(?=\nSecurity|\nPerformance|\nRecommendations|$)/s)
    if (practicesMatch) {
      content.bestPractices = practicesMatch[1]
        .split(/\n\s*[•\-\*]/)
        .filter(item => item.trim())
        .map(item => item.trim())
    }

    // Extract Security Concerns
    const securityMatch = reviewText.match(/Security Concerns?\s*(.*?)(?=\nPerformance|\nRecommendations|$)/s)
    if (securityMatch) {
      content.securityConcerns = securityMatch[1]
        .split(/\n\s*[•\-\*]/)
        .filter(item => item.trim())
        .map(item => item.trim())
    }

    // Extract Performance
    const performanceMatch = reviewText.match(/Performance\s*(.*?)(?=\nRecommendations|$)/s)
    if (performanceMatch) {
      content.performance = performanceMatch[1]
        .split(/\n\s*[•\-\*]/)
        .filter(item => item.trim())
        .map(item => item.trim())
    }

    // Extract Recommendations
    const recommendationsMatch = reviewText.match(/Recommendations\s*(.*?)$/s)
    if (recommendationsMatch) {
      content.recommendations = recommendationsMatch[1]
        .split(/\n\s*[•\-\*\d+\.]/)
        .filter(item => item.trim())
        .map(item => item.trim())
    }

    return content
  }, [reviewData])

  const exportReport = () => {
    const report = `# Detailed AI Code Review Report

## Overall Assessment
${parsedContent.overallAssessment}

## Issues Found
${parsedContent.issuesFound.map((issue, i) => `${i + 1}. ${issue}`).join('\n')}

## Best Practices
${parsedContent.bestPractices.map(practice => `• ${practice}`).join('\n')}

## Security Concerns
${parsedContent.securityConcerns.map(concern => `• ${concern}`).join('\n')}

## Performance
${parsedContent.performance.map(perf => `• ${perf}`).join('\n')}

## Recommendations
${parsedContent.recommendations.map((rec, i) => `${i + 1}. ${rec}`).join('\n')}

---
Generated on ${new Date().toLocaleDateString()} by AI Code Review Tool
Powered by Azure OpenAI
`
    
    const blob = new Blob([report], { type: 'text/markdown' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `detailed-code-review-${Date.now()}.md`
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="py-5">
      <Container>
        {/* Premium Header */}
        <div className="text-center mb-5">
          <div className="mb-3">
            <span className="badge glass-card px-4 py-2 text-uppercase fw-bold">
              <i className="bi bi-file-text me-2"></i>
              Detailed Analysis Report
            </span>
          </div>
          <h1 className="display-3 fw-bold text-gradient mb-3">Comprehensive Code Review</h1>
          <p className="lead text-secondary mb-4">
            In-depth analysis powered by AI with actionable insights and recommendations
          </p>
          
          {/* Action Bar */}
          <div className="d-flex flex-column flex-sm-row gap-3 justify-content-center align-items-center">
            <div className="d-flex align-items-center text-secondary">
              <i className="bi bi-calendar3 me-2"></i>
              <span className="fw-semibold">Generated:</span>
              <span className="ms-2">{new Date().toLocaleDateString('en-US', { 
                weekday: 'long', 
                year: 'numeric', 
                month: 'long', 
                day: 'numeric' 
              })}</span>
            </div>
            <div className="d-flex gap-3">
              <Button 
                variant="outline-primary" 
                onClick={exportReport}
                className="d-flex align-items-center"
              >
                <i className="bi bi-download me-2"></i>
                Export Report
              </Button>
              <Button 
                variant="primary" 
                onClick={onNewReview}
                className="d-flex align-items-center animate-pulse-glow"
              >
                <i className="bi bi-arrow-clockwise me-2"></i>
                New Analysis
              </Button>
            </div>
          </div>
        </div>

        {/* Premium Content Tabs */}
        <Card className="glass-card border-0">
          <Card.Body className="p-0">
            <Tabs 
              activeKey={activeTab} 
              onSelect={(k) => setActiveTab(k || 'assessment')}
              className="nav-tabs border-0 px-4 pt-4"
              style={{
                borderBottom: '1px solid rgba(255, 255, 255, 0.1)'
              }}
            >
              <Tab eventKey="assessment" title={
                <span className="d-flex align-items-center">
                  <i className="bi bi-clipboard-data me-2"></i>
                  Overall Assessment
                </span>
              }>
                <div className="p-5">
                  <div className="glass-card p-5 text-center">
                    <div className="mb-4">
                      <div className="glass-card rounded-circle p-4 d-inline-flex mb-3" style={{ width: '100px', height: '100px' }}>
                        <i className="bi bi-graph-up text-primary display-4"></i>
                      </div>
                      <h4 className="fw-bold text-gradient mb-3">Code Quality Summary</h4>
                    </div>
                    <div className="lead text-secondary" style={{ lineHeight: '1.8', maxWidth: '800px', margin: '0 auto' }}>
                      {parsedContent.overallAssessment || 'Your code has been analyzed by our AI agents for quality, security, and performance. The analysis provides comprehensive insights to help improve your codebase.'}
                    </div>
                  </div>
                </div>
              </Tab>

              <Tab eventKey="issues" title={
                <span className="d-flex align-items-center">
                  <i className="bi bi-exclamation-triangle me-2"></i>
                  Issues Found 
                  <Badge bg="danger" className="ms-2">{parsedContent.issuesFound.length}</Badge>
                </span>
              }>
                <div className="p-5">
                  {parsedContent.issuesFound.length > 0 ? (
                    <Accordion defaultActiveKey="0">
                      {parsedContent.issuesFound.map((issue, index) => (
                        <Accordion.Item eventKey={index.toString()} key={index} className="glass-card border-0 mb-3">
                          <Accordion.Header>
                            <div className="d-flex align-items-center">
                              <div className="glass-card rounded-circle p-2 me-3" style={{ minWidth: '40px', height: '40px' }}>
                                <Badge bg="danger" className="rounded-circle p-2">{index + 1}</Badge>
                              </div>
                              <span className="fw-semibold">Issue {index + 1}</span>
                            </div>
                          </Accordion.Header>
                          <Accordion.Body className="glass-card p-4">
                            <div className="d-flex align-items-start">
                              <div className="glass-card rounded-circle p-3 me-4 flex-shrink-0" style={{ width: '60px', height: '60px' }}>
                                <i className="bi bi-exclamation-triangle text-warning display-6"></i>
                              </div>
                              <div className="flex-grow-1">
                                <p className="text-secondary mb-3" style={{ lineHeight: '1.6' }}>{issue}</p>
                                {issue.includes('def ') && (
                                  <div className="mt-4">
                                    <h6 className="fw-bold mb-3 text-primary">Code Reference:</h6>
                                    <div className="code-block">
                                      <code>{issue.substring(issue.indexOf('def '), issue.indexOf('def ') + 100)}...</code>
                                    </div>
                                  </div>
                                )}
                                <div className="d-flex gap-2 mt-4">
                                  <Button variant="primary" size="sm">
                                    <i className="bi bi-check-lg me-1"></i>
                                    Mark Resolved
                                  </Button>
                                  <Button variant="outline-primary" size="sm">
                                    <i className="bi bi-bookmark me-1"></i>
                                    Save for Later
                                  </Button>
                                </div>
                              </div>
                            </div>
                          </Accordion.Body>
                        </Accordion.Item>
                      ))}
                    </Accordion>
                  ) : (
                    <div className="text-center py-5">
                      <div className="glass-card rounded-circle p-4 d-inline-flex mb-4" style={{ width: '120px', height: '120px' }}>
                        <i className="bi bi-check-circle text-success display-1"></i>
                      </div>
                      <h4 className="fw-bold text-success mt-3">No Issues Found!</h4>
                      <p className="text-secondary lead">Your code follows good practices with no major issues detected.</p>
                    </div>
                  )}
                </div>
              </Tab>

              <Tab eventKey="practices" title={
                <span className="d-flex align-items-center">
                  <i className="bi bi-stars me-2"></i>
                  Best Practices 
                  <Badge bg="success" className="ms-2">{parsedContent.bestPractices.length}</Badge>
                </span>
              }>
                <div className="p-5">
                  {parsedContent.bestPractices.length > 0 ? (
                    <Row className="g-4">
                      {parsedContent.bestPractices.map((practice, index) => (
                        <Col lg={6} key={index}>
                          <Card className="glass-card border-0 h-100">
                            <Card.Body className="p-4 d-flex align-items-start">
                              <div className="glass-card rounded-circle p-3 me-3 flex-shrink-0" style={{ width: '60px', height: '60px' }}>
                                <i className="bi bi-check-lg text-success display-6"></i>
                              </div>
                              <div>
                                <h6 className="fw-bold text-primary mb-2">Best Practice {index + 1}</h6>
                                <p className="text-secondary mb-0" style={{ lineHeight: '1.6' }}>{practice}</p>
                              </div>
                            </Card.Body>
                          </Card>
                        </Col>
                      ))}
                    </Row>
                  ) : (
                    <div className="text-center py-5">
                      <div className="glass-card rounded-circle p-4 d-inline-flex mb-4" style={{ width: '100px', height: '100px' }}>
                        <i className="bi bi-stars text-info display-4"></i>
                      </div>
                      <h5 className="fw-bold text-primary mt-3">No specific best practices mentioned</h5>
                      <p className="text-secondary">Review other sections for detailed recommendations.</p>
                    </div>
                  )}
                </div>
              </Tab>

              <Tab eventKey="security" title={
                <span className="d-flex align-items-center">
                  <i className="bi bi-shield-exclamation me-2"></i>
                  Security 
                  <Badge bg="danger" className="ms-2">{parsedContent.securityConcerns.length}</Badge>
                </span>
              }>
                <div className="p-5">
                  {parsedContent.securityConcerns.length > 0 ? (
                    <Row className="g-4">
                      {parsedContent.securityConcerns.map((concern, index) => (
                        <Col lg={6} key={index}>
                          <Card className="glass-card border-0 h-100">
                            <Card.Body className="p-4 d-flex align-items-start">
                              <div className="glass-card rounded-circle p-3 me-3 flex-shrink-0" style={{ width: '60px', height: '60px' }}>
                                <i className="bi bi-shield-exclamation text-danger display-6"></i>
                              </div>
                              <div>
                                <h6 className="fw-bold text-danger mb-2">Security Issue {index + 1}</h6>
                                <p className="text-secondary mb-3" style={{ lineHeight: '1.6' }}>{concern}</p>
                                <div className="d-flex gap-2">
                                  <span className="badge bg-danger bg-opacity-25 text-danger">High Priority</span>
                                </div>
                              </div>
                            </Card.Body>
                          </Card>
                        </Col>
                      ))}
                    </Row>
                  ) : (
                    <div className="text-center py-5">
                      <div className="glass-card rounded-circle p-4 d-inline-flex mb-4" style={{ width: '120px', height: '120px' }}>
                        <i className="bi bi-shield-check text-success display-1"></i>
                      </div>
                      <h4 className="fw-bold text-success mt-3">No Security Issues Found!</h4>
                      <p className="text-secondary lead">Your code appears to follow secure coding practices.</p>
                    </div>
                  )}
                </div>
              </Tab>

              <Tab eventKey="performance" title={
                <span className="d-flex align-items-center">
                  <i className="bi bi-lightning-charge me-2"></i>
                  Performance 
                  <Badge bg="warning" className="ms-2">{parsedContent.performance.length}</Badge>
                </span>
              }>
                <div className="p-5">
                  {parsedContent.performance.length > 0 ? (
                    <Row className="g-4">
                      {parsedContent.performance.map((perf, index) => (
                        <Col lg={6} key={index}>
                          <Card className="glass-card border-0 h-100">
                            <Card.Body className="p-4 d-flex align-items-start">
                              <div className="glass-card rounded-circle p-3 me-3 flex-shrink-0" style={{ width: '60px', height: '60px' }}>
                                <i className="bi bi-lightning-charge text-warning display-6"></i>
                              </div>
                              <div>
                                <h6 className="fw-bold text-warning mb-2">Performance Insight {index + 1}</h6>
                                <p className="text-secondary mb-3" style={{ lineHeight: '1.6' }}>{perf}</p>
                                <div className="d-flex gap-2">
                                  <span className="badge bg-warning bg-opacity-25 text-warning">Optimization</span>
                                </div>
                              </div>
                            </Card.Body>
                          </Card>
                        </Col>
                      ))}
                    </Row>
                  ) : (
                    <div className="text-center py-5">
                      <div className="glass-card rounded-circle p-4 d-inline-flex mb-4" style={{ width: '100px', height: '100px' }}>
                        <i className="bi bi-speedometer2 text-info display-4"></i>
                      </div>
                      <h5 className="fw-bold text-primary mt-3">No Performance Issues</h5>
                      <p className="text-secondary">Your code performance looks good based on the analysis.</p>
                    </div>
                  )}
                </div>
              </Tab>

              <Tab eventKey="recommendations" title={
                <span className="d-flex align-items-center">
                  <i className="bi bi-lightbulb me-2"></i>
                  Recommendations 
                  <Badge bg="info" className="ms-2">{parsedContent.recommendations.length}</Badge>
                </span>
              }>
                <div className="p-5">
                  {parsedContent.recommendations.length > 0 ? (
                    <Row className="g-4">
                      {parsedContent.recommendations.map((recommendation, index) => (
                        <Col lg={6} key={index}>
                          <Card className="glass-card border-0 h-100">
                            <Card.Body className="p-4">
                              <div className="d-flex align-items-start">
                                <div className="glass-card rounded-circle p-3 me-3 flex-shrink-0" style={{ width: '60px', height: '60px' }}>
                                  <i className="bi bi-lightbulb text-info display-6"></i>
                                </div>
                                <div className="flex-grow-1">
                                  <h6 className="fw-bold text-primary mb-2">Recommendation {index + 1}</h6>
                                  <p className="text-secondary mb-3" style={{ lineHeight: '1.6' }}>{recommendation}</p>
                                  <div className="d-flex gap-2">
                                    <Button variant="primary" size="sm">
                                      <i className="bi bi-check-lg me-1"></i>
                                      Implement
                                    </Button>
                                    <Button variant="outline-secondary" size="sm">
                                      <i className="bi bi-bookmark me-1"></i>
                                      Save
                                    </Button>
                                  </div>
                                </div>
                              </div>
                            </Card.Body>
                          </Card>
                        </Col>
                      ))}
                    </Row>
                  ) : (
                    <div className="text-center py-5">
                      <div className="glass-card rounded-circle p-4 d-inline-flex mb-4" style={{ width: '100px', height: '100px' }}>
                        <i className="bi bi-lightbulb text-warning display-4"></i>
                      </div>
                      <h5 className="fw-bold text-primary mt-3">No Specific Recommendations</h5>
                      <p className="text-secondary">Check other sections for detailed improvement suggestions.</p>
                    </div>
                  )}
                </div>
              </Tab>
            </Tabs>
          </Card.Body>
        </Card>

        {/* Premium Call to Action Footer */}
        <Row className="mt-5">
          <Col className="text-center">
            <div className="glass-card p-5">
              <div className="mb-4">
                <div className="glass-card rounded-circle p-4 d-inline-flex mb-3" style={{ width: '100px', height: '100px' }}>
                  <i className="bi bi-arrow-clockwise text-primary display-4"></i>
                </div>
                <h4 className="fw-bold text-gradient mb-3">Ready for Another Analysis?</h4>
                <p className="text-secondary mb-4" style={{ maxWidth: '500px', margin: '0 auto' }}>
                  Continue improving your code quality with our AI-powered analysis tools and expert recommendations.
                </p>
              </div>
              
              <div className="d-flex flex-column flex-sm-row gap-3 justify-content-center">
                <Button variant="primary" size="lg" onClick={onNewReview} className="px-5">
                  <i className="bi bi-rocket-takeoff me-2"></i>
                  Start New Analysis
                </Button>
                <Button variant="outline-primary" size="lg" className="px-5">
                  <i className="bi bi-share me-2"></i>
                  Share Results
                </Button>
              </div>
              
              <div className="mt-4 pt-4" style={{ borderTop: '1px solid rgba(255, 255, 255, 0.1)' }}>
                <p className="small text-secondary mb-0">
                  <i className="bi bi-shield-check me-1"></i>
                  Powered by advanced AI models • Enterprise-grade security • SOC 2 compliant
                </p>
              </div>
            </div>
          </Col>
        </Row>
      </Container>
    </div>
  )
}