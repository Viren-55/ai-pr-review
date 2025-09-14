'use client'

import { useState, useMemo } from 'react'
import { Container, Row, Col, Card, Badge, Button, Nav, Tab, Alert, ProgressBar, Accordion } from 'react-bootstrap'
import { 
  CheckCircleIcon, 
  ExclamationTriangleIcon, 
  XCircleIcon,
  InformationCircleIcon,
  ChevronDownIcon,
  ChevronUpIcon,
  ClipboardDocumentIcon,
  CodeBracketIcon,
  SparklesIcon,
  DocumentArrowDownIcon
} from '@heroicons/react/24/outline'

interface ParsedReviewData {
  overallAssessment: string
  issuesFound: Array<{
    title: string
    description: string
    severity: 'critical' | 'high' | 'medium' | 'low'
    category: string
    suggestion?: string
    codeExample?: string
  }>
  bestPractices: string[]
  securityConcerns: string[]
  performanceIssues: string[]
  recommendations: string[]
  overallScore: number
}

interface ReviewData {
  thread_id: string
  findings: Array<{
    type: string
    description: string
    location: string
    severity: string
    suggestion: string
    confidence: number
    agent: string
  }>
  summary: {
    total_findings: number
    by_severity: Record<string, number>
    by_agent: Record<string, number>
    overall_score: number
    review_timestamp: string
  }
}

interface ModernReviewResultsProps {
  reviewData: ReviewData
  onNewReview: () => void
}

// Parse AI review text into structured data
function parseAIReview(reviewText: string): ParsedReviewData {
  const sections = {
    overallAssessment: '',
    issuesFound: [] as any[],
    bestPractices: [] as string[],
    securityConcerns: [] as string[],
    performanceIssues: [] as string[],
    recommendations: [] as string[],
    overallScore: 8
  }

  // Extract sections using regex patterns
  const overallMatch = reviewText.match(/Overall Assessment\s*(.+?)(?=\n\n|\nIssues Found|\n\d+\.|\nBest Practices)/s)
  if (overallMatch) {
    sections.overallAssessment = overallMatch[1].trim()
  }

  // Extract numbered issues
  const issueMatches = reviewText.match(/(\d+)\.\s*(.+?)(?=\n\d+\.|\nBest Practices|\nSecurity|\nPerformance|\nRecommendations|$)/gs)
  if (issueMatches) {
    sections.issuesFound = issueMatches.map((issue, index) => {
      const cleanIssue = issue.replace(/^\d+\.\s*/, '').trim()
      const severity = 
        cleanIssue.toLowerCase().includes('critical') || cleanIssue.toLowerCase().includes('security') ? 'high' :
        cleanIssue.toLowerCase().includes('performance') || cleanIssue.toLowerCase().includes('error') ? 'medium' :
        'low'
      
      return {
        title: `Issue ${index + 1}`,
        description: cleanIssue,
        severity,
        category: cleanIssue.toLowerCase().includes('security') ? 'Security' : 
                 cleanIssue.toLowerCase().includes('performance') ? 'Performance' : 
                 'Code Quality',
        suggestion: `Fix issue ${index + 1}`
      }
    })
  }

  // Extract best practices
  const practicesMatch = reviewText.match(/Best Practices\s*(.+?)(?=\nSecurity|\nPerformance|\nRecommendations|$)/s)
  if (practicesMatch) {
    const practices = practicesMatch[1].split(/\n\s*[•\-\*]/).filter(p => p.trim())
    sections.bestPractices = practices.map(p => p.trim())
  }

  // Extract security concerns
  const securityMatch = reviewText.match(/Security Concerns?\s*(.+?)(?=\nPerformance|\nRecommendations|$)/s)
  if (securityMatch) {
    const concerns = securityMatch[1].split(/\n\s*[•\-\*]/).filter(c => c.trim())
    sections.securityConcerns = concerns.map(c => c.trim())
  }

  // Extract performance issues
  const performanceMatch = reviewText.match(/Performance\s*(.+?)(?=\nRecommendations|$)/s)
  if (performanceMatch) {
    const performance = performanceMatch[1].split(/\n\s*[•\-\*]/).filter(p => p.trim())
    sections.performanceIssues = performance.map(p => p.trim())
  }

  // Extract recommendations
  const recommendationsMatch = reviewText.match(/Recommendations\s*(.+?)$/s)
  if (recommendationsMatch) {
    const recs = recommendationsMatch[1].split(/\n\s*[•\-\*\d+\.]/).filter(r => r.trim())
    sections.recommendations = recs.map(r => r.trim())
  }

  return sections
}

export function ModernReviewResults({ reviewData, onNewReview }: ModernReviewResultsProps) {
  const [activeTab, setActiveTab] = useState('overview')
  const [expandedIssue, setExpandedIssue] = useState<number | null>(null)

  // Parse the AI review text
  const parsedReview = useMemo(() => {
    const rawReview = reviewData.findings[0]?.description || ''
    return parseAIReview(rawReview)
  }, [reviewData])

  const getSeverityVariant = (severity: string) => {
    switch (severity) {
      case 'critical': return 'danger'
      case 'high': return 'warning'
      case 'medium': return 'info'
      case 'low': return 'success'
      default: return 'secondary'
    }
  }

  const getSeverityIcon = (severity: string) => {
    const size = 20
    switch (severity) {
      case 'critical': return <XCircleIcon style={{ width: size, height: size }} />
      case 'high': return <ExclamationTriangleIcon style={{ width: size, height: size }} />
      case 'medium': return <ExclamationTriangleIcon style={{ width: size, height: size }} />
      case 'low': return <InformationCircleIcon style={{ width: size, height: size }} />
      default: return <InformationCircleIcon style={{ width: size, height: size }} />
    }
  }

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text)
  }

  const exportReport = () => {
    const report = `# AI Code Review Report

## Overall Assessment
${parsedReview.overallAssessment}

## Issues Found (${parsedReview.issuesFound.length})
${parsedReview.issuesFound.map((issue, i) => `${i + 1}. **${issue.title}** (${issue.severity})
   ${issue.description}
   ${issue.suggestion ? `*Suggestion: ${issue.suggestion}*` : ''}
`).join('\n')}

## Best Practices
${parsedReview.bestPractices.map(practice => `- ${practice}`).join('\n')}

## Security Concerns
${parsedReview.securityConcerns.map(concern => `- ${concern}`).join('\n')}

## Performance Issues
${parsedReview.performanceIssues.map(issue => `- ${issue}`).join('\n')}

## Recommendations
${parsedReview.recommendations.map(rec => `- ${rec}`).join('\n')}

---
Generated on ${new Date().toLocaleDateString()} by AI Code Review
`
    
    const blob = new Blob([report], { type: 'text/markdown' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `code-review-${Date.now()}.md`
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <Container className="py-4">
      {/* Header Card */}
      <Card className="shadow-sm mb-4">
        <Card.Body className="p-4">
          <Row className="align-items-center">
            <Col md={8}>
              <div className="d-flex align-items-center mb-3">
                <div className="bg-primary bg-gradient rounded-circle p-3 me-3">
                  <SparklesIcon style={{ width: 32, height: 32, color: 'white' }} />
                </div>
                <div>
                  <h2 className="mb-1">AI Code Review Complete</h2>
                  <p className="text-muted mb-0">
                    Analysis completed • {parsedReview.issuesFound.length} issues found
                  </p>
                </div>
              </div>
            </Col>
            <Col md={4} className="text-md-end">
              <div className="display-4 fw-bold text-primary">{parsedReview.overallScore}/10</div>
              <small className="text-muted">Overall Score</small>
            </Col>
          </Row>

          {/* Quick Stats */}
          <Row className="mt-4">
            <Col xs={6} md={3} className="mb-3">
              <Card className="bg-danger bg-opacity-10 border-danger">
                <Card.Body className="text-center py-3">
                  <h3 className="text-danger mb-0">
                    {parsedReview.issuesFound.filter(i => i.severity === 'critical').length}
                  </h3>
                  <small className="text-danger">Critical</small>
                </Card.Body>
              </Card>
            </Col>
            <Col xs={6} md={3} className="mb-3">
              <Card className="bg-warning bg-opacity-10 border-warning">
                <Card.Body className="text-center py-3">
                  <h3 className="text-warning mb-0">
                    {parsedReview.issuesFound.filter(i => i.severity === 'high').length}
                  </h3>
                  <small className="text-warning">High</small>
                </Card.Body>
              </Card>
            </Col>
            <Col xs={6} md={3} className="mb-3">
              <Card className="bg-info bg-opacity-10 border-info">
                <Card.Body className="text-center py-3">
                  <h3 className="text-info mb-0">
                    {parsedReview.issuesFound.filter(i => i.severity === 'medium').length}
                  </h3>
                  <small className="text-info">Medium</small>
                </Card.Body>
              </Card>
            </Col>
            <Col xs={6} md={3} className="mb-3">
              <Card className="bg-success bg-opacity-10 border-success">
                <Card.Body className="text-center py-3">
                  <h3 className="text-success mb-0">
                    {parsedReview.issuesFound.filter(i => i.severity === 'low').length}
                  </h3>
                  <small className="text-success">Low</small>
                </Card.Body>
              </Card>
            </Col>
          </Row>
        </Card.Body>

        {/* Action Bar */}
        <Card.Footer className="bg-light">
          <div className="d-flex justify-content-between align-items-center">
            <Nav variant="pills">
              <Nav.Item>
                <Nav.Link 
                  active={activeTab === 'overview'} 
                  onClick={() => setActiveTab('overview')}
                >
                  Overview
                </Nav.Link>
              </Nav.Item>
              <Nav.Item>
                <Nav.Link 
                  active={activeTab === 'issues'} 
                  onClick={() => setActiveTab('issues')}
                >
                  Issues ({parsedReview.issuesFound.length})
                </Nav.Link>
              </Nav.Item>
              <Nav.Item>
                <Nav.Link 
                  active={activeTab === 'suggestions'} 
                  onClick={() => setActiveTab('suggestions')}
                >
                  Suggestions
                </Nav.Link>
              </Nav.Item>
            </Nav>

            <div className="d-flex gap-2">
              <Button variant="outline-secondary" onClick={exportReport}>
                <DocumentArrowDownIcon style={{ width: 16, height: 16 }} className="me-2" />
                Export
              </Button>
              <Button variant="primary" onClick={onNewReview}>
                <CodeBracketIcon style={{ width: 16, height: 16 }} className="me-2" />
                New Review
              </Button>
            </div>
          </div>
        </Card.Footer>
      </Card>

      {/* Content Sections */}
      <div className="mt-4">
        {activeTab === 'overview' && (
          <Card className="shadow-sm">
            <Card.Body>
              <h4 className="mb-3">📊 Overall Assessment</h4>
              <p className="text-muted">
                {parsedReview.overallAssessment || 'The code has been analyzed for quality, security, and performance.'}
              </p>
            </Card.Body>
          </Card>
        )}

        {activeTab === 'issues' && (
          <div>
            {parsedReview.issuesFound.length > 0 ? (
              parsedReview.issuesFound.map((issue, index) => (
                <Card key={index} className="shadow-sm mb-3">
                  <Card.Body>
                    <div className="d-flex justify-content-between align-items-start">
                      <div className="flex-grow-1">
                        <div className="d-flex align-items-center mb-2">
                          {getSeverityIcon(issue.severity)}
                          <h5 className="ms-2 mb-0">{issue.title}</h5>
                          <Badge bg={getSeverityVariant(issue.severity)} className="ms-2">
                            {issue.severity}
                          </Badge>
                          <Badge bg="secondary" className="ms-2">
                            {issue.category}
                          </Badge>
                        </div>
                        
                        <p className="text-muted mb-2">{issue.description}</p>
                        
                        {expandedIssue === index && issue.suggestion && (
                          <Alert variant="info" className="mt-3">
                            <h6>💡 Suggested Fix</h6>
                            <p className="mb-2">{issue.suggestion}</p>
                            <Button 
                              size="sm" 
                              variant="outline-info"
                              onClick={() => copyToClipboard(issue.suggestion || '')}
                            >
                              <ClipboardDocumentIcon style={{ width: 16, height: 16 }} className="me-1" />
                              Copy Fix
                            </Button>
                          </Alert>
                        )}
                      </div>
                      
                      <Button
                        variant="link"
                        onClick={() => setExpandedIssue(expandedIssue === index ? null : index)}
                        className="text-secondary"
                      >
                        {expandedIssue === index ? (
                          <ChevronUpIcon style={{ width: 20, height: 20 }} />
                        ) : (
                          <ChevronDownIcon style={{ width: 20, height: 20 }} />
                        )}
                      </Button>
                    </div>
                  </Card.Body>
                </Card>
              ))
            ) : (
              <Card className="shadow-sm">
                <Card.Body className="text-center py-5">
                  <CheckCircleIcon style={{ width: 64, height: 64 }} className="text-success mb-3" />
                  <h4>No issues found!</h4>
                  <p className="text-muted">Your code looks great! No issues were detected.</p>
                </Card.Body>
              </Card>
            )}
          </div>
        )}

        {activeTab === 'suggestions' && (
          <Card className="shadow-sm">
            <Card.Body>
              <h4 className="mb-4">🎯 Recommendations</h4>
              
              {parsedReview.recommendations.length > 0 ? (
                <Accordion>
                  {parsedReview.recommendations.map((recommendation, index) => (
                    <Accordion.Item eventKey={index.toString()} key={index}>
                      <Accordion.Header>
                        <Badge bg="primary" className="me-2">{index + 1}</Badge>
                        {recommendation}
                      </Accordion.Header>
                      <Accordion.Body>
                        <p className="text-muted">{recommendation}</p>
                      </Accordion.Body>
                    </Accordion.Item>
                  ))}
                </Accordion>
              ) : (
                <Alert variant="info">
                  <SparklesIcon style={{ width: 24, height: 24 }} className="me-2" />
                  No specific recommendations available at this time.
                </Alert>
              )}
            </Card.Body>
          </Card>
        )}
      </div>
    </Container>
  )
}