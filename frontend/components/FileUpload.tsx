'use client'

import { useState } from 'react'
import { useDropzone } from 'react-dropzone'
import toast from 'react-hot-toast'
import axios from 'axios'

export default function FileUpload() {
  const [isUploading, setIsUploading] = useState(false)

  const onDrop = async (acceptedFiles: File[]) => {
    if (acceptedFiles.length === 0) return

    setIsUploading(true)
    
    try {
      const formData = new FormData()
      
      for (const file of acceptedFiles) {
        formData.append('files', file)
      }

      const response = await axios.post('/api/v1/files/upload-multiple', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      })

      if (response.status === 200) {
        toast.success(`Successfully uploaded ${acceptedFiles.length} file(s)`)
      }
    } catch (error: any) {
      console.error('Upload error:', error)
      toast.error('Upload failed. Please try again.')
    } finally {
      setIsUploading(false)
    }
  }

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
      'text/plain': ['.txt'],
      'text/csv': ['.csv'],
      'application/json': ['.json'],
      'text/markdown': ['.md'],
      'text/html': ['.html'],
      'application/xml': ['.xml'],
      'text/xml': ['.xml'],
    },
    multiple: true,
  })

  return (
    <div className="card">
      <div className="text-center mb-6">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
          Upload Files
        </h2>
        <p className="text-gray-600 dark:text-gray-300">
          Upload documents to analyze with AI
        </p>
      </div>

      <div
        {...getRootProps()}
        className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
          isDragActive
            ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
            : 'border-gray-300 dark:border-gray-600 hover:border-gray-400 dark:hover:border-gray-500'
        }`}
      >
        <input {...getInputProps()} />
        
        {isUploading ? (
          <div className="space-y-4">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
            <p className="text-gray-600 dark:text-gray-300">Uploading files...</p>
          </div>
        ) : (
          <div className="space-y-4">
            <div className="mx-auto w-16 h-16 bg-gray-100 dark:bg-gray-700 rounded-full flex items-center justify-center">
              <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
              </svg>
            </div>
            
            <div>
              <p className="text-lg font-medium text-gray-900 dark:text-white">
                {isDragActive ? 'Drop files here' : 'Drag & drop files here'}
              </p>
              <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                or click to select files
              </p>
            </div>
            
            <p className="text-xs text-gray-500 dark:text-gray-400">
              Supports PDF, DOCX, XLSX, TXT, CSV, JSON, MD, HTML, XML
            </p>
          </div>
        )}
      </div>
    </div>
  )
}
