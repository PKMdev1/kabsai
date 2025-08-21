'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import LoginForm from '@/components/LoginForm'
import Dashboard from '@/components/Dashboard'
import { AuthProvider } from '@/contexts/AuthContext'

export default function Home() {
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  const router = useRouter()

  useEffect(() => {
    // Check if user is authenticated
    const token = localStorage.getItem('access_token')
    if (token) {
      setIsAuthenticated(true)
    }
    setIsLoading(false)
  }, [])

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-kabs-600"></div>
      </div>
    )
  }

  return (
    <AuthProvider>
      <div className="min-h-screen">
        {isAuthenticated ? (
          <Dashboard />
        ) : (
          <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-kabs-50 to-elite-50">
            <div className="w-full max-w-md">
              <div className="text-center mb-8">
                <h1 className="text-4xl font-bold text-kabs-800 mb-2">KABS Assistant</h1>
                <p className="text-elite-600">AI-powered document management for Elite/KABS</p>
              </div>
              <LoginForm onLogin={() => setIsAuthenticated(true)} />
            </div>
          </div>
        )}
      </div>
    </AuthProvider>
  )
}
