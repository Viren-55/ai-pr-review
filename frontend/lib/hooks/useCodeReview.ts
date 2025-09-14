'use client'

import { useState, useCallback } from 'react'
import axios from 'axios'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
const IS_DEVELOPMENT = process.env.NODE_ENV === 'development'

// Mock data for development when backend is not available
const getMockReviewData = (): ReviewData => ({
  thread_id: 'mock-thread-123',
  findings: [
    {
      type: 'Security',
      description: 'Potential SQL injection vulnerability',
      location: 'Line 15-17',
      severity: 'High',
      suggestion: 'Use parameterized queries instead of string concatenation',
      confidence: 0.85,
      agent: 'Security Agent'
    },
    {
      type: 'Performance',
      description: 'Inefficient loop structure',
      location: 'Line 25-30',
      severity: 'Medium',
      suggestion: 'Consider using list comprehension for better performance',
      confidence: 0.72,
      agent: 'Performance Agent'
    }
  ],
  summary: {
    total_findings: 2,
    by_severity: { High: 1, Medium: 1 },
    by_agent: { 'Security Agent': 1, 'Performance Agent': 1 },
    overall_score: 7.5,
    review_timestamp: new Date().toISOString()
  },
  recommendations: [
    {
      category: 'Security',
      priority: 'High',
      action: 'Implement input validation',
      impact: 'Prevents data breaches',
      effort: 'Medium'
    }
  ]
})

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
  recommendations: Array<{
    category: string
    priority: string
    action: string
    impact: string
    effort: string
  }>
}

interface QAResponse {
  status: string
  question: string
  answer: {
    agent: string
    answer: string
    tools_used: string[]
    confidence: number
  }
}

export function useCodeReview() {
  const [isReviewing, setIsReviewing] = useState(false)
  const [reviewData, setReviewData] = useState<ReviewData | null>(null)
  const [error, setError] = useState<string | null>(null)

  const reviewCode = useCallback(async (code: string, language: string, filename?: string) => {
    setIsReviewing(true)
    setError(null)
    
    try {
      const response = await axios.post(`${API_BASE_URL}/review`, {
        code,
        language,
        context: filename ? { filename } : undefined
      })
      
      if (response.data.status === 'success') {
        // Transform the simple backend response to match the expected frontend format
        const transformedData = {
          thread_id: 'simple-review-' + Date.now(),
          findings: [
            {
              type: 'AI Review',
              description: response.data.review,
              location: 'Full code analysis',
              severity: 'Info',
              suggestion: 'See detailed review above',
              confidence: 0.9,
              agent: 'Azure OpenAI ' + response.data.model_used
            }
          ],
          summary: {
            total_findings: 1,
            by_severity: { Info: 1 },
            by_agent: { ['Azure OpenAI ' + response.data.model_used]: 1 },
            overall_score: 8.0,
            review_timestamp: response.data.timestamp
          },
          recommendations: [
            {
              category: 'General',
              priority: 'Medium',
              action: 'Review the AI feedback',
              impact: 'Code quality improvement',
              effort: 'Low'
            }
          ]
        }
        setReviewData(transformedData)
      } else {
        throw new Error(response.data.message || 'Review failed')
      }
    } catch (err: any) {
      let errorMessage = 'Review failed'
      
      if (err.code === 'ECONNREFUSED' || err.message?.includes('ECONNREFUSED')) {
        errorMessage = 'Backend service is not running. Please ensure the API server is started on port 8000.'
      } else if (err.code === 'ERR_NETWORK' || err.message?.includes('Network Error')) {
        errorMessage = 'Network connection failed. Please check if the backend service is running.'
      } else if (err.response?.status === 404) {
        errorMessage = 'Review endpoint not found. Please check the API configuration.'
      } else if (err.response?.status >= 500) {
        errorMessage = 'Internal server error. Please try again later.'
      } else if (err.response?.data?.detail) {
        errorMessage = err.response.data.detail
      } else if (err.message) {
        errorMessage = err.message
      }
      
      setError(errorMessage)
      throw new Error(errorMessage)
    } finally {
      setIsReviewing(false)
    }
  }, [])

  const reviewGitHubPR = useCallback(async (
    owner: string, 
    repo: string, 
    prNumber: number, 
    token?: string
  ) => {
    setIsReviewing(true)
    setError(null)
    
    try {
      const response = await axios.post(`${API_BASE_URL}/review/github-pr`, {
        owner,
        repo,
        pr_number: prNumber,
        github_token: token
      })
      
      if (response.data.status === 'success') {
        setReviewData(response.data.review)
      } else {
        throw new Error(response.data.message || 'GitHub PR review failed')
      }
    } catch (err: any) {
      let errorMessage = 'GitHub PR review failed'
      
      if (err.code === 'ECONNREFUSED' || err.message?.includes('ECONNREFUSED')) {
        errorMessage = 'Backend service is not running. Please ensure the API server is started on port 8000.'
      } else if (err.code === 'ERR_NETWORK' || err.message?.includes('Network Error')) {
        errorMessage = 'Network connection failed. Please check if the backend service is running.'
      } else if (err.response?.status === 404) {
        errorMessage = 'GitHub PR review endpoint not found. Please check the API configuration.'
      } else if (err.response?.status === 401) {
        errorMessage = 'GitHub authentication failed. Please check your token.'
      } else if (err.response?.status >= 500) {
        errorMessage = 'Internal server error. Please try again later.'
      } else if (err.response?.data?.detail) {
        errorMessage = err.response.data.detail
      } else if (err.message) {
        errorMessage = err.message
      }
      
      setError(errorMessage)
      throw new Error(errorMessage)
    } finally {
      setIsReviewing(false)
    }
  }, [])

  const askQuestion = useCallback(async (threadId: string, question: string): Promise<QAResponse> => {
    try {
      const response = await axios.post(`${API_BASE_URL}/ask`, {
        thread_id: threadId,
        question
      })
      
      return response.data
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || err.message || 'Question failed'
      throw new Error(errorMessage)
    }
  }, [])

  return {
    isReviewing,
    reviewData,
    error,
    reviewCode,
    reviewGitHubPR,
    askQuestion
  }
}