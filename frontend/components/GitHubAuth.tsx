'use client'

import React, { useState, useEffect } from 'react'
import { Button, Dropdown, Spinner, Alert } from 'react-bootstrap'

interface GitHubUser {
  id: number
  github_id: number
  username: string
  email?: string
  avatar_url?: string
  created_at: string
}

interface GitHubAuthProps {
  onUserChange?: (user: GitHubUser | null) => void
}

export default function GitHubAuth({ onUserChange }: GitHubAuthProps) {
  const [user, setUser] = useState<GitHubUser | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')

  // Check if user is already authenticated on component mount
  useEffect(() => {
    checkAuthStatus()
  }, [])

  const checkAuthStatus = async () => {
    try {
      const response = await fetch('http://localhost:8000/auth/user', {
        credentials: 'include'
      })
      
      if (response.ok) {
        const userData = await response.json()
        setUser(userData)
        onUserChange?.(userData)
      }
    } catch (error) {
      // User not authenticated, this is fine
      console.log('User not authenticated')
    }
  }

  const handleGitHubLogin = async () => {
    setIsLoading(true)
    setError('')

    try {
      // Simple token-based authentication - prompt for token
      const token = prompt('Enter your GitHub Personal Access Token (for demo):')
      
      if (!token) {
        setIsLoading(false)
        return
      }

      // Validate token with backend
      const response = await fetch('http://localhost:8000/auth/token/validate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ token })
      })

      const result = await response.json()

      if (result.success && result.user) {
        setUser(result.user)
        onUserChange?.(result.user)
      } else {
        throw new Error(result.message || 'Token validation failed')
      }
      
    } catch (error) {
      console.error('GitHub login failed:', error)
      setError('Failed to authenticate with GitHub token.')
    } finally {
      setIsLoading(false)
    }
  }

  const handleLogout = async () => {
    setIsLoading(true)
    
    try {
      await fetch('http://localhost:8000/auth/logout', {
        method: 'POST',
        credentials: 'include'
      })
      
      setUser(null)
      onUserChange?.(null)
    } catch (error) {
      console.error('Logout failed:', error)
    } finally {
      setIsLoading(false)
    }
  }


  if (isLoading) {
    return (
      <Button variant="outline-primary" disabled>
        <Spinner size="sm" className="me-2" />
        Connecting...
      </Button>
    )
  }

  if (!user) {
    return (
      <div>
        <Button variant="outline-primary" onClick={handleGitHubLogin}>
          <i className="bi bi-github me-2"></i>
          Sign in with GitHub
        </Button>
        {error && (
          <Alert variant="danger" className="mt-2 mb-0">
            <small>{error}</small>
          </Alert>
        )}
      </div>
    )
  }

  return (
    <Dropdown align="end">
      <Dropdown.Toggle variant="outline-light" className="d-flex align-items-center">
        {user.avatar_url && (
          <img 
            src={user.avatar_url} 
            alt={user.username}
            className="rounded-circle me-2"
            width="24"
            height="24"
          />
        )}
        <span className="me-2">{user.username}</span>
      </Dropdown.Toggle>

      <Dropdown.Menu>
        <Dropdown.Header>
          <div className="d-flex align-items-center">
            {user.avatar_url && (
              <img 
                src={user.avatar_url} 
                alt={user.username}
                className="rounded-circle me-2"
                width="32"
                height="32"
              />
            )}
            <div>
              <div className="fw-bold">{user.username}</div>
              {user.email && <small className="text-muted">{user.email}</small>}
            </div>
          </div>
        </Dropdown.Header>
        
        <Dropdown.Divider />
        
        <Dropdown.Item href="#" className="text-muted">
          <i className="bi bi-github me-2"></i>
          GitHub Profile
        </Dropdown.Item>
        
        <Dropdown.Item href="#" className="text-muted">
          <i className="bi bi-clock-history me-2"></i>
          PR Analysis History
        </Dropdown.Item>
        
        <Dropdown.Divider />
        
        <Dropdown.Item onClick={handleLogout}>
          <i className="bi bi-box-arrow-right me-2"></i>
          Sign Out
        </Dropdown.Item>
      </Dropdown.Menu>
    </Dropdown>
  )
}