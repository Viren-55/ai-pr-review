'use client'

import { useState } from 'react'
import HomePage from '@/components/HomePage'
import SubmitCodePage from '@/components/SubmitCodePage'
import ReviewResultsPage from '@/components/ReviewResultsPage'
import DetailedFindingsPage from '@/components/DetailedFindingsPage'
import ThemeToggle from '@/components/ThemeToggle'
import { Navbar, Container, Nav } from 'react-bootstrap'

export default function App() {
  const [currentPage, setCurrentPage] = useState('home')
  const [reviewData, setReviewData] = useState(null)
  const [submittedCode, setSubmittedCode] = useState(null)

  const handleStartReview = () => {
    setCurrentPage('submit')
  }

  const handleCodeSubmit = async (code: string, language: string, type: string, filename?: string) => {
    setSubmittedCode({ code, language, type, filename })
    
    // Call new backend API
    try {
      let response;
      
      if (type === 'upload' && filename) {
        // For file uploads, use the upload endpoint
        const formData = new FormData()
        formData.append('language', language)
        // Create a File object from the code string for consistency
        const file = new File([code], filename, { type: 'text/plain' })
        formData.append('file', file)
        
        response = await fetch('http://localhost:8000/api/upload', {
          method: 'POST',
          body: formData
        })
      } else {
        // For direct code submission - use real API endpoint
        response = await fetch('http://localhost:8000/api/submissions', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ 
            code, 
            language, 
            filename: filename || null,
            submission_type: type 
          })
        })
      }
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      const data = await response.json()
      
      // Transform the new API response to match the expected format
      const transformedData = {
        ...data,
        submission_id: data.id,
        status: 'success',
        timestamp: data.created_at,
        model_used: data.analysis?.model_used || 'unknown',
        review: data.analysis ? formatAnalysisText(data.analysis) : 'Analysis pending...'
      }
      
      setReviewData(transformedData)
      setCurrentPage('results')
    } catch (error) {
      console.error('Review failed:', error)
      // Show error state or fallback
      setReviewData({
        status: 'error',
        error: 'Failed to analyze code. Please try again.',
        timestamp: new Date().toISOString()
      })
      setCurrentPage('results')
    }
  }

  const formatAnalysisText = (analysis: any) => {
    const issues = analysis.issues || []
    const issuesText = issues.map((issue: any) => 
      `**${issue.title}** (${issue.severity.toUpperCase()})\n${issue.description}`
    ).join('\n\n')
    
    return `
Overall Score: ${analysis.overall_score}/100

Issues Found:
${issuesText}

${analysis.analysis_summary}
    `.trim()
  }

  const handleViewDetails = () => {
    setCurrentPage('details')
  }

  const handleNewReview = () => {
    setReviewData(null)
    setSubmittedCode(null)
    setCurrentPage('submit')
  }

  return (
    <div className="min-vh-100">
      {/* Enhanced Navigation Bar */}
      <Navbar expand="lg" className="enhanced-navbar shadow-sm">
        <Container fluid className="px-4">
          <Navbar.Brand 
            href="#" 
            onClick={() => setCurrentPage('home')}
            className="fw-bold d-flex align-items-center"
          >
            <i className="bi bi-layers me-2 text-primary"></i>
            AI Code Review
          </Navbar.Brand>
          
          <div className="navbar-center d-flex align-items-center">
            {reviewData && currentPage === 'results' && (
              <>
                <Nav className="navbar-nav-center">
                  <Nav.Link 
                    onClick={() => setCurrentPage('submit')}
                    className="nav-tab"
                  >
                    Submit Code
                  </Nav.Link>
                  <Nav.Link 
                    onClick={() => setCurrentPage('results')}
                    active={currentPage === 'results'}
                    className="nav-tab active"
                  >
                    Results
                  </Nav.Link>
                  <Nav.Link 
                    onClick={() => setCurrentPage('details')}
                    className="nav-tab"
                  >
                    Details
                  </Nav.Link>
                </Nav>
                
                {/* Issue Statistics */}
                <div className="issue-stats ms-4">
                  <span className="stat-item critical">
                    <span className="count">0</span>
                    <span className="label">C</span>
                  </span>
                  <span className="stat-item high">
                    <span className="count">3</span>
                    <span className="label">H</span>
                  </span>
                  <span className="stat-item medium">
                    <span className="count">1</span>
                    <span className="label">M</span>
                  </span>
                  <span className="stat-item low">
                    <span className="count">0</span>
                    <span className="label">L</span>
                  </span>
                </div>
              </>
            )}
            
            {!reviewData && (
              <Nav className="navbar-nav-center">
                <Nav.Link 
                  onClick={() => setCurrentPage('home')}
                  active={currentPage === 'home'}
                  className="nav-tab"
                >
                  Home
                </Nav.Link>
                <Nav.Link 
                  onClick={() => setCurrentPage('submit')}
                  active={currentPage === 'submit'}
                  className="nav-tab"
                >
                  Submit Code
                </Nav.Link>
              </Nav>
            )}
          </div>
          
          <div className="navbar-right d-flex align-items-center">
            {reviewData && currentPage === 'results' && (
              <button className="btn btn-outline-primary btn-sm me-3">
                <i className="bi bi-flag me-1"></i>
                Report
              </button>
            )}
            <ThemeToggle />
          </div>
        </Container>
      </Navbar>

      {/* Page Content */}
      <div style={{ minHeight: 'calc(100vh - 56px)' }}>
        {currentPage === 'home' && (
          <div className="animate-fade-in">
            <HomePage onStartReview={handleStartReview} />
          </div>
        )}
        {currentPage === 'submit' && (
          <div className="animate-fade-in">
            <SubmitCodePage onSubmit={handleCodeSubmit} />
          </div>
        )}
        {currentPage === 'results' && reviewData && (
          <div className="animate-fade-in">
            <ReviewResultsPage 
              reviewData={reviewData}
              onViewDetails={handleViewDetails}
              onNewReview={handleNewReview}
            />
          </div>
        )}
        {currentPage === 'details' && reviewData && (
          <div className="animate-fade-in">
            <DetailedFindingsPage 
              reviewData={reviewData}
              onNewReview={handleNewReview}
            />
          </div>
        )}
      </div>
    </div>
  )
}