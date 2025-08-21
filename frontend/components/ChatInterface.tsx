'use client'

import { useState, useEffect, useRef } from 'react'
import { Send, Bot, User } from 'lucide-react'
import axios from 'axios'
import toast from 'react-hot-toast'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

interface Message {
  id: number
  content: string
  message_type: 'user' | 'assistant'
  created_at: string
  context_files?: number[]
  context_chunks?: number[]
  tokens_used?: number
  model_used?: string
  response_time?: number
}

export default function ChatInterface() {
  const [messages, setMessages] = useState<Message[]>([])
  const [inputMessage, setInputMessage] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [sessionId, setSessionId] = useState<string | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const sendMessage = async () => {
    if (!inputMessage.trim() || isLoading) return

    const userMessage = {
      id: Date.now(),
      content: inputMessage,
      message_type: 'user' as const,
      created_at: new Date().toISOString(),
    }

    setMessages(prev => [...prev, userMessage])
    setInputMessage('')
    setIsLoading(true)

    try {
      const response = await axios.post('/api/v1/chat/', {
        message: inputMessage,
        session_id: sessionId,
      })

      const assistantMessage: Message = {
        id: response.data.session_id + Date.now(),
        content: response.data.response,
        message_type: 'assistant',
        created_at: new Date().toISOString(),
        context_files: response.data.context_files,
        context_chunks: response.data.context_chunks,
        tokens_used: response.data.tokens_used,
        model_used: response.data.model_used,
        response_time: response.data.response_time,
      }

      setSessionId(response.data.session_id)
      setMessages(prev => [...prev, assistantMessage])
    } catch (error) {
      console.error('Error sending message:', error)
      toast.error('Failed to send message. Please try again.')
      
      // Remove the user message if the request failed
      setMessages(prev => prev.filter(msg => msg.id !== userMessage.id))
    } finally {
      setIsLoading(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  const formatTime = (timestamp: string) => {
    return new Date(timestamp).toLocaleTimeString([], { 
      hour: '2-digit', 
      minute: '2-digit' 
    })
  }

  return (
    <div className="flex flex-col h-full bg-white">
      {/* Chat Header */}
      <div className="border-b border-elite-200 px-6 py-4">
        <div className="flex items-center space-x-3">
          <div className="w-8 h-8 bg-kabs-600 rounded-lg flex items-center justify-center">
            <Bot className="w-5 h-5 text-white" />
          </div>
          <div>
            <h2 className="text-lg font-semibold text-elite-900">KABS AI Assistant</h2>
            <p className="text-sm text-elite-600">Ask questions about your documents</p>
          </div>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-6 space-y-4">
        {messages.length === 0 && (
          <div className="text-center py-12">
            <div className="w-16 h-16 bg-kabs-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <Bot className="w-8 h-8 text-kabs-600" />
            </div>
            <h3 className="text-lg font-medium text-elite-900 mb-2">Welcome to KABS Assistant</h3>
            <p className="text-elite-600 max-w-md mx-auto">
              Upload documents to the Files section, then ask me questions about them. 
              I'll search through your documents and provide relevant answers.
            </p>
          </div>
        )}

        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex ${message.message_type === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-3xl rounded-lg p-4 ${
                message.message_type === 'user'
                  ? 'bg-kabs-600 text-white'
                  : 'bg-elite-50 border border-elite-200'
              }`}
            >
              <div className="flex items-start space-x-3">
                <div className={`w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0 ${
                  message.message_type === 'user' 
                    ? 'bg-kabs-500' 
                    : 'bg-kabs-100'
                }`}>
                  {message.message_type === 'user' ? (
                    <User className="w-3 h-3 text-white" />
                  ) : (
                    <Bot className="w-3 h-3 text-kabs-600" />
                  )}
                </div>
                
                <div className="flex-1">
                  <div className={`${
                    message.message_type === 'user' 
                      ? 'text-white' 
                      : 'text-elite-900'
                  }`}>
                    <ReactMarkdown 
                      remarkPlugins={[remarkGfm]}
                      className="prose prose-sm max-w-none"
                      components={{
                        p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
                        code: ({ children }) => (
                          <code className="bg-elite-200 px-1 py-0.5 rounded text-sm">
                            {children}
                          </code>
                        ),
                        pre: ({ children }) => (
                          <pre className="bg-elite-100 p-3 rounded-lg overflow-x-auto text-sm">
                            {children}
                          </pre>
                        ),
                      }}
                    >
                      {message.content}
                    </ReactMarkdown>
                  </div>
                  
                  {message.message_type === 'assistant' && message.context_files && message.context_files.length > 0 && (
                    <div className="mt-3 pt-3 border-t border-elite-200">
                      <p className="text-xs text-elite-600">
                        Sources: {message.context_files.length} document(s) referenced
                      </p>
                    </div>
                  )}
                  
                  <div className={`text-xs mt-2 ${
                    message.message_type === 'user' 
                      ? 'text-kabs-200' 
                      : 'text-elite-500'
                  }`}>
                    {formatTime(message.created_at)}
                    {message.message_type === 'assistant' && message.response_time && (
                      <span> • {message.response_time}ms</span>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </div>
        ))}

        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-elite-50 border border-elite-200 rounded-lg p-4 max-w-3xl">
              <div className="flex items-center space-x-3">
                <div className="w-6 h-6 bg-kabs-100 rounded-full flex items-center justify-center">
                  <Bot className="w-3 h-3 text-kabs-600" />
                </div>
                <div className="flex space-x-1">
                  <div className="w-2 h-2 bg-kabs-400 rounded-full animate-bounce"></div>
                  <div className="w-2 h-2 bg-kabs-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                  <div className="w-2 h-2 bg-kabs-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                </div>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="border-t border-elite-200 p-6">
        <div className="flex space-x-4">
          <div className="flex-1">
            <textarea
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Ask a question about your documents..."
              className="w-full px-4 py-3 border border-elite-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-kabs-500 focus:border-transparent resize-none"
              rows={1}
              disabled={isLoading}
            />
          </div>
          <button
            onClick={sendMessage}
            disabled={!inputMessage.trim() || isLoading}
            className="px-6 py-3 bg-kabs-600 text-white rounded-lg hover:bg-kabs-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <Send className="w-5 h-5" />
          </button>
        </div>
        <p className="text-xs text-elite-500 mt-2">
          Press Enter to send, Shift+Enter for new line
        </p>
      </div>
    </div>
  )
}
