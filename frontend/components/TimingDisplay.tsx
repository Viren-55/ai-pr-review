'use client'

import React from 'react'
import { Card, ProgressBar } from 'react-bootstrap'

interface TimingData {
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

interface TimingDisplayProps {
  timing?: TimingData
}

export default function TimingDisplay({ timing }: TimingDisplayProps) {
  if (!timing) return null

  const parseTime = (timeStr: string): number => {
    if (timeStr === '< 1ms' || timeStr === 'N/A') return 0
    const match = timeStr.match(/([\d.]+)ms/)
    return match ? parseFloat(match[1]) : 0
  }

  const validationTime = parseTime(timing.steps.validation)
  const dbSubmissionTime = parseTime(timing.steps.database_submission)
  const aiAnalysisTime = parseTime(timing.steps.ai_analysis)
  const dbStorageTime = parseTime(timing.steps.database_storage)

  const totalMeasured = validationTime + dbSubmissionTime + aiAnalysisTime + dbStorageTime
  const actualTotal = timing.total_time_ms

  // Calculate percentages based on actual total
  const getPercentage = (time: number) => (time / actualTotal) * 100

  return (
    <Card className="border-0 shadow-sm mb-4">
      <Card.Body>
        <div className="d-flex align-items-center justify-content-between mb-3">
          <h6 className="mb-0 fw-semibold">
            <i className="bi bi-speedometer2 me-2 text-primary"></i>
            Performance Metrics
          </h6>
          <span className="badge bg-success-subtle text-success">
            {timing.total_time_seconds}s total
          </span>
        </div>

        {/* Overall Progress */}
        <div className="mb-3">
          <div className="d-flex justify-content-between align-items-center mb-2">
            <small className="text-muted">Total Analysis Time</small>
            <small className="fw-semibold">{timing.total_time_ms.toFixed(0)}ms</small>
          </div>
          <ProgressBar style={{ height: '8px' }}>
            <ProgressBar 
              variant="info" 
              now={getPercentage(validationTime)} 
              key={1}
              style={{ backgroundColor: '#3b82f6' }}
            />
            <ProgressBar 
              variant="primary" 
              now={getPercentage(dbSubmissionTime)} 
              key={2}
              style={{ backgroundColor: '#8b5cf6' }}
            />
            <ProgressBar 
              variant="warning" 
              now={getPercentage(aiAnalysisTime)} 
              key={3}
              style={{ backgroundColor: '#f59e0b' }}
            />
            <ProgressBar 
              variant="success" 
              now={getPercentage(dbStorageTime)} 
              key={4}
              style={{ backgroundColor: '#10b981' }}
            />
          </ProgressBar>
        </div>

        {/* Step Breakdown */}
        <div className="small">
          <div className="d-flex align-items-center justify-content-between py-2 border-bottom">
            <div className="d-flex align-items-center">
              <div style={{ 
                width: '12px', 
                height: '12px', 
                backgroundColor: '#3b82f6', 
                borderRadius: '2px',
                marginRight: '8px'
              }}></div>
              <span className="text-muted">Validation</span>
            </div>
            <span className="fw-medium">{timing.steps.validation}</span>
          </div>

          <div className="d-flex align-items-center justify-content-between py-2 border-bottom">
            <div className="d-flex align-items-center">
              <div style={{ 
                width: '12px', 
                height: '12px', 
                backgroundColor: '#8b5cf6', 
                borderRadius: '2px',
                marginRight: '8px'
              }}></div>
              <span className="text-muted">Database Storage</span>
            </div>
            <span className="fw-medium">{timing.steps.database_submission}</span>
          </div>

          <div className="d-flex align-items-center justify-content-between py-2 border-bottom">
            <div className="d-flex align-items-center">
              <div style={{ 
                width: '12px', 
                height: '12px', 
                backgroundColor: '#f59e0b', 
                borderRadius: '2px',
                marginRight: '8px'
              }}></div>
              <span className="text-muted">AI Analysis</span>
            </div>
            <span className="fw-medium text-warning">{timing.steps.ai_analysis}</span>
          </div>

          <div className="d-flex align-items-center justify-content-between py-2">
            <div className="d-flex align-items-center">
              <div style={{ 
                width: '12px', 
                height: '12px', 
                backgroundColor: '#10b981', 
                borderRadius: '2px',
                marginRight: '8px'
              }}></div>
              <span className="text-muted">Results Storage</span>
            </div>
            <span className="fw-medium">{timing.steps.database_storage}</span>
          </div>
        </div>

        {/* Additional Stats */}
        <div className="mt-3 pt-3 border-top">
          <div className="row text-center small">
            <div className="col-6">
              <div className="text-muted mb-1">AI Agents</div>
              <div className="fw-semibold text-primary">{timing.agents_used}</div>
            </div>
            <div className="col-6">
              <div className="text-muted mb-1">Issues Found</div>
              <div className="fw-semibold text-danger">{timing.issues_found}</div>
            </div>
          </div>
        </div>
      </Card.Body>
    </Card>
  )
}