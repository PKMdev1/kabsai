'use client'

import { useState } from 'react'
import FileUpload from '@/components/FileUpload'
import ChatInterface from '@/components/ChatInterface'
import FileList from '@/components/FileList'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'

export default function Home() {
  const [activeTab, setActiveTab] = useState('chat')

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-2">
            KABS Assistant
          </h1>
          <p className="text-lg text-gray-600 dark:text-gray-300">
            AI-powered document management and chat system
          </p>
        </div>

        {/* Main Content */}
        <div className="max-w-6xl mx-auto">
          <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
            <TabsList className="grid w-full grid-cols-3 mb-8">
              <TabsTrigger value="chat">Chat</TabsTrigger>
              <TabsTrigger value="files">Files</TabsTrigger>
              <TabsTrigger value="upload">Upload</TabsTrigger>
            </TabsList>

            <TabsContent value="chat" className="space-y-4">
              <ChatInterface />
            </TabsContent>

            <TabsContent value="files" className="space-y-4">
              <FileList />
            </TabsContent>

            <TabsContent value="upload" className="space-y-4">
              <FileUpload />
            </TabsContent>
          </Tabs>
        </div>
      </div>
    </div>
  )
}
