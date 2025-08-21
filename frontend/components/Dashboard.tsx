'use client'

import { useState } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import ChatInterface from './ChatInterface'
import FileManager from './FileManager'
import XMLProcessor from './XMLProcessor'
import Sidebar from './Sidebar'
import Header from './Header'

type TabType = 'chat' | 'files' | 'xml'

export default function Dashboard() {
  const [activeTab, setActiveTab] = useState<TabType>('chat')
  const { user, logout } = useAuth()

  const handleLogout = () => {
    logout()
    window.location.reload()
  }

  return (
    <div className="flex h-screen bg-elite-50">
      <Sidebar activeTab={activeTab} onTabChange={setActiveTab} />
      
      <div className="flex-1 flex flex-col">
        <Header user={user} onLogout={handleLogout} />
        
        <main className="flex-1 overflow-hidden">
          {activeTab === 'chat' && <ChatInterface />}
          {activeTab === 'files' && <FileManager />}
          {activeTab === 'xml' && <XMLProcessor />}
        </main>
      </div>
    </div>
  )
}
