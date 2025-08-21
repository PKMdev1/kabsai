'use client'

import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import toast from 'react-hot-toast'
import axios from 'axios'

const registerSchema = z.object({
  username: z.string().min(3, 'Username must be at least 3 characters'),
  full_name: z.string().min(1, 'Full name is required'),
  password: z.string().min(6, 'Password must be at least 6 characters'),
  confirmPassword: z.string()
}).refine((data) => data.password === data.confirmPassword, {
  message: "Passwords don't match",
  path: ["confirmPassword"],
})

type RegisterFormData = z.infer<typeof registerSchema>

interface RegisterFormProps {
  onRegisterSuccess: () => void
  onBackToLogin: () => void
}

export default function RegisterForm({ onRegisterSuccess, onBackToLogin }: RegisterFormProps) {
  const [isLoading, setIsLoading] = useState(false)

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<RegisterFormData>({
    resolver: zodResolver(registerSchema),
  })

  const onSubmit = async (data: RegisterFormData) => {
    setIsLoading(true)
    try {
      const response = await axios.post('/api/v1/auth/register', {
        username: data.username,
        full_name: data.full_name,
        password: data.password,
        role: 'viewer'
      })
      
      if (response.status === 200) {
        toast.success('Registration successful! Please login.')
        onRegisterSuccess()
      }
    } catch (error: any) {
      if (error.response?.data?.detail) {
        toast.error(error.response.data.detail)
      } else {
        toast.error('Registration failed. Please try again.')
      }
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="card">
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        <div>
          <label htmlFor="username" className="block text-sm font-medium text-elite-700 dark:text-gray-300 mb-2">
            Username
          </label>
          <input
            id="username"
            type="text"
            {...register('username')}
            className="input-field"
            placeholder="Enter your username"
            disabled={isLoading}
          />
          {errors.username && (
            <p className="mt-1 text-sm text-red-600 dark:text-red-400">{errors.username.message}</p>
          )}
        </div>

        <div>
          <label htmlFor="full_name" className="block text-sm font-medium text-elite-700 dark:text-gray-300 mb-2">
            Full Name
          </label>
          <input
            id="full_name"
            type="text"
            {...register('full_name')}
            className="input-field"
            placeholder="Enter your full name"
            disabled={isLoading}
          />
          {errors.full_name && (
            <p className="mt-1 text-sm text-red-600 dark:text-red-400">{errors.full_name.message}</p>
          )}
        </div>

        <div>
          <label htmlFor="password" className="block text-sm font-medium text-elite-700 dark:text-gray-300 mb-2">
            Password
          </label>
          <input
            id="password"
            type="password"
            {...register('password')}
            className="input-field"
            placeholder="Enter your password"
            disabled={isLoading}
          />
          {errors.password && (
            <p className="mt-1 text-sm text-red-600 dark:text-red-400">{errors.password.message}</p>
          )}
        </div>

        <div>
          <label htmlFor="confirmPassword" className="block text-sm font-medium text-elite-700 dark:text-gray-300 mb-2">
            Confirm Password
          </label>
          <input
            id="confirmPassword"
            type="password"
            {...register('confirmPassword')}
            className="input-field"
            placeholder="Confirm your password"
            disabled={isLoading}
          />
          {errors.confirmPassword && (
            <p className="mt-1 text-sm text-red-600 dark:text-red-400">{errors.confirmPassword.message}</p>
          )}
        </div>

        <button
          type="submit"
          disabled={isLoading}
          className="btn-primary w-full disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isLoading ? 'Creating account...' : 'Create Account'}
        </button>
      </form>

      <div className="mt-6 text-center">
        <button
          type="button"
          onClick={onBackToLogin}
          className="text-sm text-elite-600 dark:text-gray-400 hover:text-elite-800 dark:hover:text-gray-300"
        >
          Already have an account? Sign in
        </button>
      </div>
    </div>
  )
}
