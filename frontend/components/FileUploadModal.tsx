'use client'

import { useState, useCallback } from 'react'
import { X, Upload, File, Tag } from 'lucide-react'
import { useDropzone } from 'react-dropzone'

interface FileUploadModalProps {
  onClose: () => void
  onUpload: (file: File, metadata: any) => void
}

export default function FileUploadModal({ onClose, onUpload }: FileUploadModalProps) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [metadata, setMetadata] = useState({
    title: '',
    description: '',
    tags: [] as string[],
    project: '',
    department: '',
  })
  const [tagInput, setTagInput] = useState('')

  const onDrop = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      setSelectedFile(acceptedFiles[0])
    }
  }, [])

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
    },
    maxFiles: 1,
  })

  const handleAddTag = () => {
    if (tagInput.trim() && !metadata.tags.includes(tagInput.trim())) {
      setMetadata(prev => ({
        ...prev,
        tags: [...prev.tags, tagInput.trim()]
      }))
      setTagInput('')
    }
  }

  const handleRemoveTag = (tagToRemove: string) => {
    setMetadata(prev => ({
      ...prev,
      tags: prev.tags.filter(tag => tag !== tagToRemove)
    }))
  }

  const handleSubmit = () => {
    if (selectedFile) {
      onUpload(selectedFile, metadata)
    }
  }

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-elite-200">
          <h2 className="text-xl font-semibold text-elite-900">Upload File</h2>
          <button
            onClick={onClose}
            className="p-2 text-elite-400 hover:text-elite-600 hover:bg-elite-100 rounded-lg transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-6 space-y-6">
          {/* File Upload Area */}
          <div>
            <label className="block text-sm font-medium text-elite-700 mb-3">
              Select File
            </label>
            <div
              {...getRootProps()}
              className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
                isDragActive
                  ? 'border-kabs-400 bg-kabs-50'
                  : 'border-elite-300 hover:border-kabs-400 hover:bg-elite-50'
              }`}
            >
              <input {...getInputProps()} />
              <Upload className="w-12 h-12 text-elite-400 mx-auto mb-4" />
              {isDragActive ? (
                <p className="text-kabs-600">Drop the file here...</p>
              ) : (
                <div>
                  <p className="text-elite-600 mb-2">
                    Drag and drop a file here, or click to select
                  </p>
                  <p className="text-sm text-elite-500">
                    Supports PDF, DOCX, XLSX, TXT, CSV, JSON, MD, HTML
                  </p>
                </div>
              )}
            </div>
          </div>

          {/* Selected File Info */}
          {selectedFile && (
            <div className="bg-elite-50 rounded-lg p-4">
              <div className="flex items-center space-x-3">
                <File className="w-8 h-8 text-kabs-600" />
                <div className="flex-1">
                  <h3 className="font-medium text-elite-900">{selectedFile.name}</h3>
                  <p className="text-sm text-elite-600">
                    {formatFileSize(selectedFile.size)} • {selectedFile.type}
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Metadata Form */}
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-elite-700 mb-2">
                Title (optional)
              </label>
              <input
                type="text"
                value={metadata.title}
                onChange={(e) => setMetadata(prev => ({ ...prev, title: e.target.value }))}
                placeholder="Enter a title for the file"
                className="input-field"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-elite-700 mb-2">
                Description (optional)
              </label>
              <textarea
                value={metadata.description}
                onChange={(e) => setMetadata(prev => ({ ...prev, description: e.target.value }))}
                placeholder="Enter a description"
                rows={3}
                className="input-field"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-elite-700 mb-2">
                Tags
              </label>
              <div className="flex space-x-2 mb-2">
                <input
                  type="text"
                  value={tagInput}
                  onChange={(e) => setTagInput(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), handleAddTag())}
                  placeholder="Add a tag"
                  className="flex-1 input-field"
                />
                <button
                  onClick={handleAddTag}
                  className="px-4 py-2 bg-kabs-600 text-white rounded-lg hover:bg-kabs-700 transition-colors"
                >
                  Add
                </button>
              </div>
              {metadata.tags.length > 0 && (
                <div className="flex flex-wrap gap-2">
                  {metadata.tags.map((tag, index) => (
                    <span
                      key={index}
                      className="bg-kabs-100 text-kabs-700 px-3 py-1 rounded-full text-sm flex items-center space-x-1"
                    >
                      <Tag className="w-3 h-3" />
                      <span>{tag}</span>
                      <button
                        onClick={() => handleRemoveTag(tag)}
                        className="ml-1 text-kabs-500 hover:text-kabs-700"
                      >
                        ×
                      </button>
                    </span>
                  ))}
                </div>
              )}
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-elite-700 mb-2">
                  Project (optional)
                </label>
                <input
                  type="text"
                  value={metadata.project}
                  onChange={(e) => setMetadata(prev => ({ ...prev, project: e.target.value }))}
                  placeholder="Enter project name"
                  className="input-field"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-elite-700 mb-2">
                  Department (optional)
                </label>
                <input
                  type="text"
                  value={metadata.department}
                  onChange={(e) => setMetadata(prev => ({ ...prev, department: e.target.value }))}
                  placeholder="Enter department"
                  className="input-field"
                />
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end space-x-4 p-6 border-t border-elite-200">
          <button
            onClick={onClose}
            className="btn-secondary"
          >
            Cancel
          </button>
          <button
            onClick={handleSubmit}
            disabled={!selectedFile}
            className="btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Upload File
          </button>
        </div>
      </div>
    </div>
  )
}
