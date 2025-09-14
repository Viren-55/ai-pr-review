'use client'

import React, { useState, useMemo } from 'react'
import { Container, Row, Col, Card, Badge, Button, Nav, ProgressBar } from 'react-bootstrap'

interface ReviewResultsPageProps {
  reviewData: any
  onViewDetails: () => void
  onNewReview: () => void
}

interface ParsedIssue {
  id: number
  title: string
  description: string
  severity: 'critical' | 'high' | 'medium' | 'low'
  category: string
  suggestion: string
  codeSnippet?: string
  lineNumber?: number
  filePath?: string
  fixedCode?: string
}

interface FileNode {
  name: string
  path: string
  type: 'file' | 'directory'
  issues: ParsedIssue[]
  children?: FileNode[]
  expanded?: boolean
}

export default function ReviewResultsPage({ reviewData, onViewDetails, onNewReview }: ReviewResultsPageProps) {
  const [activeFilter, setActiveFilter] = useState('all')
  const [selectedIssueId, setSelectedIssueId] = useState<number | null>(null)
  const [selectedFile, setSelectedFile] = useState<string | null>(null)
  const [highlightedLines, setHighlightedLines] = useState<number[]>([])
  const [fixedIssues, setFixedIssues] = useState<Set<number>>(new Set())
  const [viewMode, setViewMode] = useState<'original' | 'fixed' | 'diff'>('original')
  const [leftPaneCollapsed, setLeftPaneCollapsed] = useState(false)
  const [rightPaneCollapsed, setRightPaneCollapsed] = useState(false)

  // Get the submitted code from reviewData
  const sampleCode = reviewData?.original_code || reviewData?.code || `// No code available`

  // Parse the review data into structured issues
  const parsedIssues = useMemo(() => {
    if (!reviewData?.analysis?.issues) {
      return []
    }
    
    const issues: ParsedIssue[] = reviewData.analysis.issues.map((issue: any) => ({
      id: issue.id,
      title: issue.title,
      description: issue.description,
      severity: issue.severity as 'critical' | 'high' | 'medium' | 'low',
      category: issue.category,
      suggestion: issue.fix_explanation || 'No suggestion available',
      lineNumber: issue.line_number,
      filePath: reviewData.filename || 'Submitted Code',
      codeSnippet: issue.code_snippet,
      fixedCode: issue.suggested_fix
    }))
    
    return issues
  }, [reviewData])

  // Create file tree structure
  const fileTree = useMemo(() => {
    const tree: FileNode[] = []
    const files = new Map<string, FileNode>()
    
    // Group issues by file
    const issuesByFile = new Map<string, ParsedIssue[]>()
    parsedIssues.forEach(issue => {
      const filePath = issue.filePath || 'Submitted Code'
      if (!issuesByFile.has(filePath)) {
        issuesByFile.set(filePath, [])
      }
      issuesByFile.get(filePath)!.push(issue)
    })
    
    // Create file nodes
    issuesByFile.forEach((issues, filePath) => {
      const node: FileNode = {
        name: filePath.split('/').pop() || filePath,
        path: filePath,
        type: 'file',
        issues,
        expanded: true
      }
      files.set(filePath, node)
      tree.push(node)
    })
    
    return tree
  }, [parsedIssues])

  // Calculate summary statistics
  const summary = useMemo(() => {
    const severityCounts = {
      critical: parsedIssues.filter(i => i.severity === 'critical').length,
      high: parsedIssues.filter(i => i.severity === 'high').length,
      medium: parsedIssues.filter(i => i.severity === 'medium').length,
      low: parsedIssues.filter(i => i.severity === 'low').length,
    }
    
    const totalIssues = Object.values(severityCounts).reduce((a, b) => a + b, 0)
    // Use the score from the backend analysis if available, otherwise calculate
    const overallScore = reviewData?.analysis?.overall_score || 
      Math.max(0, 100 - (severityCounts.critical * 25 + severityCounts.high * 15 + severityCounts.medium * 10 + severityCounts.low * 5))
    
    return {
      totalIssues,
      overallScore,
      severityCounts
    }
  }, [parsedIssues, reviewData])

  const filteredIssues = parsedIssues.filter(issue => 
    activeFilter === 'all' || issue.severity === activeFilter
  )

  const handleIssueClick = (issue: ParsedIssue) => {
    setSelectedIssueId(issue.id)
    setSelectedFile(issue.filePath || null)
    if (issue.lineNumber) {
      setHighlightedLines([issue.lineNumber])
    }
  }

  const handleFileClick = (file: FileNode) => {
    setSelectedFile(file.path)
    // Auto-select first issue in the file
    if (file.issues.length > 0) {
      handleIssueClick(file.issues[0])
    }
  }

  const handleFixIssue = async (issue: ParsedIssue) => {
    try {
      // Call backend API to fix the issue
      const response = await fetch(`http://localhost:8000/api/issues/${issue.id}/fix`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          issue_id: issue.id,
          apply_fix: true 
        })
      })
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      const result = await response.json()
      
      if (result.success) {
        setFixedIssues(prev => new Set(prev.add(issue.id)))
        // Optionally update the code display with the fixed code
        if (result.updated_code) {
          // Update the parent component with the new code
          // For now, just mark as fixed
        }
      } else {
        console.error('Fix failed:', result.message)
        alert('Failed to apply fix: ' + result.message)
      }
    } catch (error) {
      console.error('Error applying fix:', error)
      alert('Error applying fix. Please try again.')
    }
  }

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical': return '#dc3545'
      case 'high': return '#fd7e14'
      case 'medium': return '#0dcaf0'
      case 'low': return '#6c757d'
      default: return '#6c757d'
    }
  }

  const getSeverityBg = (severity: string) => {
    switch (severity) {
      case 'critical': return 'rgba(220, 53, 69, 0.1)'
      case 'high': return 'rgba(255, 193, 7, 0.1)'
      case 'medium': return 'rgba(13, 202, 240, 0.1)'
      case 'low': return 'rgba(108, 117, 125, 0.1)'
      default: return 'rgba(108, 117, 125, 0.1)'
    }
  }

  // Left Pane - File & Issue Navigation
  const renderLeftPane = () => {
    if (leftPaneCollapsed) {
      return (
        <div className="left-pane-collapsed">
          <Button 
            variant="link" 
            onClick={() => setLeftPaneCollapsed(false)}
            className="collapse-toggle vertical-text"
          >
            <i className="bi bi-chevron-right"></i>
            Files
          </Button>
        </div>
      )
    }

    return (
      <div className="left-pane-expanded">
        <div className="pane-header">
          <div className="d-flex align-items-center justify-content-between">
            <h6 className="mb-0 fw-bold">
              <i className="bi bi-folder2-open me-2"></i>
              Files & Issues
            </h6>
            <Button 
              variant="link" 
              size="sm"
              onClick={() => setLeftPaneCollapsed(true)}
              className="text-muted p-0"
            >
              <i className="bi bi-chevron-left"></i>
            </Button>
          </div>
        </div>

        <div className="pane-content">
          {/* Summary Stats */}
          <div className="summary-stats-compact mb-3">
            <div className="stats-row">
              {Object.entries(summary.severityCounts).map(([severity, count]) => (
                <div key={severity} className="stat-item-mini">
                  <span className="stat-count" style={{ color: getSeverityColor(severity) }}>
                    {count}
                  </span>
                  <span className="stat-label">{severity.charAt(0).toUpperCase()}</span>
                </div>
              ))}
            </div>
          </div>

          {/* File Tree */}
          <div className="file-tree">
            {fileTree.map((file) => (
              <div key={file.path} className="file-node">
                <div 
                  className={`file-header ${selectedFile === file.path ? 'selected' : ''}`}
                  onClick={() => handleFileClick(file)}
                >
                  <i className="bi bi-file-earmark-code me-2"></i>
                  <span className="file-name">{file.name}</span>
                  <Badge bg="secondary" className="ms-auto issue-count">
                    {file.issues.length}
                  </Badge>
                </div>

                {/* Issues under each file */}
                {file.expanded && file.issues.map((issue) => (
                  <div 
                    key={issue.id}
                    className={`issue-item ${selectedIssueId === issue.id ? 'selected' : ''} ${fixedIssues.has(issue.id) ? 'fixed' : ''}`}
                    onClick={() => handleIssueClick(issue)}
                  >
                    <div className="issue-indicator">
                      <i 
                        className={fixedIssues.has(issue.id) ? "bi bi-check-circle-fill" : "bi bi-exclamation-triangle-fill"} 
                        style={{ color: fixedIssues.has(issue.id) ? '#28a745' : getSeverityColor(issue.severity) }}
                      ></i>
                    </div>
                    <div className="issue-content">
                      <div className="issue-title">{issue.title}</div>
                      <div className="issue-meta">
                        <Badge 
                          bg="" 
                          className="severity-badge"
                          style={{ 
                            backgroundColor: getSeverityBg(issue.severity),
                            color: getSeverityColor(issue.severity)
                          }}
                        >
                          {issue.severity.toUpperCase()}
                        </Badge>
                        {issue.lineNumber && (
                          <span className="line-info">Line {issue.lineNumber}</span>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ))}
          </div>
        </div>
      </div>
    )
  }

  // Middle Pane - Enhanced Code Viewer
  const renderMiddlePane = () => {
    const lines = sampleCode.split('\n')
    const currentFileIssues = selectedFile 
      ? parsedIssues.filter(issue => issue.filePath === selectedFile)
      : []

    return (
      <div className="middle-pane">
        <div className="code-header">
          <div className="d-flex align-items-center justify-content-between">
            <div className="d-flex align-items-center">
              <i className="bi bi-file-earmark-code me-2 text-primary"></i>
              <span className="fw-semibold">{selectedFile || 'Select a file'}</span>
              {currentFileIssues.length > 0 && (
                <Badge bg="warning" className="ms-2">
                  {currentFileIssues.length} issues
                </Badge>
              )}
            </div>
            <div className="d-flex align-items-center gap-2">
              {/* View Mode Toggle */}
              <div className="btn-group btn-group-sm" role="group">
                <input 
                  type="radio" 
                  className="btn-check" 
                  name="viewMode" 
                  id="original"
                  checked={viewMode === 'original'}
                  onChange={() => setViewMode('original')}
                />
                <label className="btn btn-outline-secondary" htmlFor="original">
                  <i className="bi bi-file-text me-1"></i>Original
                </label>

                <input 
                  type="radio" 
                  className="btn-check" 
                  name="viewMode" 
                  id="fixed"
                  checked={viewMode === 'fixed'}
                  onChange={() => setViewMode('fixed')}
                />
                <label className="btn btn-outline-success" htmlFor="fixed">
                  <i className="bi bi-patch-check me-1"></i>Fixed
                </label>

                <input 
                  type="radio" 
                  className="btn-check" 
                  name="viewMode" 
                  id="diff"
                  checked={viewMode === 'diff'}
                  onChange={() => setViewMode('diff')}
                />
                <label className="btn btn-outline-info" htmlFor="diff">
                  <i className="bi bi-arrow-left-right me-1"></i>Diff
                </label>
              </div>
              
              <div className="file-info">
                <Badge bg="primary" className="small">{reviewData?.language || 'Code'}</Badge>
                <Badge bg="secondary" className="small">{lines.length} lines</Badge>
              </div>
            </div>
          </div>
        </div>

        <div className="code-content">
          {selectedFile ? (
            <>
              {viewMode === 'diff' ? (
                // Diff view for comparing original vs fixed
                <div className="diff-view">
                  <div className="diff-pane diff-before">
                    <div className="diff-header">
                      <i className="bi bi-dash-circle text-danger me-2"></i>
                      Original Code
                    </div>
                    {renderCodeLines(lines, 'original')}
                  </div>
                  <div className="diff-pane diff-after">
                    <div className="diff-header">
                      <i className="bi bi-plus-circle text-success me-2"></i>
                      Fixed Code
                    </div>
                    {renderCodeLines(lines, 'fixed')}
                  </div>
                </div>
              ) : (
                // Single view (original or fixed)
                renderCodeLines(lines, viewMode)
              )}
            </>
          ) : (
            <div className="empty-code-view">
              <div className="text-center py-5">
                <i className="bi bi-file-earmark-code display-1 text-muted mb-3"></i>
                <h5 className="text-muted">Select a file to view code</h5>
                <p className="text-muted">Choose a file from the left panel to see its contents and issues</p>
              </div>
            </div>
          )}
        </div>
      </div>
    )
  }

  // Basic syntax highlighting for Python
  const highlightPythonSyntax = (code: string) => {
    return code
      // Keywords
      .replace(/\b(def|class|if|else|elif|for|while|import|from|return|try|except|finally|with|as|in|and|or|not|is|pass|break|continue|yield|lambda|global|nonlocal)\b/g, 
        '<span class="python-keyword">$1</span>')
      // Strings
      .replace(/(["'])((?:\\.|(?!\1)[^\\])*?)\1/g, '<span class="python-string">$&</span>')
      // Comments
      .replace(/#.*$/gm, '<span class="python-comment">$&</span>')
      // Numbers
      .replace(/\b\d+\.?\d*\b/g, '<span class="python-number">$&</span>')
      // Built-ins
      .replace(/\b(print|len|str|int|float|bool|list|dict|tuple|set|range|enumerate|zip|map|filter|sorted|reversed|sum|min|max|abs|round|type|isinstance|hasattr|getattr|setattr|delattr)\b/g,
        '<span class="python-builtin">$1</span>')
  }

  const renderCodeLines = (lines: string[], mode: 'original' | 'fixed') => {
    const currentFileIssues = selectedFile 
      ? parsedIssues.filter(issue => issue.filePath === selectedFile)
      : []

    return (
      <div className="code-lines">
        {lines.map((line, index) => {
          const lineNumber = index + 1
          const isHighlighted = highlightedLines.includes(lineNumber)
          const lineIssues = currentFileIssues.filter(issue => issue.lineNumber === lineNumber)
          const hasIssue = lineIssues.length > 0
          const selectedLineIssue = lineIssues.find(issue => issue.id === selectedIssueId)
          
          let displayLine = line
          if (mode === 'fixed' && selectedLineIssue && fixedIssues.has(selectedLineIssue.id)) {
            displayLine = selectedLineIssue.fixedCode?.split('\n')[0] || line
          }

          // Apply syntax highlighting
          const highlightedLine = reviewData?.language === 'python' 
            ? highlightPythonSyntax(displayLine)
            : displayLine
          
          return (
            <div 
              key={`${mode}-${lineNumber}`}
              className={`code-line ${isHighlighted ? 'highlighted' : ''} ${selectedLineIssue ? 'selected-issue' : ''} ${hasIssue ? 'has-issue' : ''}`}
              data-line={lineNumber}
              title={hasIssue ? `${lineIssues.length} issue${lineIssues.length > 1 ? 's' : ''} found` : ''}
            >
              <span className="line-number">{lineNumber}</span>
              <span 
                className="line-content"
                dangerouslySetInnerHTML={{ __html: highlightedLine }}
              />
              {hasIssue && (
                <div className="line-issues">
                  {lineIssues.map(issue => (
                    <i 
                      key={issue.id}
                      className={`bi ${fixedIssues.has(issue.id) ? 'bi-check-circle-fill' : 'bi-exclamation-triangle-fill'}`} 
                      style={{ 
                        color: fixedIssues.has(issue.id) ? '#28a745' : getSeverityColor(issue.severity),
                        cursor: 'pointer',
                        fontSize: '0.875rem'
                      }}
                      onClick={() => handleIssueClick(issue)}
                      title={`${issue.severity.toUpperCase()}: ${issue.title}`}
                    ></i>
                  ))}
                </div>
              )}
            </div>
          )
        })}
      </div>
    )
  }

  // Right Pane - AI-Powered Issue Panel
  const renderRightPane = () => {
    if (rightPaneCollapsed) {
      return (
        <div className="right-pane-collapsed">
          <Button 
            variant="link" 
            onClick={() => setRightPaneCollapsed(false)}
            className="collapse-toggle vertical-text"
          >
            <i className="bi bi-chevron-left"></i>
            Issues
          </Button>
        </div>
      )
    }

    const selectedIssue = parsedIssues.find(issue => issue.id === selectedIssueId)
    const currentFileIssues = selectedFile 
      ? parsedIssues.filter(issue => issue.filePath === selectedFile)
      : parsedIssues

    return (
      <div className="right-pane-expanded">
        <div className="pane-header">
          <div className="d-flex align-items-center justify-content-between">
            <h6 className="mb-0 fw-bold">
              <i className="bi bi-robot me-2"></i>
              AI Issue Analysis
            </h6>
            <Button 
              variant="link" 
              size="sm"
              onClick={() => setRightPaneCollapsed(true)}
              className="text-muted p-0"
            >
              <i className="bi bi-chevron-right"></i>
            </Button>
          </div>
        </div>

        <div className="pane-content">
          {/* Current File Issues */}
          {selectedFile && currentFileIssues.length > 0 && (
            <div className="file-issues-section mb-4">
              <div className="section-header mb-3">
                <h6 className="mb-1">
                  <i className="bi bi-file-earmark-code me-2"></i>
                  {selectedFile.split('/').pop()}
                </h6>
                <small className="text-muted">{currentFileIssues.length} issues found</small>
              </div>

              {/* Apply All Fixes Button */}
              {currentFileIssues.some(issue => !fixedIssues.has(issue.id)) && (
                <div className="apply-all-section mb-3">
                  <Button 
                    variant="outline-success" 
                    size="sm" 
                    className="w-100"
                    onClick={() => {
                      currentFileIssues.forEach(issue => {
                        if (!fixedIssues.has(issue.id)) {
                          handleFixIssue(issue)
                        }
                      })
                    }}
                  >
                    <i className="bi bi-magic me-2"></i>
                    Apply All Fixes ({currentFileIssues.filter(issue => !fixedIssues.has(issue.id)).length})
                  </Button>
                </div>
              )}

              {/* Issue List for Current File */}
              <div className="current-file-issues">
                {currentFileIssues.map(issue => (
                  <div 
                    key={issue.id}
                    className={`issue-card ${selectedIssueId === issue.id ? 'selected' : ''} ${fixedIssues.has(issue.id) ? 'fixed' : ''}`}
                    onClick={() => handleIssueClick(issue)}
                  >
                    <div className="issue-card-header">
                      <div className="d-flex align-items-center justify-content-between">
                        <Badge 
                          className="severity-badge"
                          style={{ 
                            backgroundColor: getSeverityBg(issue.severity),
                            color: getSeverityColor(issue.severity)
                          }}
                        >
                          {issue.severity.toUpperCase()}
                        </Badge>
                        {fixedIssues.has(issue.id) ? (
                          <i className="bi bi-check-circle-fill text-success"></i>
                        ) : (
                          <Button
                            variant="outline-success"
                            size="sm"
                            onClick={(e) => {
                              e.stopPropagation()
                              handleFixIssue(issue)
                            }}
                          >
                            <i className="bi bi-wrench"></i>
                          </Button>
                        )}
                      </div>
                    </div>
                    <div className="issue-card-body">
                      <h6 className="issue-title">{issue.title}</h6>
                      <p className="issue-description text-muted small">{issue.description}</p>
                      {issue.lineNumber && (
                        <small className="line-reference">
                          <i className="bi bi-arrow-right me-1"></i>
                          Line {issue.lineNumber}
                        </small>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Selected Issue Details */}
          {selectedIssue && (
            <div className="selected-issue-details">
              <div className="section-header mb-3">
                <h6 className="mb-1">Issue Details</h6>
                <small className="text-muted">AI-generated analysis and fix</small>
              </div>

              <div className="issue-detail-card">
                <div className="issue-header mb-3">
                  <h5 className="fw-bold mb-2">{selectedIssue.title}</h5>
                  <div className="d-flex align-items-center gap-2 mb-2">
                    <Badge 
                      style={{ 
                        backgroundColor: getSeverityBg(selectedIssue.severity),
                        color: getSeverityColor(selectedIssue.severity),
                        border: `1px solid ${getSeverityColor(selectedIssue.severity)}40`
                      }}
                    >
                      {selectedIssue.severity.toUpperCase()}
                    </Badge>
                    <Badge bg="secondary">{selectedIssue.category}</Badge>
                  </div>
                </div>

                <div className="issue-content">
                  <div className="description-section mb-3">
                    <h6>
                      <i className="bi bi-info-circle me-2"></i>
                      Why this is an issue
                    </h6>
                    <p className="text-muted">{selectedIssue.description}</p>
                  </div>

                  {selectedIssue.codeSnippet && (
                    <div className="code-section mb-3">
                      <h6>
                        <i className="bi bi-code-slash me-2"></i>
                        Problematic Code
                      </h6>
                      <pre className="code-snippet"><code>{selectedIssue.codeSnippet}</code></pre>
                    </div>
                  )}

                  {selectedIssue.fixedCode && (
                    <div className="fix-section mb-3">
                      <h6>
                        <i className="bi bi-patch-check me-2"></i>
                        AI-Generated Fix
                      </h6>
                      <pre className="code-fix"><code>{selectedIssue.fixedCode}</code></pre>
                    </div>
                  )}

                  <div className="recommendation-section mb-3">
                    <h6>
                      <i className="bi bi-lightbulb me-2"></i>
                      Recommendation
                    </h6>
                    <p className="text-muted">{selectedIssue.suggestion}</p>
                  </div>

                  <div className="action-section">
                    {fixedIssues.has(selectedIssue.id) ? (
                      <div className="fixed-status">
                        <Badge bg="success" className="px-3 py-2">
                          <i className="bi bi-check-lg me-2"></i>
                          Fix Applied
                        </Badge>
                      </div>
                    ) : (
                      <Button 
                        variant="success" 
                        onClick={() => handleFixIssue(selectedIssue)}
                        className="w-100"
                      >
                        <i className="bi bi-wrench me-2"></i>
                        Apply AI Fix
                      </Button>
                    )}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Empty State */}
          {!selectedFile && !selectedIssue && (
            <div className="empty-issue-state text-center py-5">
              <i className="bi bi-robot display-1 text-muted mb-3"></i>
              <h5 className="text-muted">Select a file or issue</h5>
              <p className="text-muted">Choose from the file tree to see AI-powered issue analysis</p>
            </div>
          )}
        </div>
      </div>
    )
  }


  return (
    <div className="review-results-container">
      {/* Compact Header */}
      <div className="review-header">
        <Container fluid>
          <Row className="align-items-center py-3">
            <Col md={6}>
              <div className="d-flex align-items-center">
                <div className="status-icon me-3">
                  <i className="bi bi-check-circle text-success fs-4"></i>
                </div>
                <div>
                  <h5 className="mb-1 fw-bold">Analysis Complete</h5>
                  <p className="mb-0 text-muted small">{summary.totalIssues} issues found • {reviewData?.analysis?.analysis_time_seconds || '?'}s</p>
                </div>
              </div>
            </Col>
            <Col md={6} className="text-end">
              <div className="d-flex align-items-center justify-content-end gap-3">
                <div className="score-compact">
                  <span className="score-number fw-bold fs-4" style={{ color: getSeverityColor(summary.overallScore > 80 ? 'low' : summary.overallScore > 60 ? 'medium' : 'critical') }}>
                    {summary.overallScore}
                  </span>
                  <span className="text-muted">/100</span>
                </div>
                <div className="action-buttons">
                  <Button variant="outline-primary" size="sm" onClick={onViewDetails} className="me-2">
                    <i className="bi bi-file-text me-1"></i>Report
                  </Button>
                  <Button variant="primary" size="sm" onClick={onNewReview}>
                    <i className="bi bi-plus me-1"></i>New
                  </Button>
                </div>
              </div>
            </Col>
          </Row>
        </Container>
      </div>

      {/* Three-Pane Layout */}
      <div className="three-pane-layout">
        <Container fluid className="h-100">
          <Row className="h-100 g-0">
            {/* Left Pane - File & Issue Navigation */}
            <Col 
              lg={leftPaneCollapsed ? 1 : 3} 
              className="left-pane-container"
              style={{ transition: 'all 0.3s ease' }}
            >
              {renderLeftPane()}
            </Col>
            
            {/* Middle Pane - Enhanced Code Viewer */}
            <Col 
              lg={leftPaneCollapsed && rightPaneCollapsed ? 10 : leftPaneCollapsed ? 7 : rightPaneCollapsed ? 7 : 6} 
              className="middle-pane-container"
              style={{ transition: 'all 0.3s ease' }}
            >
              {renderMiddlePane()}
            </Col>
            
            {/* Right Pane - AI-Powered Issue Panel */}
            <Col 
              lg={rightPaneCollapsed ? 1 : 3} 
              className="right-pane-container"
              style={{ transition: 'all 0.3s ease' }}
            >
              {renderRightPane()}
            </Col>
          </Row>
        </Container>
      </div>
    </div>
  )
}