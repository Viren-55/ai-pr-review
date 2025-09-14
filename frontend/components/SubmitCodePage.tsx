'use client'

import React, { useState, useCallback, useRef } from 'react'
import { Container, Row, Col, Card, Button, Form, Alert, Spinner, Nav, Tab } from 'react-bootstrap'

interface SubmitCodePageProps {
  onSubmit: (code: string, language: string, type: string, filename?: string) => void
}

export default function SubmitCodePage({ onSubmit }: SubmitCodePageProps) {
  const [activeTab, setActiveTab] = useState<'paste' | 'upload' | 'github'>('paste')
  const [code, setCode] = useState('')
  const [language, setLanguage] = useState('python')
  const [githubUrl, setGithubUrl] = useState('')
  const [file, setFile] = useState<File | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState('')
  const [dragOver, setDragOver] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleSubmit = async () => {
    setError('')
    setIsSubmitting(true)

    try {
      let codeToSubmit = ''
      let submissionType = activeTab

      if (activeTab === 'paste') {
        if (!code.trim()) {
          setError('Please enter some code to review')
          setIsSubmitting(false)
          return
        }
        codeToSubmit = code
      } else if (activeTab === 'upload') {
        if (!file) {
          setError('Please select a file to upload')
          setIsSubmitting(false)
          return
        }
        codeToSubmit = await file.text()
      } else if (activeTab === 'github') {
        if (!githubUrl.trim()) {
          setError('Please enter a GitHub PR URL')
          setIsSubmitting(false)
          return
        }
        codeToSubmit = `GitHub PR: ${githubUrl}`
        submissionType = 'github'
      }

      await onSubmit(codeToSubmit, language, submissionType, file?.name)
    } catch (err) {
      setError('Failed to submit code for review')
    }
    
    setIsSubmitting(false)
  }

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    setDragOver(true)
  }

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault()
    setDragOver(false)
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setDragOver(false)
    const files = e.dataTransfer.files
    if (files.length > 0) {
      setFile(files[0])
      setActiveTab('upload')
    }
  }

  const handleUploadClick = (e: React.MouseEvent) => {
    e.preventDefault()
    e.stopPropagation()
    console.log('Upload zone clicked')
    if (fileInputRef.current) {
      fileInputRef.current.click()
    }
  }


  return (
    <div className="py-5" style={{ minHeight: '100vh' }}>
      <Container fluid>
        <Row className="justify-content-center">
          <Col xl={8} lg={10} md={11}>
            {/* Clean Header */}
            <div className="text-center mb-5">
              <h1 className="display-5 fw-bold mb-3 text-gradient">Code Analysis</h1>
              <p className="text-secondary fs-5" style={{ maxWidth: '500px', margin: '0 auto' }}>
                Submit your code for comprehensive AI-powered analysis
              </p>
            </div>

            {/* Main Content Card */}
            <Card className="glass-card border-0 shadow-lg">
              <Card.Body className="p-0">
                {/* Tabbed Interface */}
                <Nav variant="pills" className="justify-content-center p-4 border-bottom border-opacity-10">
                  <Nav.Item>
                    <Nav.Link 
                      active={activeTab === 'paste'} 
                      onClick={() => setActiveTab('paste')}
                      className="px-4 py-2 mx-2 fw-semibold"
                    >
                      <i className="bi bi-code-square me-2"></i>
                      Paste Code
                    </Nav.Link>
                  </Nav.Item>
                  <Nav.Item>
                    <Nav.Link 
                      active={activeTab === 'upload'} 
                      onClick={() => setActiveTab('upload')}
                      className="px-4 py-2 mx-2 fw-semibold"
                    >
                      <i className="bi bi-cloud-upload me-2"></i>
                      Upload File
                    </Nav.Link>
                  </Nav.Item>
                  <Nav.Item>
                    <Nav.Link 
                      active={activeTab === 'github'} 
                      onClick={() => setActiveTab('github')}
                      className="px-4 py-2 mx-2 fw-semibold"
                    >
                      <i className="bi bi-github me-2"></i>
                      GitHub PR
                    </Nav.Link>
                  </Nav.Item>
                </Nav>

                {/* Tab Content */}
                <div className="p-5">
                  {activeTab === 'paste' && (
                    <div className="animate-fade-in">
                      <div className="text-center mb-4">
                        <div className="glass-card rounded-circle p-4 d-inline-flex mb-3" style={{ width: '80px', height: '80px' }}>
                          <i className="bi bi-code-square text-primary display-6"></i>
                        </div>
                        <h4 className="fw-bold text-primary mb-2">Paste Your Code</h4>
                        <p className="text-secondary">Copy and paste your code directly for instant analysis</p>
                      </div>
                      
                      <Form.Control
                        as="textarea"
                        rows={12}
                        placeholder={`// Paste your code here...
function fibonacci(n) {
  if (n <= 1) return n;
  return fibonacci(n-1) + fibonacci(n-2);
}

console.log(fibonacci(10));`}
                        value={code}
                        onChange={(e) => setCode(e.target.value)}
                        className="font-monospace"
                        style={{ 
                          fontSize: '0.9rem',
                          background: 'rgba(0, 0, 0, 0.4)',
                          border: '1px solid rgba(255, 255, 255, 0.1)',
                          borderRadius: '1rem',
                          color: 'var(--text-primary)',
                          resize: 'vertical',
                          minHeight: '300px'
                        }}
                      />
                      <div className="mt-3 text-center">
                        <small className="text-secondary">
                          <i className="bi bi-info-circle me-1"></i>
                          Supports all major programming languages
                        </small>
                      </div>
                    </div>
                  )}

                  {activeTab === 'upload' && (
                    <div className="animate-fade-in">
                      <div className="text-center mb-4">
                        <div className="glass-card rounded-circle p-4 d-inline-flex mb-3" style={{ width: '80px', height: '80px' }}>
                          <i className="bi bi-cloud-upload text-success display-6"></i>
                        </div>
                        <h4 className="fw-bold text-primary mb-2">Upload File</h4>
                        <p className="text-secondary">Upload code files from your computer with drag & drop support</p>
                      </div>
                      
                      <div 
                        className={`clean-upload-zone ${dragOver ? 'drag-over' : ''} ${file ? 'has-file' : ''}`}
                        onDragOver={handleDragOver}
                        onDragLeave={handleDragLeave}
                        onDrop={handleDrop}
                        onClick={handleUploadClick}
                        role="button"
                        tabIndex={0}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter' || e.key === ' ') {
                            e.preventDefault()
                            handleUploadClick(e as any)
                          }
                        }}
                      >
                        {!file ? (
                          <>
                            <i className="bi bi-cloud-arrow-up display-1 text-primary mb-3"></i>
                            <h5 className="fw-bold text-primary mb-2">Drop your file here</h5>
                            <p className="text-secondary mb-3">or click to browse files</p>
                            <div className="d-flex justify-content-center gap-2 flex-wrap">
                              <span className="badge bg-primary bg-opacity-25 text-primary">.py</span>
                              <span className="badge bg-primary bg-opacity-25 text-primary">.js</span>
                              <span className="badge bg-primary bg-opacity-25 text-primary">.ts</span>
                              <span className="badge bg-primary bg-opacity-25 text-primary">.java</span>
                              <span className="badge bg-primary bg-opacity-25 text-primary">.cpp</span>
                              <span className="badge bg-primary bg-opacity-25 text-primary">+15 more</span>
                            </div>
                          </>
                        ) : (
                          <div className="uploaded-file-info">
                            <i className="bi bi-file-earmark-code text-success display-4 mb-3"></i>
                            <h5 className="fw-bold text-success mb-1">{file.name}</h5>
                            <p className="text-secondary mb-2">{(file.size / 1024).toFixed(1)} KB</p>
                            <Button variant="outline-secondary" size="sm" onClick={(e) => {
                              e.stopPropagation()
                              setFile(null)
                            }}>
                              <i className="bi bi-x-circle me-1"></i>
                              Remove
                            </Button>
                          </div>
                        )}
                      </div>
                      
                      <input
                        ref={fileInputRef}
                        type="file"
                        onChange={(e) => setFile(e.target.files?.[0] || null)}
                        accept=".py,.js,.ts,.jsx,.tsx,.java,.cpp,.c,.go,.rb,.php,.cs,.swift,.kt,.rs,.scala,.dart,.r,.m,.pl,.sh"
                        style={{ display: 'none' }}
                      />
                    </div>
                  )}

                  {activeTab === 'github' && (
                    <div className="animate-fade-in">
                      <div className="text-center mb-4">
                        <div className="glass-card rounded-circle p-4 d-inline-flex mb-3" style={{ width: '80px', height: '80px' }}>
                          <i className="bi bi-github text-primary display-6"></i>
                        </div>
                        <h4 className="fw-bold text-primary mb-2">GitHub Pull Request</h4>
                        <p className="text-secondary">Analyze entire GitHub Pull Requests with full context and diff analysis</p>
                      </div>
                      
                      <div className="mb-4">
                        <Form.Label className="fw-semibold mb-3">Pull Request URL</Form.Label>
                        <Form.Control
                          type="url"
                          size="lg"
                          placeholder="https://github.com/owner/repository/pull/123"
                          value={githubUrl}
                          onChange={(e) => setGithubUrl(e.target.value)}
                          style={{
                            background: 'rgba(0, 0, 0, 0.4)',
                            border: '1px solid rgba(255, 255, 255, 0.1)',
                            borderRadius: '1rem',
                            color: 'var(--text-primary)',
                            padding: '1rem 1.5rem'
                          }}
                        />
                      </div>
                      
                      <div className="text-center">
                        <small className="text-secondary">
                          <i className="bi bi-info-circle me-1"></i>
                          We'll analyze all changed files and provide comprehensive feedback on your pull request
                        </small>
                      </div>
                    </div>
                  )}
                </div>

                {/* Configuration Section */}
                <div className="border-top border-opacity-10 p-5">
                  <Row className="align-items-center g-4">
                    <Col lg={4}>
                      <Form.Group>
                        <Form.Label className="fw-semibold mb-3 d-flex align-items-center">
                          <i className="bi bi-code-slash me-2 text-primary"></i>
                          Language
                        </Form.Label>
                        <Form.Select 
                          value={language}
                          onChange={(e) => setLanguage(e.target.value)}
                          size="lg"
                          style={{
                            background: 'rgba(255, 255, 255, 0.05)',
                            border: '1px solid rgba(255, 255, 255, 0.1)',
                            color: 'var(--text-primary)',
                            borderRadius: '0.75rem'
                          }}
                        >
                          <option value="python">🐍 Python</option>
                          <option value="javascript">⚡ JavaScript</option>
                          <option value="typescript">📘 TypeScript</option>
                          <option value="java">☕ Java</option>
                          <option value="cpp">⚙️ C++</option>
                          <option value="go">🚀 Go</option>
                          <option value="rust">🦀 Rust</option>
                          <option value="php">🐘 PHP</option>
                          <option value="ruby">💎 Ruby</option>
                          <option value="csharp">🔷 C#</option>
                        </Form.Select>
                      </Form.Group>
                    </Col>
                    
                    <Col lg={8}>
                      <div className="d-flex flex-column justify-content-end h-100">
                        <div className="mb-3">
                          <small className="text-secondary d-flex align-items-center justify-content-center">
                            <i className="bi bi-shield-check text-success me-2"></i>
                            Enterprise Security • Zero Data Retention • SOC 2 Compliant
                          </small>
                        </div>
                        
                        <div className="d-flex gap-3 justify-content-center">
                          <Button
                            variant="outline-secondary"
                            size="lg"
                            className="px-4"
                            onClick={() => {
                              setCode('')
                              setFile(null)
                              setGithubUrl('')
                              setError('')
                            }}
                          >
                            <i className="bi bi-arrow-counterclockwise me-2"></i>
                            Reset
                          </Button>
                          
                          <Button
                            variant="primary"
                            size="lg"
                            onClick={handleSubmit}
                            disabled={isSubmitting || (
                              (activeTab === 'paste' && !code.trim()) ||
                              (activeTab === 'upload' && !file) ||
                              (activeTab === 'github' && !githubUrl.trim())
                            )}
                            className="px-5 fw-bold"
                          >
                            {isSubmitting ? (
                              <>
                                <Spinner animation="border" size="sm" className="me-2" />
                                Analyzing...
                              </>
                            ) : (
                              <>
                                <i className="bi bi-cpu me-2"></i>
                                Start Analysis
                              </>
                            )}
                          </Button>
                        </div>
                      </div>
                    </Col>
                  </Row>

                  {error && (
                    <Alert 
                      variant="danger" 
                      className="mt-4 animate-fade-in" 
                      dismissible 
                      onClose={() => setError('')}
                      style={{
                        background: 'rgba(220, 53, 69, 0.1)',
                        border: '1px solid rgba(220, 53, 69, 0.3)',
                        borderRadius: '1rem'
                      }}
                    >
                      <div className="d-flex align-items-center">
                        <i className="bi bi-exclamation-triangle text-danger me-2"></i>
                        <span>{error}</span>
                      </div>
                    </Alert>
                  )}
                </div>
              </Card.Body>
            </Card>

            {/* Features Section - Simplified */}
            <div className="mt-5 pt-4">
              <Row className="g-4 text-center">
                <Col md={4}>
                  <div className="p-3">
                    <i className="bi bi-lightning-charge text-warning display-6 mb-3"></i>
                    <h6 className="fw-bold text-primary mb-2">Lightning Fast</h6>
                    <small className="text-secondary">Results in under 30 seconds</small>
                  </div>
                </Col>
                <Col md={4}>
                  <div className="p-3">
                    <i className="bi bi-shield-check text-success display-6 mb-3"></i>
                    <h6 className="fw-bold text-primary mb-2">Secure & Private</h6>
                    <small className="text-secondary">Zero data retention policy</small>
                  </div>
                </Col>
                <Col md={4}>
                  <div className="p-3">
                    <i className="bi bi-cpu text-info display-6 mb-3"></i>
                    <h6 className="fw-bold text-primary mb-2">AI-Powered</h6>
                    <small className="text-secondary">5 specialized analysis agents</small>
                  </div>
                </Col>
              </Row>
            </div>
          </Col>
        </Row>
      </Container>
    </div>
  )
}