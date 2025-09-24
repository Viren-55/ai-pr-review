'use client'

import React, { useState, useMemo } from 'react'
import { Container, Row, Col, Card, Badge, Button, Nav, ProgressBar } from 'react-bootstrap'
import TimingDisplay from './TimingDisplay'

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
  const originalCode = reviewData?.original_code || reviewData?.code || `// No code available`
  const [modifiedCode, setModifiedCode] = useState<string>(originalCode)
  const [appliedFixes, setAppliedFixes] = useState<Map<number, {originalLine: string, fixedLine: string, lineNumber: number}>>(new Map())
  
  // Use appropriate code based on view mode
  const sampleCode = viewMode === 'original' ? originalCode : modifiedCode

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

  const applyIntelligentFix = (originalLine: string, issue: ParsedIssue): string => {
    const title = issue.title.toLowerCase()
    const suggestion = issue.suggestion.toLowerCase()
    const indent = originalLine.match(/^\s*/)?.[0] || ''
    
    // Print statement fixes
    if (title.includes('print') && originalLine.includes('print(')) {
      return originalLine.replace('print(', 'logging.info(')
    }
    
    // Missing docstring fixes
    if (title.includes('docstring') || title.includes('documentation')) {
      if (originalLine.trim().startsWith('def ')) {
        return `${originalLine}\n${indent}    """TODO: Add function docstring."""`
      }
      if (originalLine.trim().startsWith('class ')) {
        return `${originalLine}\n${indent}    """TODO: Add class docstring."""`
      }
      // For module-level docstring
      return `${indent}"""TODO: Add module docstring."""\n${originalLine}`
    }
    
    // Main entry point guard fixes
    if (title.includes('main') && title.includes('guard')) {
      if (originalLine.includes('main()') && !originalLine.includes('__name__')) {
        return originalLine.replace(/^(\s*)(.*)$/, '$1if __name__ == "__main__":\n$1    $2')
      }
    }
    
    // SQL injection fixes
    if (title.includes('sql') && title.includes('injection')) {
      if (originalLine.includes('" + ') || originalLine.includes("' + ")) {
        // Simple parameterized query suggestion
        return originalLine.replace(/["'].*?["']/, '"SELECT * FROM users WHERE username = %s"')
          .replace(/\s*\+\s*\w+\s*\+?\s*["'].*?["']?/, ', (username,)')
      }
    }
    
    // Hardcoded values fixes
    if (title.includes('hardcoded') || title.includes('credential')) {
      if (originalLine.includes('=') && (originalLine.includes('"') || originalLine.includes("'"))) {
        const varName = originalLine.split('=')[0].trim()
        return originalLine.replace(/=\s*["'].*?["']/, `= os.getenv('${varName.toUpperCase()}')`)
      }
    }
    
    // Exception handling fixes
    if (title.includes('exception') && originalLine.includes('except:')) {
      return originalLine.replace('except:', 'except Exception as e:')
    }
    
    // Import organization
    if (title.includes('import') && title.includes('unused')) {
      // Remove the line if it's an unused import
      if (originalLine.trim().startsWith('import ') || originalLine.trim().startsWith('from ')) {
        return '' // Remove the line
      }
    }
    
    // Default: return original line if no specific fix applies
    return originalLine
  }

  const handleFixIssue = async (issue: ParsedIssue) => {
    try {
      // For now, simulate a successful fix since we have the suggested fix already
      if (issue.fixedCode || issue.suggestion) {
        // Apply the fix to the code
        let newCode = modifiedCode
        
        if (issue.lineNumber && issue.codeSnippet) {
          // Try to replace the specific line
          const lines = newCode.split('\n')
          const lineIndex = issue.lineNumber - 1
          
          if (lineIndex >= 0 && lineIndex < lines.length) {
            const originalLine = lines[lineIndex]
            let fixedLine = originalLine
            
            // Apply intelligent code fixes based on issue type
            fixedLine = applyIntelligentFix(originalLine, issue)
            
            // Add necessary imports if needed
            if (issue.title.toLowerCase().includes('print') && fixedLine.includes('logging.info')) {
              // Add logging import at the top if not already present
              if (!newCode.includes('import logging')) {
                const firstLine = lines[0]
                if (firstLine.includes('import') || firstLine.includes('from')) {
                  // Add after existing imports
                  let insertIndex = 0
                  for (let i = 0; i < lines.length; i++) {
                    if (lines[i].includes('import') || lines[i].includes('from')) {
                      insertIndex = i + 1
                    } else if (lines[i].trim() === '') {
                      continue
                    } else {
                      break
                    }
                  }
                  lines.splice(insertIndex, 0, 'import logging')
                } else {
                  // Add at the very beginning
                  lines.unshift('import logging', '')
                }
              }
            }
            
            // Handle cases where we need to add os import
            if (fixedLine.includes('os.getenv') && !newCode.includes('import os')) {
              // Add os import
              if (lines[0].includes('import')) {
                lines.splice(1, 0, 'import os')
              } else {
                lines.unshift('import os', '')
              }
            }
            
            // Track the fix for undo functionality
            setAppliedFixes(prev => new Map(prev.set(issue.id, {
              originalLine,
              fixedLine,
              lineNumber: issue.lineNumber
            })))
            
            lines[lineIndex] = fixedLine
            newCode = lines.join('\n')
          }
        }
        
        // Update the modified code
        setModifiedCode(newCode)
        
        // Mark as fixed
        setFixedIssues(prev => new Set(prev.add(issue.id)))
        
        // Show success message
        alert(`✅ Intelligent fix applied!\n\nIssue: ${issue.title}\n🔧 Applied: Smart code transformation\n\n💡 Switch to "Fixed" or "Diff" view to see changes.`)
        
        console.log('Issue fixed:', {
          id: issue.id,
          title: issue.title,
          suggestedFix: issue.fixedCode,
          explanation: issue.suggestion
        })
      } else {
        alert('⚠️ No fix available for this issue.')
      }
    } catch (error) {
      console.error('Error applying fix:', error)
      alert('❌ Error applying fix. Please try again.')
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
                <span className="file-name">{selectedFile?.split('/').pop() || reviewData?.filename || 'submitted_code.py'}</span>
              </div>
              <div className="file-meta">
                <span className="language-badge">Python</span>
                <span className="line-count">• {sampleCode.split('\n').length} lines</span>
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
                {renderEnhancedCodeLines(originalCode.split('\n'), 'original')}
              </div>
              <div className="diff-pane diff-after">
                <div className="diff-header">
                  <i className="bi bi-plus-circle text-success me-2"></i>
                  Fixed Code
                </div>
                {renderEnhancedCodeLines(modifiedCode.split('\n'), 'fixed')}
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

  // Clean syntax highlighting for Python without HTML markup
  const highlightPythonSyntax = (code: string) => {
    // Return clean code without HTML markup to avoid showing HTML tags in the UI
    // TODO: Implement proper syntax highlighting with CSS classes
    return code
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
          {/* Performance Timing Display */}
          {reviewData?.timing && (
            <div className="mb-3">
              <TimingDisplay timing={reviewData.timing} />
            </div>
          )}
          
          {/* Issues Section Header */}
          <div className="issues-section-header">
            <h5 className="issues-title">
              <i className="bi bi-exclamation-triangle me-2"></i>
              Code Issues {currentFileIssues.length > 0 && `(${currentFileIssues.length})`}
            </h5>
            {currentFileIssues.length > 0 && (
              <div className="issues-summary">
                <span className="text-muted">
                  Found in {selectedFile ? selectedFile.split('/').pop() : 'current file'}
                </span>
              </div>
            )}
          </div>
          
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
                      {issue.lineNumber ? `Line ${issue.lineNumber}` : 'Multiple lines'}
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
                    
                    {/* Auto-Fix Actions */}
                    <div className="issue-actions">
                      {!fixedIssues.has(issue.id) ? (
                        <div className="action-buttons">
                          <button
                            className="btn btn-sm btn-outline-primary apply-fix-btn"
                            onClick={(e) => {
                              e.stopPropagation();
                              handleFixIssue(issue);
                            }}
                            title="Apply AI-suggested fix"
                          >
                            <i className="bi bi-magic"></i>
                            Apply Fix
                          </button>
                          <button
                            className="btn btn-sm btn-outline-secondary preview-fix-btn"
                            onClick={(e) => {
                              e.stopPropagation();
                              // Show fix preview
                              const previewMessage = `🔍 Fix Preview for: ${issue.title}\n\n` +
                                `📍 Location: Line ${issue.lineNumber || 'Multiple lines'}\n\n` +
                                `🔧 Suggested Fix:\n${issue.suggestion}\n\n` +
                                `${issue.fixedCode ? `💻 Code Change:\n${issue.fixedCode}` : ''}`;
                              
                              alert(previewMessage);
                            }}
                            title="Preview changes before applying"
                          >
                            <i className="bi bi-eye"></i>
                            Preview
                          </button>
                        </div>
                      ) : (
                        <div className="fix-applied-status">
                          <i className="bi bi-check-circle-fill text-success"></i>
                          <span className="text-success ms-2">Fix Applied</span>
                          <button
                            className="btn btn-sm btn-outline-warning ms-2 undo-fix-btn"
                            onClick={(e) => {
                              e.stopPropagation();
                              
                              // Revert the code changes
                              const fixInfo = appliedFixes.get(issue.id)
                              if (fixInfo) {
                                const lines = modifiedCode.split('\n')
                                const lineIndex = fixInfo.lineNumber - 1
                                if (lineIndex >= 0 && lineIndex < lines.length) {
                                  lines[lineIndex] = fixInfo.originalLine
                                  setModifiedCode(lines.join('\n'))
                                }
                                
                                // Remove from applied fixes
                                setAppliedFixes(prev => {
                                  const newMap = new Map(prev)
                                  newMap.delete(issue.id)
                                  return newMap
                                })
                              }
                              
                              // Remove from fixed issues
                              setFixedIssues(prev => {
                                const newSet = new Set(prev);
                                newSet.delete(issue.id);
                                return newSet;
                              });
                            }}
                            title="Undo this fix"
                          >
                            <i className="bi bi-arrow-counterclockwise"></i>
                            Undo
                          </button>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))
            ) : (
              // No issues found - show empty state
              <div className="text-center py-5">
                <div className="mb-3">
                  <i className="bi bi-check-circle text-success" style={{ fontSize: '3rem' }}></i>
                </div>
                <h5 className="text-muted">No Issues Found</h5>
                <p className="text-secondary">Your code looks great! No issues detected in this file.</p>
              </div>
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