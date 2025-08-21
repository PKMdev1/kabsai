'use client'

import { useState, useEffect } from 'react'
import { Upload, Search, Filter, Download, Trash2, Edit, Tag } from 'lucide-react'
import axios from 'axios'
import toast from 'react-hot-toast'
import { useDropzone } from 'react-dropzone'
import FileUploadModal from './FileUploadModal'

interface File {
  id: number
  filename: string
  original_filename: string
  file_size: number
  file_type: string
  mime_type: string
  title?: string
  description?: string
  tags?: string[]
  project?: string
  department?: string
  is_processed: boolean
  is_indexed: boolean
  embedding_status: string
  created_at: string
}

export default function FileManager() {
  const [files, setFiles] = useState<File[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedProject, setSelectedProject] = useState('')
  const [selectedDepartment, setSelectedDepartment] = useState('')
  const [projects, setProjects] = useState<string[]>([])
  const [departments, setDepartments] = useState<string[]>([])
  const [showUploadModal, setShowUploadModal] = useState(false)
  const [editingFile, setEditingFile] = useState<File | null>(null)

  useEffect(() => {
    fetchFiles()
    fetchProjects()
    fetchDepartments()
  }, [])

  const fetchFiles = async () => {
    try {
      const response = await axios.get('/api/v1/files/')
      setFiles(response.data)
    } catch (error) {
      console.error('Error fetching files:', error)
      toast.error('Failed to load files')
    } finally {
      setIsLoading(false)
    }
  }

  const fetchProjects = async () => {
    try {
      const response = await axios.get('/api/v1/files/projects/list')
      setProjects(response.data)
    } catch (error) {
      console.error('Error fetching projects:', error)
    }
  }

  const fetchDepartments = async () => {
    try {
      const response = await axios.get('/api/v1/files/departments/list')
      setDepartments(response.data)
    } catch (error) {
      console.error('Error fetching departments:', error)
    }
  }

  const handleFileUpload = async (file: File, metadata: any) => {
    try {
      const formData = new FormData()
      formData.append('file', file)
      formData.append('title', metadata.title || '')
      formData.append('description', metadata.description || '')
      formData.append('tags', JSON.stringify(metadata.tags || []))
      formData.append('project', metadata.project || '')
      formData.append('department', metadata.department || '')

      const response = await axios.post('/api/v1/files/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      })

      if (response.data.status === 'success') {
        toast.success('File uploaded successfully!')
        fetchFiles()
        setShowUploadModal(false)
      } else {
        toast.error(response.data.message || 'Upload failed')
      }
    } catch (error) {
      console.error('Error uploading file:', error)
      toast.error('Failed to upload file')
    }
  }

  const handleDeleteFile = async (fileId: number) => {
    if (!confirm('Are you sure you want to delete this file?')) return

    try {
      await axios.delete(`/api/v1/files/${fileId}`)
      toast.success('File deleted successfully')
      fetchFiles()
    } catch (error) {
      console.error('Error deleting file:', error)
      toast.error('Failed to delete file')
    }
  }

  const handleDownloadFile = async (fileId: number, filename: string) => {
    try {
      const response = await axios.get(`/api/v1/files/${fileId}/download`, {
        responseType: 'blob',
      })

      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', filename)
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
    } catch (error) {
      console.error('Error downloading file:', error)
      toast.error('Failed to download file')
    }
  }

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  const filteredFiles = files.filter(file => {
    const matchesSearch = !searchTerm || 
      file.original_filename.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (file.title && file.title.toLowerCase().includes(searchTerm.toLowerCase())) ||
      (file.description && file.description.toLowerCase().includes(searchTerm.toLowerCase()))
    
    const matchesProject = !selectedProject || file.project === selectedProject
    const matchesDepartment = !selectedDepartment || file.department === selectedDepartment

    return matchesSearch && matchesProject && matchesDepartment
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-kabs-600"></div>
      </div>
    )
  }

  return (
    <div className="flex flex-col h-full bg-white">
      {/* Header */}
      <div className="border-b border-elite-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold text-elite-900">Document Vault</h2>
            <p className="text-sm text-elite-600">Manage and organize your files</p>
          </div>
          <button
            onClick={() => setShowUploadModal(true)}
            className="btn-primary flex items-center space-x-2"
          >
            <Upload className="w-4 h-4" />
            <span>Upload File</span>
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="border-b border-elite-200 px-6 py-4">
        <div className="flex items-center space-x-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-elite-400 w-4 h-4" />
            <input
              type="text"
              placeholder="Search files..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-elite-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-kabs-500 focus:border-transparent"
            />
          </div>
          
          <select
            value={selectedProject}
            onChange={(e) => setSelectedProject(e.target.value)}
            className="px-3 py-2 border border-elite-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-kabs-500 focus:border-transparent"
          >
            <option value="">All Projects</option>
            {projects.map(project => (
              <option key={project} value={project}>{project}</option>
            ))}
          </select>

          <select
            value={selectedDepartment}
            onChange={(e) => setSelectedDepartment(e.target.value)}
            className="px-3 py-2 border border-elite-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-kabs-500 focus:border-transparent"
          >
            <option value="">All Departments</option>
            {departments.map(dept => (
              <option key={dept} value={dept}>{dept}</option>
            ))}
          </select>
        </div>
      </div>

      {/* File List */}
      <div className="flex-1 overflow-y-auto p-6">
        {filteredFiles.length === 0 ? (
          <div className="text-center py-12">
            <div className="w-16 h-16 bg-elite-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <Upload className="w-8 h-8 text-elite-400" />
            </div>
            <h3 className="text-lg font-medium text-elite-900 mb-2">No files found</h3>
            <p className="text-elite-600">
              {searchTerm || selectedProject || selectedDepartment 
                ? 'Try adjusting your search criteria'
                : 'Upload your first document to get started'
              }
            </p>
          </div>
        ) : (
          <div className="grid gap-4">
            {filteredFiles.map((file) => (
              <div key={file.id} className="card hover:shadow-md transition-shadow">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-3 mb-2">
                      <div className="w-10 h-10 bg-kabs-100 rounded-lg flex items-center justify-center">
                        <span className="text-kabs-600 font-medium text-sm uppercase">
                          {file.file_type}
                        </span>
                      </div>
                      <div>
                        <h3 className="font-medium text-elite-900">
                          {file.title || file.original_filename}
                        </h3>
                        <p className="text-sm text-elite-600">
                          {file.original_filename} • {formatFileSize(file.file_size)}
                        </p>
                      </div>
                    </div>

                    {file.description && (
                      <p className="text-sm text-elite-700 mb-3">{file.description}</p>
                    )}

                    <div className="flex items-center space-x-4 text-xs text-elite-500">
                      {file.project && (
                        <span className="bg-kabs-100 text-kabs-700 px-2 py-1 rounded">
                          {file.project}
                        </span>
                      )}
                      {file.department && (
                        <span className="bg-elite-100 text-elite-700 px-2 py-1 rounded">
                          {file.department}
                        </span>
                      )}
                      <span className={`px-2 py-1 rounded ${
                        file.embedding_status === 'completed' 
                          ? 'bg-green-100 text-green-700'
                          : file.embedding_status === 'failed'
                          ? 'bg-red-100 text-red-700'
                          : 'bg-yellow-100 text-yellow-700'
                      }`}>
                        {file.embedding_status}
                      </span>
                    </div>

                    {file.tags && file.tags.length > 0 && (
                      <div className="flex items-center space-x-2 mt-3">
                        <Tag className="w-3 h-3 text-elite-400" />
                        <div className="flex flex-wrap gap-1">
                          {file.tags.map((tag, index) => (
                            <span key={index} className="bg-elite-100 text-elite-600 px-2 py-1 rounded text-xs">
                              {tag}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>

                  <div className="flex items-center space-x-2 ml-4">
                    <button
                      onClick={() => handleDownloadFile(file.id, file.original_filename)}
                      className="p-2 text-elite-600 hover:text-elite-900 hover:bg-elite-100 rounded-lg transition-colors"
                      title="Download"
                    >
                      <Download className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => setEditingFile(file)}
                      className="p-2 text-elite-600 hover:text-elite-900 hover:bg-elite-100 rounded-lg transition-colors"
                      title="Edit"
                    >
                      <Edit className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => handleDeleteFile(file.id)}
                      className="p-2 text-red-600 hover:text-red-900 hover:bg-red-100 rounded-lg transition-colors"
                      title="Delete"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Upload Modal */}
      {showUploadModal && (
        <FileUploadModal
          onClose={() => setShowUploadModal(false)}
          onUpload={handleFileUpload}
        />
      )}
    </div>
  )
}
