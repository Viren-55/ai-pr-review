'use client'

import 'bootstrap/dist/css/bootstrap.min.css'
import 'bootstrap-icons/font/bootstrap-icons.css'
import './globals.css'
import { Inter, JetBrains_Mono } from 'next/font/google'
import { Toaster } from 'react-hot-toast'
import { ThemeProvider } from '@/lib/ThemeContext'

const inter = Inter({ 
  subsets: ['latin'],
  display: 'swap',
  variable: '--font-inter',
  weight: ['300', '400', '500', '600', '700', '800', '900']
})

const jetbrainsMono = JetBrains_Mono({
  subsets: ['latin'],
  display: 'swap',
  variable: '--font-mono'
})

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className={`${inter.variable} ${jetbrainsMono.variable}`}>
      <head>
        <title>AI Code Review - Premium AI-Powered Code Analysis</title>
        <meta name="description" content="Transform your code quality with our premium AI-powered review system. 5 specialized AI agents provide comprehensive analysis on security, performance, and best practices." />
        <meta name="keywords" content="AI code review, code analysis, automated code review, code quality, static analysis, security scan, performance optimization" />
        <meta name="author" content="AI Code Review" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        
        {/* Open Graph / Facebook */}
        <meta property="og:type" content="website" />
        <meta property="og:title" content="AI Code Review - Premium AI-Powered Code Analysis" />
        <meta property="og:description" content="Transform your code quality with our premium AI-powered review system. 5 specialized AI agents provide comprehensive analysis." />
        <meta property="og:image" content="/og-image.png" />
        
        {/* Twitter */}
        <meta name="twitter:card" content="summary_large_image" />
        <meta name="twitter:title" content="AI Code Review - Premium AI-Powered Code Analysis" />
        <meta name="twitter:description" content="Transform your code quality with our premium AI-powered review system." />
        <meta name="twitter:image" content="/twitter-image.png" />
        
        {/* Theme and Dark Mode Support */}
        <meta name="theme-color" content="#0A0A0B" />
        <meta name="color-scheme" content="dark light" />
        
        {/* Favicons */}
        <link rel="icon" type="image/svg+xml" href="/favicon.svg" />
        <link rel="icon" type="image/png" href="/favicon.png" />
        
        {/* Preload Critical Resources */}
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        
        {/* Performance and SEO */}
        <link rel="canonical" href="https://ai-code-review.com" />
      </head>
      <body className={`${inter.className} antialiased`}>
        <ThemeProvider>
          <div id="app-root" className="min-vh-100">
            {children}
          </div>
        </ThemeProvider>
        
        <Toaster 
          position="top-right"
          toastOptions={{
            duration: 5000,
            style: {
              background: 'rgba(26, 26, 28, 0.95)',
              color: '#FFFFFF',
              border: '1px solid rgba(255, 255, 255, 0.12)',
              borderRadius: '1rem',
              padding: '16px 20px',
              fontSize: '14px',
              fontWeight: '600',
              backdropFilter: 'blur(20px)',
              boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.8), 0 8px 32px 0 rgba(0, 0, 0, 0.37)',
            },
            success: {
              iconTheme: {
                primary: '#10B981',
                secondary: '#FFFFFF',
              },
              style: {
                border: '1px solid rgba(16, 185, 129, 0.3)',
              }
            },
            error: {
              iconTheme: {
                primary: '#EF4444',
                secondary: '#FFFFFF',
              },
              style: {
                border: '1px solid rgba(239, 68, 68, 0.3)',
              }
            },
            loading: {
              iconTheme: {
                primary: '#0EA5E9',
                secondary: '#FFFFFF',
              },
              style: {
                border: '1px solid rgba(14, 165, 233, 0.3)',
              }
            }
          }}
        />
      </body>
    </html>
  )
}