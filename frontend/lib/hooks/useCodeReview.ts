'use client'

import { useState, useCallback } from 'react'
import axios from 'axios'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
const IS_DEVELOPMENT = process.env.NODE_ENV === 'development'

// Mock data for development when backend is not available
const getMockReviewData = (): ReviewData => ({
  thread_id: 'mock-thread-123',
  analysis: {
    issues: [
      {
        id: 1,
        title: 'Potential SQL injection vulnerability',
        description: 'String concatenation in SQL query allows injection attacks',
        severity: 'high',
        category: 'security',
        line_number: 15,
        code_snippet: 'SELECT * FROM users WHERE id = \' + user_id',
        suggested_fix: 'Use parameterized queries instead',
        fix_explanation: 'Use parameterized queries to prevent SQL injection'
      },
      {
        id: 2,
        title: 'Inefficient loop structure',
        description: 'Nested loops result in O(n^2) complexity',
        severity: 'medium',
        category: 'performance',
        line_number: 25,
        code_snippet: 'for i in items: for j in items:',
        suggested_fix: 'Use set for lookups',
        fix_explanation: 'Consider using list comprehension for better performance'
      }
    ],
    overall_score: 75,
    analysis_summary: 'Found 2 issues: 1 high severity security issue and 1 medium severity performance issue.',
    files_analyzed: 1,
    total_lines_analyzed: 50
  },
  timestamp: new Date().toISOString(),
  model_used: 'Mock Data',
  filename: 'Mock File',
  language: 'python',
  original_code: 'mock code here'
})

// ReviewData interface now matches what ReviewResultsPage expects
interface ReviewData {
  analysis: {
    issues: Array<{
      id: number
      title: string
      description: string
      severity: string
      category: string
      line_number?: number | null
      code_snippet?: string
      suggested_fix?: string
      fix_explanation?: string
      file_path?: string
    }>
    overall_score: number
    analysis_summary: string
    files_analyzed: number
    total_lines_analyzed: number
  }
  timestamp: string
  model_used: string
  filename?: string
  language?: string
  original_code?: string
  thread_id: string
  submission_id?: number
  demo_mode?: boolean
  // For GitHub PR specific data
  pr_info?: any
  changes_summary?: any
  metadata?: any
  // Timing information
  timing?: {
    total_time_ms: number
    total_time_seconds: number
    steps: {
      validation: string
      database_submission: string
      ai_analysis: string
      database_storage: string
    }
    agents_used: number
    issues_found: number
  }
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
      // Use the structured API endpoint instead of legacy /review
      const response = await axios.post(`${API_BASE_URL}/api/submissions`, {
        code,
        language,
        filename: filename || undefined
      })
      
      // The structured API returns data in the correct format already
      if (response.data && response.data.analysis) {
        const submissionData = response.data
        
        // Transform to ReviewResultsPage expected format
        const transformedData = {
          analysis: {
            issues: submissionData.analysis.issues || [],
            overall_score: submissionData.analysis.overall_score || 0,
            analysis_summary: submissionData.analysis.analysis_summary || '',
            files_analyzed: 1,
            total_lines_analyzed: code.split('\n').length
          },
          timestamp: submissionData.created_at || new Date().toISOString(),
          model_used: submissionData.analysis.model_used || 'Azure OpenAI',
          filename: filename || 'Submitted Code',
          language: language,
          original_code: code,
          thread_id: 'code-review-' + Date.now(),
          submission_id: submissionData.id,
          timing: submissionData.timing || undefined
        }
        setReviewData(transformedData as any)
      } else {
        throw new Error('Invalid response format from API')
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
    prUrl: string, 
    language: string = 'javascript'
  ) => {
    setIsReviewing(true)
    setError(null)
    
    try {
      const response = await axios.post(`${API_BASE_URL}/review/github-pr`, {
        pr_url: prUrl,
        language: language
      })
      
      if (response.data.status === 'success') {
        // Pass the raw analysis data directly to ReviewResultsPage
        // ReviewResultsPage expects analysis.issues structure
        const analysisData = response.data.analysis
        
        // Extract actual code content for display in the middle pane
        const codeContent = analysisData.code_content
        let displayCode = ''
        
        if (codeContent?.file_contents && Object.keys(codeContent.file_contents).length > 0) {
          // Use full file contents (best for complete code review)
          const files = codeContent.file_contents
          displayCode = Object.entries(files).map(([filename, content]) => 
            `=== ${filename} ===\n${content}`
          ).join('\n\n')
        } else if (codeContent?.formatted_diff) {
          // Use formatted diff (good for showing changes)
          displayCode = codeContent.formatted_diff
        } else if (codeContent?.diff) {
          // Fallback to raw diff content
          displayCode = codeContent.diff
        } else if (codeContent?.extracted_code) {
          // Use extracted code (clean, analyzable content)
          displayCode = codeContent.extracted_code
        } else {
          // Final fallback - show file list
          const fileList = analysisData.changes_summary?.changed_files || []
          displayCode = `GitHub PR: ${analysisData.pr_info?.title || prUrl}\n\nChanged files:\n${fileList.map(f => `- ${f}`).join('\n')}`
        }
        
        // Transform to the format ReviewResultsPage expects
        const transformedData = {
          analysis: {
            issues: analysisData.analysis.issues.map((issue: any, index: number) => ({
              id: index + 1,
              title: issue.title,
              description: issue.description,
              severity: issue.severity,
              category: issue.category,
              line_number: issue.line_number,
              code_snippet: issue.code_snippet,
              suggested_fix: issue.suggested_fix,
              fix_explanation: issue.fix_explanation || issue.suggestion,
              file_path: issue.file_path
            })),
            overall_score: analysisData.analysis.overall_score,
            analysis_summary: analysisData.analysis.analysis_summary,
            files_analyzed: analysisData.analysis.files_analyzed,
            total_lines_analyzed: analysisData.analysis.total_lines_analyzed
          },
          pr_info: analysisData.pr_info,
          changes_summary: analysisData.changes_summary,
          code_content: codeContent,
          metadata: analysisData.metadata,
          timestamp: response.data.timestamp,
          demo_mode: response.data.demo_mode,
          model_used: response.data.demo_mode ? 'Demo Mode' : 'Azure OpenAI',
          // Add additional fields for compatibility
          filename: analysisData.pr_info?.title || 'GitHub PR',
          language: language,
          original_code: displayCode,  // Use actual code content instead of just the URL
          thread_id: `pr-review-${analysisData.pr_info.pr_number}-${Date.now()}`
        }
        
        setReviewData(transformedData as any)
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