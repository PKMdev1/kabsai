'use client'

import { MessageSquare, FolderOpen, Bot, FileText } from 'lucide-react'

type TabType = 'chat' | 'files' | 'xml'

interface SidebarProps {
  activeTab: TabType
  onTabChange: (tab: TabType) => void
}

export default function Sidebar({ activeTab, onTabChange }: SidebarProps) {
  const tabs = [
    {
      id: 'chat' as TabType,
      label: 'Chat',
      icon: MessageSquare,
      description: 'AI Assistant'
    },
    {
      id: 'files' as TabType,
      label: 'Files',
      icon: FolderOpen,
      description: 'Document Vault'
    },
    {
      id: 'xml' as TabType,
      label: 'XML',
      icon: FileText,
      description: 'XML Processor'
    }
  ]

  return (
    <aside className="w-64 bg-white dark:bg-gray-800 border-r border-elite-200 dark:border-gray-700 flex flex-col">
      <div className="p-6 border-b border-elite-200 dark:border-gray-700">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 bg-kabs-600 rounded-lg flex items-center justify-center">
            <Bot className="w-6 h-6 text-white" />
          </div>
          <div>
            <h2 className="text-lg font-semibold text-elite-900 dark:text-gray-100">KABS</h2>
            <p className="text-xs text-elite-600 dark:text-gray-400">Assistant</p>
          </div>
        </div>
      </div>

      <nav className="flex-1 p-4">
        <ul className="space-y-2">
          {tabs.map((tab) => {
            const Icon = tab.icon
            const isActive = activeTab === tab.id
            
            return (
              <li key={tab.id}>
                <button
                  onClick={() => onTabChange(tab.id)}
                  className={`w-full flex items-center space-x-3 px-4 py-3 rounded-lg text-left transition-colors ${
                    isActive
                      ? 'bg-kabs-50 dark:bg-kabs-900/30 text-kabs-700 dark:text-kabs-300 border border-kabs-200 dark:border-kabs-700'
                      : 'text-elite-600 dark:text-gray-400 hover:bg-elite-50 dark:hover:bg-gray-700 hover:text-elite-900 dark:hover:text-gray-100'
                  }`}
                >
                  <Icon className={`w-5 h-5 ${isActive ? 'text-kabs-600 dark:text-kabs-400' : 'text-elite-500 dark:text-gray-500'}`} />
                  <div>
                    <div className="font-medium">{tab.label}</div>
                    <div className="text-xs opacity-75">{tab.description}</div>
                  </div>
                </button>
              </li>
            )
          })}
        </ul>
      </nav>

      <div className="p-4 border-t border-elite-200 dark:border-gray-700">
        <div className="text-xs text-elite-500 dark:text-gray-500 text-center">
          <p>Elite/KABS Systems</p>
          <p>v1.0.0</p>
        </div>
      </div>
    </aside>
  )
}
