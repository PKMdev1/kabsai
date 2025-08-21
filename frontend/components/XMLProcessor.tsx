'use client'

import React, { useState, useEffect } from 'react'
import { Upload, Search, FileText, Database, CheckCircle, AlertCircle } from 'lucide-react'
import axios from 'axios'

interface XMLFile {
  id: number
  filename: string
  title: string
  description: string
  root_element: string
  element_count: number
  upload_date: string
  tags: string
  project: string
  department: string
}

interface XMLMatch {
  file_id: number
  filename: string
  title: string
  matched_element: any
  relevance_score: number
}

interface XMLSchema {
  file_id: number
  filename: string
  schema: any
}

export default function XMLProcessor() {
  const [xmlFiles, setXmlFiles] = useState<XMLFile[]>([])
  const [selectedFile, setSelectedFile] = useState<XMLFile | null>(null)
  const [searchResults, setSearchResults] = useState<XMLMatch[]>([])
  const [schema, setSchema] = useState<XMLSchema | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [activeTab, setActiveTab] = useState<'files' | 'search' | 'schema' | 'upload'>('files')

  // Search criteria
  const [searchCriteria, setSearchCriteria] = useState({
    tag: '',
    attributes: {},
    text: '',
    value: ''
  })

  // Upload form
  const [uploadForm, setUploadForm] = useState({
    title: '',
    description: '',
    tags: '',
    project: '',
    department: ''
  })

  useEffect(() => {
    loadXMLFiles()
  }, [])

  const loadXMLFiles = async () => {
    try {
      const response = await axios.get('/api/v1/xml/files')
      setXmlFiles(response.data)
    } catch (error) {
      console.error('Error loading XML files:', error)
    }
  }

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    if (!file.name.toLowerCase().endsWith('.xml')) {
      alert('Please select an XML file')
      return
    }

    setIsLoading(true)
    const formData = new FormData()
    formData.append('file', file)
    formData.append('title', uploadForm.title || file.name)
    formData.append('description', uploadForm.description)
    formData.append('tags', uploadForm.tags)
    formData.append('project', uploadForm.project)
    formData.append('department', uploadForm.department)

    try {
      const response = await axios.post('/api/v1/xml/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      })

      if (response.data.success) {
        alert('XML file uploaded and processed successfully!')
        loadXMLFiles()
        setUploadForm({
          title: '',
          description: '',
          tags: '',
          project: '',
          department: ''
        })
      }
    } catch (error) {
      console.error('Error uploading XML file:', error)
      alert('Error uploading XML file')
    } finally {
      setIsLoading(false)
    }
  }

  const handleSearch = async () => {
    if (!searchCriteria.tag && !searchCriteria.text && !searchCriteria.value && Object.keys(searchCriteria.attributes).length === 0) {
      alert('Please enter at least one search criteria')
      return
    }

    setIsLoading(true)
    try {
      const response = await axios.post('/api/v1/xml/search', {
        search_criteria: searchCriteria
      })
      setSearchResults(response.data)
    } catch (error) {
      console.error('Error searching XML data:', error)
      alert('Error searching XML data')
    } finally {
      setIsLoading(false)
    }
  }

  const loadSchema = async (fileId: number) => {
    try {
      const response = await axios.get(`/api/v1/xml/schema/${fileId}`)
      setSchema(response.data)
    } catch (error) {
      console.error('Error loading schema:', error)
    }
  }

  const renderSearchResults = () => {
    if (searchResults.length === 0) {
      return (
        <div className="text-center py-8 text-gray-500">
          <Search className="w-12 h-12 mx-auto mb-4 text-gray-400" />
          <p>No matches found</p>
        </div>
      )
    }

    return (
      <div className="space-y-4">
        {searchResults.map((match, index) => (
          <div key={index} className="card">
            <div className="flex items-center justify-between mb-2">
              <h3 className="font-semibold text-kabs-600 dark:text-kabs-400">{match.title}</h3>
              <span className="text-sm bg-kabs-100 dark:bg-kabs-900/30 text-kabs-700 dark:text-kabs-300 px-2 py-1 rounded">
                Score: {match.relevance_score.toFixed(2)}
              </span>
            </div>
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">{match.filename}</p>
            <div className="bg-gray-50 dark:bg-gray-800 p-3 rounded border">
              <pre className="text-xs overflow-x-auto">
                {JSON.stringify(match.matched_element, null, 2)}
              </pre>
            </div>
          </div>
        ))}
      </div>
    )
  }

  const renderSchema = () => {
    if (!schema) {
      return (
        <div className="text-center py-8 text-gray-500">
          <Database className="w-12 h-12 mx-auto mb-4 text-gray-400" />
          <p>Select a file to view its schema</p>
        </div>
      )
    }

    return (
      <div className="space-y-4">
        <div className="card">
          <h3 className="font-semibold text-kabs-600 dark:text-kabs-400 mb-4">Schema for {schema.filename}</h3>
          <div className="bg-gray-50 dark:bg-gray-800 p-4 rounded border">
            <pre className="text-xs overflow-x-auto">
              {JSON.stringify(schema.schema, null, 2)}
            </pre>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="h-full flex flex-col">
      {/* Tabs */}
      <div className="flex border-b border-gray-200 dark:border-gray-700 mb-6">
        <button
          onClick={() => setActiveTab('files')}
          className={`px-4 py-2 font-medium ${
            activeTab === 'files'
              ? 'text-kabs-600 dark:text-kabs-400 border-b-2 border-kabs-600 dark:border-kabs-400'
              : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
          }`}
        >
          <FileText className="w-4 h-4 inline mr-2" />
          XML Files
        </button>
        <button
          onClick={() => setActiveTab('search')}
          className={`px-4 py-2 font-medium ${
            activeTab === 'search'
              ? 'text-kabs-600 dark:text-kabs-400 border-b-2 border-kabs-600 dark:border-kabs-400'
              : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
          }`}
        >
          <Search className="w-4 h-4 inline mr-2" />
          Data Search
        </button>
        <button
          onClick={() => setActiveTab('schema')}
          className={`px-4 py-2 font-medium ${
            activeTab === 'schema'
              ? 'text-kabs-600 dark:text-kabs-400 border-b-2 border-kabs-600 dark:border-kabs-400'
              : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
          }`}
        >
          <Database className="w-4 h-4 inline mr-2" />
          Schema Viewer
        </button>
        <button
          onClick={() => setActiveTab('upload')}
          className={`px-4 py-2 font-medium ${
            activeTab === 'upload'
              ? 'text-kabs-600 dark:text-kabs-400 border-b-2 border-kabs-600 dark:border-kabs-400'
              : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
          }`}
        >
          <Upload className="w-4 h-4 inline mr-2" />
          Upload XML
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-auto">
        {activeTab === 'files' && (
          <div className="space-y-4">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100">XML Files</h2>
            {xmlFiles.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <FileText className="w-12 h-12 mx-auto mb-4 text-gray-400" />
                <p>No XML files uploaded yet</p>
              </div>
            ) : (
              <div className="grid gap-4">
                {xmlFiles.map((file) => (
                  <div key={file.id} className="card hover:shadow-md transition-shadow cursor-pointer" onClick={() => setSelectedFile(file)}>
                    <div className="flex items-center justify-between">
                      <div>
                        <h3 className="font-semibold text-gray-900 dark:text-gray-100">{file.title}</h3>
                        <p className="text-sm text-gray-600 dark:text-gray-400">{file.filename}</p>
                        <div className="flex items-center space-x-4 mt-2 text-xs text-gray-500 dark:text-gray-400">
                          <span>Root: {file.root_element}</span>
                          <span>Elements: {file.element_count}</span>
                          <span>Uploaded: {new Date(file.upload_date).toLocaleDateString()}</span>
                        </div>
                      </div>
                      <CheckCircle className="w-5 h-5 text-green-500" />
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {activeTab === 'search' && (
          <div className="space-y-6">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100">XML Data Search</h2>
            
            {/* Search Form */}
            <div className="card">
              <h3 className="font-semibold mb-4">Search Criteria</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Element Tag
                  </label>
                  <input
                    type="text"
                    value={searchCriteria.tag}
                    onChange={(e) => setSearchCriteria({ ...searchCriteria, tag: e.target.value })}
                    className="input-field"
                    placeholder="e.g., user, product, order"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Text Content
                  </label>
                  <input
                    type="text"
                    value={searchCriteria.text}
                    onChange={(e) => setSearchCriteria({ ...searchCriteria, text: e.target.value })}
                    className="input-field"
                    placeholder="Search in text content"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Element Value
                  </label>
                  <input
                    type="text"
                    value={searchCriteria.value}
                    onChange={(e) => setSearchCriteria({ ...searchCriteria, value: e.target.value })}
                    className="input-field"
                    placeholder="Search in element values"
                  />
                </div>
                <div className="flex items-end">
                  <button
                    onClick={handleSearch}
                    disabled={isLoading}
                    className="btn-primary w-full"
                  >
                    {isLoading ? 'Searching...' : 'Search XML Data'}
                  </button>
                </div>
              </div>
            </div>

            {/* Search Results */}
            <div>
              <h3 className="font-semibold mb-4">Search Results ({searchResults.length})</h3>
              {renderSearchResults()}
            </div>
          </div>
        )}

        {activeTab === 'schema' && (
          <div className="space-y-6">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100">XML Schema Viewer</h2>
            
            {/* File Selection */}
            <div className="card">
              <h3 className="font-semibold mb-4">Select XML File</h3>
              <select
                onChange={(e) => {
                  const file = xmlFiles.find(f => f.id === parseInt(e.target.value))
                  setSelectedFile(file || null)
                  if (file) loadSchema(file.id)
                }}
                className="input-field"
                value={selectedFile?.id || ''}
              >
                <option value="">Choose an XML file...</option>
                {xmlFiles.map((file) => (
                  <option key={file.id} value={file.id}>
                    {file.title} ({file.filename})
                  </option>
                ))}
              </select>
            </div>

            {/* Schema Display */}
            {renderSchema()}
          </div>
        )}

        {activeTab === 'upload' && (
          <div className="space-y-6">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100">Upload XML File</h2>
            
            <div className="card">
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    XML File
                  </label>
                  <input
                    type="file"
                    accept=".xml,.xsd"
                    onChange={handleFileUpload}
                    className="input-field"
                    disabled={isLoading}
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Title
                  </label>
                  <input
                    type="text"
                    value={uploadForm.title}
                    onChange={(e) => setUploadForm({ ...uploadForm, title: e.target.value })}
                    className="input-field"
                    placeholder="Enter file title"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Description
                  </label>
                  <textarea
                    value={uploadForm.description}
                    onChange={(e) => setUploadForm({ ...uploadForm, description: e.target.value })}
                    className="input-field"
                    rows={3}
                    placeholder="Enter file description"
                  />
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Tags
                    </label>
                    <input
                      type="text"
                      value={uploadForm.tags}
                      onChange={(e) => setUploadForm({ ...uploadForm, tags: e.target.value })}
                      className="input-field"
                      placeholder="comma-separated tags"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Project
                    </label>
                    <input
                      type="text"
                      value={uploadForm.project}
                      onChange={(e) => setUploadForm({ ...uploadForm, project: e.target.value })}
                      className="input-field"
                      placeholder="Project name"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Department
                    </label>
                    <input
                      type="text"
                      value={uploadForm.department}
                      onChange={(e) => setUploadForm({ ...uploadForm, department: e.target.value })}
                      className="input-field"
                      placeholder="Department"
                    />
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
