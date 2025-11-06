/**
 * API client with axios interceptors for authentication and error handling
 */
import axios, { AxiosInstance, AxiosError, InternalAxiosRequestConfig } from 'axios'
import { getAccessToken, getRefreshToken, setTokens, clearTokens } from './auth'

// Use empty string for same-origin requests (Nginx proxies /api to backend)
// Or specify a full URL for development (e.g., http://localhost:8000)
const API_URL = import.meta.env.VITE_API_URL || ''
const API_TIMEOUT = Number(import.meta.env.VITE_API_TIMEOUT) || 30000

/**
 * Create axios instance with default configuration
 */
export const api: AxiosInstance = axios.create({
  baseURL: API_URL,
  timeout: API_TIMEOUT,
  headers: {
    'Content-Type': 'application/json',
  },
})

/**
 * Request interceptor to add auth token
 */
api.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = getAccessToken()

    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }

    return config
  },
  (error: AxiosError) => {
    return Promise.reject(error)
  }
)

/**
 * Response interceptor for error handling and token refresh
 */
api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & {
      _retry?: boolean
    }

    // If error is 401 and we haven't retried yet, try to refresh token
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true

      try {
        const refreshToken = getRefreshToken()

        if (!refreshToken) {
          clearTokens()
          window.location.href = '/login'
          return Promise.reject(error)
        }

        // Try to refresh token (use relative URL if API_URL is empty)
        const refreshUrl = API_URL ? `${API_URL}/api/v1/auth/refresh` : '/api/v1/auth/refresh'
        const response = await axios.post(refreshUrl, {
          refresh_token: refreshToken,
        })

        const { access_token, refresh_token: new_refresh_token } = response.data

        // Save new tokens
        setTokens(access_token, new_refresh_token)

        // Retry original request with new token
        if (originalRequest.headers) {
          originalRequest.headers.Authorization = `Bearer ${access_token}`
        }

        return api(originalRequest)
      } catch (refreshError) {
        // Refresh failed, redirect to login
        clearTokens()
        window.location.href = '/login'
        return Promise.reject(refreshError)
      }
    }

    return Promise.reject(error)
  }
)

/**
 * API error handler
 */
export function handleApiError(error: unknown): string {
  if (axios.isAxiosError(error)) {
    if (error.response) {
      // Server responded with error
      const message = error.response.data?.detail || error.response.data?.message
      return message || `Error: ${error.response.status}`
    } else if (error.request) {
      // Request made but no response
      return 'No response from server. Please check your connection.'
    }
  }

  return 'An unexpected error occurred.'
}

/**
 * API types
 */
export interface ApiResponse<T> {
  data: T
  message?: string
}

export interface ApiError {
  detail: string
  [key: string]: unknown
}

/**
 * Generic API request wrapper
 */
export async function apiRequest<T>(
  method: 'get' | 'post' | 'put' | 'patch' | 'delete',
  url: string,
  data?: unknown,
  config?: Record<string, unknown>
): Promise<T> {
  try {
    const response = await api[method](url, data, config)
    return response.data as T
  } catch (error) {
    throw new Error(handleApiError(error))
  }
}
