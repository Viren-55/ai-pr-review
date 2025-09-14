'use client'

import { useTheme } from '@/lib/ThemeContext'
import { Button } from 'react-bootstrap'
import { useEffect, useState } from 'react'

export default function ThemeToggle() {
  const [mounted, setMounted] = useState(false)
  
  useEffect(() => {
    setMounted(true)
  }, [])

  // Prevent hydration mismatch by not rendering until mounted
  if (!mounted) {
    return (
      <Button
        variant="outline-secondary"
        size="sm"
        disabled
        className="theme-toggle d-flex align-items-center gap-2"
        style={{
          background: 'transparent',
          border: '1px solid var(--border-color)',
          color: 'var(--text-secondary)',
          borderRadius: '0.5rem',
          padding: '0.5rem 0.75rem',
          transition: 'all 0.3s ease',
        }}
      >
        <i className="bi bi-moon-stars-fill" style={{ fontSize: '0.875rem' }}></i>
        <span className="d-none d-md-inline">Theme</span>
      </Button>
    )
  }

  const { theme, toggleTheme } = useTheme()

  return (
    <Button
      variant="outline-secondary"
      size="sm"
      onClick={toggleTheme}
      className="theme-toggle d-flex align-items-center gap-2"
      style={{
        background: 'transparent',
        border: '1px solid var(--border-color)',
        color: 'var(--text-secondary)',
        borderRadius: '0.5rem',
        padding: '0.5rem 0.75rem',
        transition: 'all 0.3s ease',
      }}
      title={`Switch to ${theme === 'light' ? 'dark' : 'light'} mode`}
    >
      {theme === 'light' ? (
        <>
          <i className="bi bi-moon-stars-fill" style={{ fontSize: '0.875rem' }}></i>
          <span className="d-none d-md-inline">Dark</span>
        </>
      ) : (
        <>
          <i className="bi bi-sun-fill" style={{ fontSize: '0.875rem' }}></i>
          <span className="d-none d-md-inline">Light</span>
        </>
      )}
    </Button>
  )
}