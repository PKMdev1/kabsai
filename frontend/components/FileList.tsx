'use client'

import { useState, useEffect } from 'react'
import axios from 'axios'
import toast from 'react-hot-toast'

interface File {
  id: number
  filename: string
  original_filename: string
  title: string
  file_type: string
  file_size: number
  created_at: string
  is_processed: boolean
  is_indexed: boolean
}

export default function FileList() {
  const [files, setFiles] = useState<File[]>([])
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    fetchFiles()
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

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString()
  }

  if (isLoading) {
    return (
      <div className="card">
        <div className="text-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-2 text-gray-600 dark:text-gray-300">Loading files...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="card">
      <div className="text-center mb-6">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
          Uploaded Files
        </h2>
        <p className="text-gray-600 dark:text-gray-300">
          {files.length} file(s) uploaded
        </p>
      </div>

      {files.length === 0 ? (
        <div className="text-center py-8">
          <p className="text-gray-500 dark:text-gray-400">
            No files uploaded yet. Go to the Upload tab to add files.
          </p>
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-gray-200 dark:border-gray-700">
                <th className="text-left py-3 px-4 font-medium text-gray-900 dark:text-white">File</th>
                <th className="text-left py-3 px-4 font-medium text-gray-900 dark:text-white">Type</th>
                <th className="text-left py-3 px-4 font-medium text-gray-900 dark:text-white">Size</th>
                <th className="text-left py-3 px-4 font-medium text-gray-900 dark:text-white">Uploaded</th>
                <th className="text-left py-3 px-4 font-medium text-gray-900 dark:text-white">Status</th>
              </tr>
            </thead>
            <tbody>
              {files.map((file) => (
                <tr key={file.id} className="border-b border-gray-100 dark:border-gray-800 hover:bg-gray-50 dark:hover:bg-gray-800">
                  <td className="py-3 px-4">
                    <div>
                      <p className="font-medium text-gray-900 dark:text-white">{file.title || file.original_filename}</p>
                      <p className="text-sm text-gray-500 dark:text-gray-400">{file.original_filename}</p>
                    </div>
                  </td>
                  <td className="py-3 px-4">
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200">
                      {file.file_type.toUpperCase()}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-gray-600 dark:text-gray-300">
                    {formatFileSize(file.file_size)}
                  </td>
                  <td className="py-3 px-4 text-gray-600 dark:text-gray-300">
                    {formatDate(file.created_at)}
                  </td>
                  <td className="py-3 px-4">
                    <div className="flex space-x-2">
                      {file.is_processed && (
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200">
                          Processed
                        </span>
                      )}
                      {file.is_indexed && (
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200">
                          Indexed
                        </span>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
