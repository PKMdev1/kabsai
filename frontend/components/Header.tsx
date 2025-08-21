'use client'

import { User, LogOut, Settings } from 'lucide-react'
import { ThemeToggle } from './ThemeToggle'

interface User {
  id: number
  username: string
  email: string
  full_name: string
  role: string
  is_admin: boolean
}

interface HeaderProps {
  user: User | null
  onLogout: () => void
}

export default function Header({ user, onLogout }: HeaderProps) {
  return (
    <header className="bg-white dark:bg-gray-800 border-b border-elite-200 dark:border-gray-700 px-6 py-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <div className="w-8 h-8 bg-kabs-600 rounded-lg flex items-center justify-center">
            <span className="text-white font-bold text-sm">K</span>
          </div>
          <div>
            <h1 className="text-xl font-semibold text-elite-900 dark:text-gray-100">KABS Assistant</h1>
            <p className="text-sm text-elite-600 dark:text-gray-400">AI-powered document management</p>
          </div>
        </div>

        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 bg-kabs-100 dark:bg-kabs-900/30 rounded-full flex items-center justify-center">
              <User className="w-4 h-4 text-kabs-600 dark:text-kabs-400" />
            </div>
            <div className="text-right">
              <p className="text-sm font-medium text-elite-900 dark:text-gray-100">{user?.full_name}</p>
              <p className="text-xs text-elite-600 dark:text-gray-400">{user?.role}</p>
            </div>
          </div>

          <ThemeToggle />

          <button
            onClick={onLogout}
            className="p-2 text-elite-600 dark:text-gray-400 hover:text-elite-900 dark:hover:text-gray-100 hover:bg-elite-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
            title="Logout"
          >
            <LogOut className="w-5 h-5" />
          </button>
        </div>
      </div>
    </header>
  )
}
