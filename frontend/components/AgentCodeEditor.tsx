'use client'

import React, { useState, useRef, useEffect } from 'react'
import { Container, Row, Col, Card, Button, Badge, Alert, Spinner } from 'react-bootstrap'
import { 
  PlayIcon, 
  StopIcon, 
  CheckIcon, 
  XMarkIcon,
  ExclamationTriangleIcon,
  LightBulbIcon,
  CodeBracketIcon
} from '@heroicons/react/24/outline'

interface CodeIssue {
  id: string
  title: string
  description: string
  severity: 'critical' | 'high' | 'medium' | 'low' | 'info'
  category: string
  location?: {
    file_path: string
    line_start: number
    line_end?: number
  }
  code_snippet?: string
  confidence: number
  detected_by: string
}

interface CodeRecommendation {
  issue_id: string
  title: string
  description: string
  original_code: string
  suggested_code: string
  explanation: string
  confidence: number
  auto_fixable: boolean
  requires_review: boolean
  impact: 'safe' | 'moderate' | 'risky'
}

interface AnalysisResult {
  id: string
  issues: CodeIssue[]
  recommendations: CodeRecommendation[]
  overall_score: number
  summary: string
  analyzed_by: string[]
  analysis_time_seconds: number
}

interface AnalysisUpdate {
  type: string
  analysis_id: string
  agent?: string
  issue?: CodeIssue
  recommendation?: CodeRecommendation
  result?: AnalysisResult
  progress?: number
  error?: string
}

interface AgentCodeEditorProps {
  initialCode?: string
  language?: string
  onCodeChange?: (code: string) => void
}

export default function AgentCodeEditor({ 
  initialCode = '', 
  language = 'python',
  onCodeChange 
}: AgentCodeEditorProps) {
  const [code, setCode] = useState(initialCode)
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null)
  const [analysisUpdates, setAnalysisUpdates] = useState<AnalysisUpdate[]>([])
  const [recommendations, setRecommendations] = useState<CodeRecommendation[]>([])
  const [selectedRecommendations, setSelectedRecommendations] = useState<Set<string>>(new Set())
  const [isApplyingFixes, setIsApplyingFixes] = useState(false)
  const [connectionStatus, setConnectionStatus] = useState<'disconnected' | 'connecting' | 'connected'>('disconnected')
  
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const wsRef = useRef<WebSocket | null>(null)

  useEffect(() => {
    connectWebSocket()
    return () => {
      if (wsRef.current) {
        wsRef.current.close()
      }
    }
  }, [])

  const connectWebSocket = () => {
    try {
      setConnectionStatus('connecting')
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
      const wsUrl = `${protocol}//${window.location.host}/api/v2/ws/analysis`
      
      wsRef.current = new WebSocket(wsUrl)
      
      wsRef.current.onopen = () => {
        setConnectionStatus('connected')
        console.log('WebSocket connected')
      }
      
      wsRef.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          handleWebSocketMessage(data)
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error)
        }
      }
      
      wsRef.current.onclose = () => {
        setConnectionStatus('disconnected')
        console.log('WebSocket disconnected')
        
        // Attempt to reconnect after 3 seconds
        setTimeout(() => {
          if (connectionStatus === 'disconnected') {
            connectWebSocket()
          }
        }, 3000)
      }
      
      wsRef.current.onerror = (error) => {
        console.error('WebSocket error:', error)
        setConnectionStatus('disconnected')
      }
      
    } catch (error) {
      console.error('Failed to connect WebSocket:', error)
      setConnectionStatus('disconnected')
    }
  }

  const handleWebSocketMessage = (data: any) => {
    if (data.type === 'analysis_update') {
      const update = data.update as AnalysisUpdate
      setAnalysisUpdates(prev => [...prev, update])
      
      if (update.type === 'issue_found' && update.issue) {
        // Add issue to current result
        setAnalysisResult(prev => {
          if (!prev) return null
          return {
            ...prev,
            issues: [...prev.issues, update.issue!]
          }
        })
      } else if (update.type === 'recommendation_generated' && update.recommendation) {
        setRecommendations(prev => [...prev, update.recommendation!])
      } else if (update.type === 'analysis_complete' && update.result) {
        setAnalysisResult(update.result)
        setRecommendations(update.result.recommendations || [])
        setIsAnalyzing(false)
      }
    } else if (data.type === 'error') {
      console.error('Analysis error:', data.message)
      setIsAnalyzing(false)
    }
  }

  const handleCodeChange = (newCode: string) => {
    setCode(newCode)
    onCodeChange?.(newCode)
  }

  const startAnalysis = async () => {
    if (!wsRef.current || connectionStatus !== 'connected') {
      // Fallback to HTTP API
      try {
        setIsAnalyzing(true)
        setAnalysisResult(null)
        setAnalysisUpdates([])
        setRecommendations([])
        
        const response = await fetch('/api/v2/analyze', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            code,
            language,
            include_recommendations: true
          })
        })
        
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`)
        }
        
        const result = await response.json()
        if (result.status === 'success') {
          setAnalysisResult(result.analysis)
          setRecommendations(result.analysis.recommendations || [])
        }
      } catch (error) {
        console.error('Analysis failed:', error)
      } finally {
        setIsAnalyzing(false)
      }
    } else {
      // Use WebSocket for real-time updates
      setIsAnalyzing(true)
      setAnalysisResult(null)
      setAnalysisUpdates([])
      setRecommendations([])
      
      wsRef.current.send(JSON.stringify({
        type: 'start_analysis',
        code,
        language
      }))
    }
  }

  const stopAnalysis = () => {
    setIsAnalyzing(false)
    // Note: In a real implementation, you'd send a stop message to the backend
  }

  const toggleRecommendation = (issueId: string) => {
    setSelectedRecommendations(prev => {
      const newSet = new Set(prev)
      if (newSet.has(issueId)) {
        newSet.delete(issueId)
      } else {
        newSet.add(issueId)
      }
      return newSet
    })
  }

  const applySelectedRecommendations = async () => {
    if (selectedRecommendations.size === 0) return
    
    setIsApplyingFixes(true)
    
    try {
      const selectedRecs = recommendations.filter(rec => 
        selectedRecommendations.has(rec.issue_id)
      )
      
      const response = await fetch('/api/v2/recommendations/apply', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          code,
          language,
          recommendations: selectedRecs
        })
      })
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      const result = await response.json()
      if (result.status === 'success' && result.result.final_code) {
        handleCodeChange(result.result.final_code)
        setSelectedRecommendations(new Set())
        
        // Optionally re-analyze the fixed code
        setTimeout(() => {
          startAnalysis()
        }, 1000)
      }
    } catch (error) {
      console.error('Failed to apply recommendations:', error)
    } finally {
      setIsApplyingFixes(false)
    }
  }

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical': return 'danger'
      case 'high': return 'warning'
      case 'medium': return 'info'
      case 'low': return 'success'
      default: return 'secondary'
    }
  }

  const getSeverityIcon = (severity: string) => {
    const props = { className: "w-4 h-4" }
    switch (severity) {
      case 'critical': return <XMarkIcon {...props} />
      case 'high': return <ExclamationTriangleIcon {...props} />
      case 'medium': return <ExclamationTriangleIcon {...props} />
      case 'low': return <CheckIcon {...props} />
      default: return <CheckIcon {...props} />
    }
  }

  return (
    <Container fluid className="h-100">
      <Row className="h-100">
        {/* Code Editor Pane */}
        <Col lg={8} className="h-100 d-flex flex-column">
          <Card className="h-100">
            <Card.Header className="d-flex justify-content-between align-items-center">
              <div className="d-flex align-items-center">
                <CodeBracketIcon className="w-5 h-5 me-2" />
                <h5 className="mb-0">Code Editor</h5>
              </div>
              <div className="d-flex align-items-center gap-2">
                {connectionStatus === 'connected' && (
                  <Badge bg="success">Real-time</Badge>
                )}
                {connectionStatus === 'connecting' && (
                  <Badge bg="warning">Connecting...</Badge>
                )}
                {connectionStatus === 'disconnected' && (
                  <Badge bg="secondary">Offline</Badge>
                )}
                
                {!isAnalyzing ? (
                  <Button 
                    variant="primary" 
                    onClick={startAnalysis}
                    disabled={!code.trim()}
                  >
                    <PlayIcon className="w-4 h-4 me-2" />
                    Analyze Code
                  </Button>
                ) : (
                  <Button 
                    variant="danger" 
                    onClick={stopAnalysis}
                  >
                    <StopIcon className="w-4 h-4 me-2" />
                    Stop Analysis
                  </Button>
                )}
              </div>
            </Card.Header>
            
            <Card.Body className="p-0 flex-grow-1">
              <textarea
                ref={textareaRef}
                className="form-control h-100 border-0"
                style={{ 
                  resize: 'none', 
                  fontFamily: 'Monaco, Menlo, "Ubuntu Mono", monospace',
                  fontSize: '14px',
                  lineHeight: '1.5'
                }}
                value={code}
                onChange={(e) => handleCodeChange(e.target.value)}
                placeholder={`Enter your ${language} code here...`}
              />
            </Card.Body>
            
            {analysisResult && (
              <Card.Footer>
                <div className="d-flex justify-content-between align-items-center">
                  <div>
                    <Badge bg={analysisResult.overall_score > 80 ? 'success' : analysisResult.overall_score > 60 ? 'warning' : 'danger'} className="me-2">
                      Score: {analysisResult.overall_score}/100
                    </Badge>
                    <span className="text-muted">
                      {analysisResult.issues.length} issues found in {analysisResult.analysis_time_seconds.toFixed(1)}s
                    </span>
                  </div>
                  {selectedRecommendations.size > 0 && (
                    <Button
                      variant="success"
                      size="sm"
                      onClick={applySelectedRecommendations}
                      disabled={isApplyingFixes}
                    >
                      {isApplyingFixes ? (
                        <>
                          <Spinner size="sm" className="me-2" />
                          Applying Fixes...
                        </>
                      ) : (
                        <>
                          <CheckIcon className="w-4 h-4 me-2" />
                          Apply {selectedRecommendations.size} Fix{selectedRecommendations.size !== 1 ? 'es' : ''}
                        </>
                      )}
                    </Button>
                  )}
                </div>
              </Card.Footer>
            )}
          </Card>
        </Col>

        {/* Analysis Results Pane */}
        <Col lg={4} className="h-100 d-flex flex-column">
          <Card className="h-100">
            <Card.Header>
              <h5 className="mb-0">AI Analysis & Recommendations</h5>
            </Card.Header>
            
            <Card.Body className="overflow-auto">
              {isAnalyzing && (
                <div className="text-center py-4">
                  <Spinner animation="border" className="mb-3" />
                  <p className="text-muted">AI agents are analyzing your code...</p>
                  
                  {analysisUpdates.length > 0 && (
                    <div className="mt-3">
                      {analysisUpdates.slice(-3).map((update, index) => (
                        <div key={index} className="text-sm text-muted">
                          {update.type === 'agent_start' && `Starting ${update.agent}...`}
                          {update.type === 'agent_complete' && `${update.agent} completed`}
                          {update.type === 'issue_found' && `Found: ${update.issue?.title}`}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {analysisResult && !isAnalyzing && (
                <>
                  {/* Summary */}
                  <Alert variant={analysisResult.overall_score > 80 ? 'success' : analysisResult.overall_score > 60 ? 'warning' : 'danger'}>
                    <strong>Analysis Complete</strong>
                    <br />
                    {analysisResult.summary}
                  </Alert>

                  {/* Recommendations */}
                  {recommendations.length > 0 && (
                    <div className="mb-4">
                      <h6 className="mb-3">
                        <LightBulbIcon className="w-4 h-4 me-2" />
                        Recommendations ({recommendations.length})
                      </h6>
                      
                      {recommendations.map((rec) => (
                        <Card key={rec.issue_id} className="mb-3">
                          <Card.Body className="p-3">
                            <div className="d-flex justify-content-between align-items-start mb-2">
                              <div className="form-check">
                                <input
                                  className="form-check-input"
                                  type="checkbox"
                                  id={`rec-${rec.issue_id}`}
                                  checked={selectedRecommendations.has(rec.issue_id)}
                                  onChange={() => toggleRecommendation(rec.issue_id)}
                                />
                                <label className="form-check-label fw-bold" htmlFor={`rec-${rec.issue_id}`}>
                                  {rec.title}
                                </label>
                              </div>
                              <Badge bg={rec.auto_fixable ? 'success' : 'warning'}>
                                {rec.auto_fixable ? 'Auto-fixable' : 'Manual'}
                              </Badge>
                            </div>
                            
                            <p className="text-muted small mb-2">{rec.description}</p>
                            
                            <div className="small">
                              <strong>Fix:</strong>
                              <pre className="bg-light p-2 mt-1 rounded">
                                <code>{rec.suggested_code}</code>
                              </pre>
                            </div>
                            
                            <div className="d-flex justify-content-between align-items-center mt-2">
                              <Badge bg={getSeverityColor(rec.impact)}>
                                {rec.impact} impact
                              </Badge>
                              <small className="text-muted">
                                {(rec.confidence * 100).toFixed(0)}% confidence
                              </small>
                            </div>
                          </Card.Body>
                        </Card>
                      ))}
                    </div>
                  )}

                  {/* Issues */}
                  {analysisResult.issues.length > 0 && (
                    <div>
                      <h6 className="mb-3">Issues Found ({analysisResult.issues.length})</h6>
                      
                      {analysisResult.issues.map((issue) => (
                        <Card key={issue.id} className="mb-2">
                          <Card.Body className="p-3">
                            <div className="d-flex align-items-start mb-2">
                              {getSeverityIcon(issue.severity)}
                              <div className="ms-2 flex-grow-1">
                                <div className="d-flex justify-content-between align-items-center">
                                  <strong className="small">{issue.title}</strong>
                                  <Badge bg={getSeverityColor(issue.severity)}>
                                    {issue.severity}
                                  </Badge>
                                </div>
                                <p className="text-muted small mb-1">{issue.description}</p>
                                <small className="text-muted">
                                  Detected by {issue.detected_by} 
                                  {issue.location && ` at line ${issue.location.line_start}`}
                                </small>
                              </div>
                            </div>
                          </Card.Body>
                        </Card>
                      ))}
                    </div>
                  )}
                </>
              )}

              {!isAnalyzing && !analysisResult && (
                <div className="text-center py-5 text-muted">
                  <CodeBracketIcon className="w-12 h-12 mx-auto mb-3" />
                  <p>Enter code and click "Analyze Code" to get AI-powered recommendations</p>
                </div>
              )}
            </Card.Body>
          </Card>
        </Col>
      </Row>
    </Container>
  )
}