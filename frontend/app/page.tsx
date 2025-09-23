'use client'

import { useState } from 'react'
import HomePage from '@/components/HomePage'
import SubmitCodePage from '@/components/SubmitCodePage'
import ReviewResultsPage from '@/components/ReviewResultsPage'
import DetailedFindingsPage from '@/components/DetailedFindingsPage'
import ThemeToggle from '@/components/ThemeToggle'
import GitHubAuth from '@/components/GitHubAuth'
import { Navbar, Container, Nav } from 'react-bootstrap'
import { useCodeReview } from '@/lib/hooks/useCodeReview'

interface GitHubUser {
  id: number
  github_id: number
  username: string
  email?: string
  avatar_url?: string
  created_at: string
}

export default function App() {
  const [currentPage, setCurrentPage] = useState('home')
  const [submittedCode, setSubmittedCode] = useState(null)
  const [user, setUser] = useState<GitHubUser | null>(null)
  
  // Use the proper hook for code review functionality
  const { isReviewing, reviewData, error, reviewCode, reviewGitHubPR } = useCodeReview()

  const handleStartReview = () => {
    setCurrentPage('submit')
  }

  const handleCodeSubmit = async (code: string, language: string, type: string, filename?: string) => {
    setSubmittedCode({ code, language, type, filename })
    
    try {
      if (type === 'github') {
        // For GitHub PR submissions - extract URL from code and use the proper hook
        const githubUrl = code.replace('GitHub PR: ', '').trim()
        await reviewGitHubPR(githubUrl, language)
      } else {
        // For direct code submission, use the reviewCode hook
        await reviewCode(code, language, filename)
      }
      
      // Navigate to results page
      setCurrentPage('results')
    } catch (error) {
      console.error('Review failed:', error)
      // Error handling is done by the hook, just navigate to results to show the error
      setCurrentPage('results')
    }
  }


  const handleViewDetails = () => {
    setCurrentPage('details')
  }

  const handleNewReview = () => {
    setSubmittedCode(null)
    setCurrentPage('submit')
    // Note: reviewData is now managed by the useCodeReview hook
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
            <GitHubAuth onUserChange={setUser} />
            <div className="ms-3">
              <ThemeToggle />
            </div>
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
            <SubmitCodePage onSubmit={handleCodeSubmit} user={user} />
          </div>
        )}
        {currentPage === 'results' && (reviewData || error || isReviewing) && (
          <div className="animate-fade-in">
            {isReviewing ? (
              <div className="d-flex justify-content-center align-items-center" style={{ minHeight: '400px' }}>
                <div className="text-center">
                  <div className="spinner-border text-primary mb-3" role="status">
                    <span className="visually-hidden">Loading...</span>
                  </div>
                  <h5>Analyzing your code...</h5>
                  <p className="text-muted">This may take a moment</p>
                </div>
              </div>
            ) : error ? (
              <div className="d-flex justify-content-center align-items-center" style={{ minHeight: '400px' }}>
                <div className="text-center">
                  <div className="text-danger mb-3">
                    <i className="bi bi-exclamation-triangle" style={{ fontSize: '3rem' }}></i>
                  </div>
                  <h5 className="text-danger">Analysis Failed</h5>
                  <p className="text-muted mb-4">{error}</p>
                  <button className="btn btn-primary" onClick={() => setCurrentPage('submit')}>
                    <i className="bi bi-arrow-left me-2"></i>
                    Try Again
                  </button>
                </div>
              </div>
            ) : reviewData ? (
              <ReviewResultsPage 
                reviewData={reviewData}
                onViewDetails={handleViewDetails}
                onNewReview={handleNewReview}
              />
            ) : null}
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