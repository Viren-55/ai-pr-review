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

  // Left Pane - Enhanced File & Issue Navigation
  const renderLeftPane = () => {
    if (leftPaneCollapsed) {
      return (
        <div className="left-pane-collapsed">
          <Button 
            variant="link" 
            onClick={() => setLeftPaneCollapsed(false)}
            className="collapse-toggle"
            style={{ 
              writingMode: 'vertical-lr',
              padding: '2rem 0.5rem',
              height: '100%',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              background: 'transparent',
              border: 'none',
              color: 'var(--text-muted)'
            }}
          >
            <i className="bi bi-chevron-right me-1"></i>
            <span>Files</span>
          </Button>
        </div>
      )
    }

    return (
      <div className="left-pane-expanded">
        <div className="enhanced-pane-header">
          <div className="d-flex align-items-center justify-content-between">
            <h6 className="mb-0 fw-bold text-muted">
              Files
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

        <div className="enhanced-pane-content">
          {/* Enhanced File Tree */}
          <div className="enhanced-file-tree">
            {fileTree.length > 0 ? (
              <div className="file-tree-section">
                <div className="folder-header">
                  <i className="bi bi-folder2-open me-2 text-primary"></i>
                  <span className="folder-name">Files</span>
                  <i className="bi bi-chevron-down ms-auto"></i>
                </div>
                
                {fileTree.map((file) => (
                <div key={file.path} className="enhanced-file-node">
                  <div 
                    className={`enhanced-file-header ${selectedFile === file.path ? 'selected' : ''}`}
                    onClick={() => handleFileClick(file)}
                  >
                    <div className="file-icon-container">
                      <i className="bi bi-file-earmark-code file-icon"></i>
                      {file.issues.length > 0 && (
                        <span className="issue-indicator-badge">{file.issues.length}</span>
                      )}
                    </div>
                    <span className="enhanced-file-name">{file.name}</span>
                  </div>

                </div>
                ))}
              </div>
            ) : (
              <div className="file-tree-section">
                <div className="folder-header">
                  <i className="bi bi-folder2-open me-2 text-primary"></i>
                  <span className="folder-name">Files</span>
                  <i className="bi bi-chevron-down ms-auto"></i>
                </div>
                <div className="enhanced-file-node">
                  <div className="enhanced-file-header selected">
                    <div className="file-icon-container">
                      <i className="bi bi-file-earmark-code file-icon"></i>
                      {parsedIssues.length > 0 && (
                        <span className="issue-indicator-badge">{parsedIssues.length}</span>
                      )}
                    </div>
                    <span className="enhanced-file-name">
                      {reviewData?.filename || 'Submitted Code'}
                    </span>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    )
  }

  // Middle Pane - Enhanced Code Viewer with Tabs
  const renderMiddlePane = () => {
    const lines = sampleCode.split('\n')
    const currentFileIssues = selectedFile 
      ? parsedIssues.filter(issue => issue.filePath === selectedFile)
      : []

    return (
      <div className="enhanced-middle-pane">
        {/* Enhanced Code Header with Tabs */}
        <div className="enhanced-code-header">
          <div className="d-flex align-items-center justify-content-between">
            <div className="file-info-section">
              <div className="d-flex align-items-center">
                <i className="bi bi-folder2-open me-2 text-muted"></i>
                <span className="file-path">src/ </span>
                <span className="file-name">{selectedFile?.split('/').pop() || 'crisp_report_data_extraction.py'}</span>
              </div>
              <div className="file-meta">
                <span className="language-badge">Python</span>
                <span className="line-count">• 2730 lines</span>
              </div>
            </div>
            
            {/* Code View Tabs */}
            <div className="code-tabs">
              <button 
                className={`code-tab ${viewMode === 'original' ? 'active' : ''}`}
                onClick={() => setViewMode('original')}
              >
                Original
              </button>
              <button 
                className={`code-tab ${viewMode === 'fixed' ? 'active' : ''}`}
                onClick={() => setViewMode('fixed')}
              >
                Fixed
              </button>
              <button 
                className={`code-tab ${viewMode === 'diff' ? 'active' : ''}`}
                onClick={() => setViewMode('diff')}
              >
                D
              </button>
            </div>
          </div>
        </div>

        {/* Enhanced Code Content */}
        <div className="enhanced-code-content">
          {viewMode === 'diff' ? (
            // Enhanced Diff view
            <div className="enhanced-diff-view">
              <div className="diff-pane diff-before">
                <div className="diff-header">
                  <i className="bi bi-dash-circle text-danger me-2"></i>
                  Original Code
                </div>
                {renderEnhancedCodeLines(lines, 'original')}
              </div>
              <div className="diff-pane diff-after">
                <div className="diff-header">
                  <i className="bi bi-plus-circle text-success me-2"></i>
                  Fixed Code
                </div>
                {renderEnhancedCodeLines(lines, 'fixed')}
              </div>
            </div>
          ) : (
            // Enhanced Single view - always show code
            renderEnhancedCodeLines(lines, viewMode)
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

  // Enhanced code rendering with better issue indicators
  const renderEnhancedCodeLines = (lines: string[], mode: 'original' | 'fixed') => {
    const currentFileIssues = selectedFile 
      ? parsedIssues.filter(issue => issue.filePath === selectedFile)
      : []

    return (
      <div className="enhanced-code-lines">
        {lines.map((line, index) => {
          const lineNumber = index + 1
          const isHighlighted = highlightedLines.includes(lineNumber)
          const lineIssues = currentFileIssues.filter(issue => issue.lineNumber === lineNumber)
          const hasIssue = lineIssues.length > 0
          const selectedLineIssue = lineIssues.find(issue => issue.id === selectedIssueId)
          
          let displayLine = line
          if (mode === 'fixed' && selectedLineIssue && fixedIssues.has(selectedLineIssue.id)) {
            displayLine = selectedLineIssue.fixedCode?.split('\\n')[0] || line
          }

          // Apply syntax highlighting
          const highlightedLine = reviewData?.language === 'python' 
            ? highlightPythonSyntax(displayLine)
            : displayLine
          
          return (
            <div 
              key={`${mode}-${lineNumber}`}
              className={`enhanced-code-line ${isHighlighted ? 'highlighted' : ''} ${selectedLineIssue ? 'selected-issue' : ''} ${hasIssue ? 'has-issue' : ''}`}
              data-line={lineNumber}
            >
              <span className="enhanced-line-number">{lineNumber}</span>
              <span 
                className="enhanced-line-content"
                dangerouslySetInnerHTML={{ __html: highlightedLine }}
              />
              {hasIssue && (
                <div className="enhanced-line-issues">
                  <div className="issue-indicator-dot" style={{ backgroundColor: getSeverityColor(lineIssues[0].severity) }}>
                    <i className="bi bi-exclamation-triangle-fill"></i>
                  </div>
                </div>
              )}
            </div>
          )
        })}
      </div>
    )
  }

  // Enhanced Right Pane - AI Assistant
  const renderRightPane = () => {
    if (rightPaneCollapsed) {
      return (
        <div className="right-pane-collapsed">
          <Button 
            variant="link" 
            onClick={() => setRightPaneCollapsed(false)}
            className="collapse-toggle"
            style={{ 
              writingMode: 'vertical-lr',
              padding: '2rem 0.5rem',
              height: '100%',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              background: 'transparent',
              border: 'none',
              color: 'var(--text-muted)'
            }}
          >
            <i className="bi bi-chevron-left me-1"></i>
            <span>AI Assistant</span>
          </Button>
        </div>
      )
    }

    const selectedIssue = parsedIssues.find(issue => issue.id === selectedIssueId)
    const currentFileIssues = selectedFile 
      ? parsedIssues.filter(issue => issue.filePath === selectedFile)
      : parsedIssues

    return (
      <div className="enhanced-right-pane">
        <div className="enhanced-ai-header">
          <div className="d-flex align-items-center justify-content-between">
            <div className="ai-title-section">
              <div className="ai-status-indicator">
                <div className="status-dot active"></div>
                <h6 className="mb-0 fw-bold">AI Assistant</h6>
              </div>
            </div>
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

        <div className="enhanced-ai-content">
          {/* Enhanced Issue Cards */}
          <div className="ai-issues-section">
            {currentFileIssues.length > 0 ? (
              currentFileIssues.map(issue => (
                <div 
                  key={issue.id}
                  className={`enhanced-issue-card ${selectedIssueId === issue.id ? 'selected' : ''} ${fixedIssues.has(issue.id) ? 'fixed' : ''}`}
                  onClick={() => handleIssueClick(issue)}
                >
                  <div className="enhanced-issue-header">
                    <div className="severity-indicator">
                      <span 
                        className={`severity-badge-enhanced ${issue.severity}`}
                        style={{ 
                          backgroundColor: getSeverityBg(issue.severity),
                          color: getSeverityColor(issue.severity)
                        }}
                      >
                        {issue.severity.toUpperCase()}
                      </span>
                    </div>
                    <div className="issue-line-info">
                      Line {issue.lineNumber || '79'}
                    </div>
                  </div>
                  
                  <div className="enhanced-issue-body">
                    <h6 className="enhanced-issue-title">{issue.title}</h6>
                    <p className="enhanced-issue-description">
                      {issue.description}
                    </p>
                    
                    {/* AI Suggestion */}
                    <div className="ai-suggestion">
                      <div className="suggestion-icon">
                        <i className="bi bi-lightbulb"></i>
                      </div>
                      <div className="suggestion-text">
                        {issue.suggestion}
                      </div>
                    </div>
                  </div>
                </div>
              ))
            ) : (
              // Sample issues from the design
              <>
                <div className="enhanced-issue-card selected">
                  <div className="enhanced-issue-header">
                    <div className="severity-indicator">
                      <span className="severity-badge-enhanced high" style={{ backgroundColor: 'rgba(255, 193, 7, 0.1)', color: '#f59e0b' }}>
                        HIGH
                      </span>
                    </div>
                    <div className="issue-line-info">
                      Line 79
                    </div>
                  </div>
                  
                  <div className="enhanced-issue-body">
                    <h6 className="enhanced-issue-title">SQL injection vulnerability detected. User input is directly concatenated into SQL query without proper sanitization.</h6>
                    
                    <div className="ai-suggestion">
                      <div className="suggestion-icon">
                        <i className="bi bi-lightbulb"></i>
                      </div>
                      <div className="suggestion-text">
                        Use parameterized queries or prepared statements to prevent SQL injection.
                      </div>
                    </div>
                  </div>
                </div>
                
                <div className="enhanced-issue-card">
                  <div className="enhanced-issue-header">
                    <div className="severity-indicator">
                      <span className="severity-badge-enhanced high" style={{ backgroundColor: 'rgba(255, 193, 7, 0.1)', color: '#f59e0b' }}>
                        HIGH
                      </span>
                    </div>
                    <div className="issue-line-info">
                      Line 249
                    </div>
                  </div>
                  
                  <div className="enhanced-issue-body">
                    <h6 className="enhanced-issue-title">Potential performance issue: Missing index on frequently queried columns in large dataset.</h6>
                    
                    <div className="ai-suggestion">
                      <div className="suggestion-icon">
                        <i className="bi bi-lightbulb"></i>
                      </div>
                      <div className="suggestion-text">
                        Consider adding indexes on line_item_usage_account_name and line_item_usage_account_id.
                      </div>
                    </div>
                  </div>
                </div>
                
                <div className="enhanced-issue-card">
                  <div className="enhanced-issue-header">
                    <div className="severity-indicator">
                      <span className="severity-badge-enhanced high" style={{ backgroundColor: 'rgba(255, 193, 7, 0.1)', color: '#f59e0b' }}>
                        HIGH
                      </span>
                    </div>
                    <div className="issue-line-info">
                      Line 576
                    </div>
                  </div>
                  
                  <div className="enhanced-issue-body">
                    <h6 className="enhanced-issue-title">Exception handling is too broad. Catching all exceptions can hide important errors.</h6>
                    
                    <div className="ai-suggestion">
                      <div className="suggestion-icon">
                        <i className="bi bi-lightbulb"></i>
                      </div>
                      <div className="suggestion-text">
                        Catch specific exceptions like DatabaseError or ValueError instead of using bare except.
                      </div>
                    </div>
                  </div>
                </div>
              </>
            )}

          </div>
        
          {/* Chat Interface */}
          <div className="ai-chat-container">
            <div className="chat-input-section">
              <div className="chat-input-wrapper">
                <input
                  type="text"
                  className="chat-input"
                  placeholder="Ask about the code or issues..."
                />
                <div className="chat-actions">
                  <span className="chat-hint">Press Enter to send, Shift+Enter for new line</span>
                  <button className="send-button">
                    Send
                  </button>
                </div>
              </div>
            </div>
          </div>

        </div>
      </div>
    )
  }


  return (
    <div className="review-results-container">
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