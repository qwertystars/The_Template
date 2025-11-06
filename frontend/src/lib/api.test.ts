/**
 * Comprehensive tests for frontend/src/lib/api.ts
 */
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import axios, { AxiosError } from 'axios'
import MockAdapter from 'axios-mock-adapter'
import { api, handleApiError, apiRequest } from './api'
import * as auth from './auth'

// Mock the auth module
vi.mock('./auth', () => ({
  getAccessToken: vi.fn(),
  getRefreshToken: vi.fn(),
  setTokens: vi.fn(),
  clearTokens: vi.fn(),
}))

describe('API Client', () => {
  let mock: MockAdapter

  beforeEach(() => {
    mock = new MockAdapter(api)
    vi.clearAllMocks()
    // Clear any stored tokens
    localStorage.clear()
  })

  afterEach(() => {
    mock.restore()
  })

  describe('Request Interceptor', () => {
    it('should add authorization header when token exists', async () => {
      vi.mocked(auth.getAccessToken).mockReturnValue('test-token')
      mock.onGet('/test').reply((config) => {
        expect(config.headers?.Authorization).toBe('Bearer test-token')
        return [200, { success: true }]
      })

      await api.get('/test')
    })

    it('should not add authorization header when no token', async () => {
      vi.mocked(auth.getAccessToken).mockReturnValue(null)
      mock.onGet('/test').reply((config) => {
        expect(config.headers?.Authorization).toBeUndefined()
        return [200, { success: true }]
      })

      await api.get('/test')
    })

    it('should include content-type header', async () => {
      mock.onGet('/test').reply((config) => {
        expect(config.headers?.['Content-Type']).toBe('application/json')
        return [200, {}]
      })

      await api.get('/test')
    })
  })

  describe('Response Interceptor - Token Refresh', () => {
    it('should retry request after successful token refresh', async () => {
      vi.mocked(auth.getAccessToken).mockReturnValue('expired-token')
      vi.mocked(auth.getRefreshToken).mockReturnValue('refresh-token')

      // First request fails with 401
      mock.onGet('/protected').replyOnce(401)

      // Refresh token request succeeds
      mock.onPost('/api/v1/auth/refresh').reply(200, {
        access_token: 'new-access-token',
        refresh_token: 'new-refresh-token',
      })

      // Retry with new token succeeds
      mock.onGet('/protected').reply(200, { data: 'success' })

      const response = await api.get('/protected')

      expect(response.data.data).toBe('success')
      expect(auth.setTokens).toHaveBeenCalledWith(
        'new-access-token',
        'new-refresh-token'
      )
    })

    it('should redirect to login when no refresh token', async () => {
      vi.mocked(auth.getRefreshToken).mockReturnValue(null)
      
      // Mock window.location.href
      const originalLocation = window.location
      delete (window as any).location
      window.location = { ...originalLocation, href: '' } as any

      mock.onGet('/protected').reply(401)

      try {
        await api.get('/protected')
      } catch (error) {
        // Expected to fail
      }

      expect(auth.clearTokens).toHaveBeenCalled()
      expect(window.location.href).toBe('/login')

      // Restore
      window.location = originalLocation
    })

    it('should redirect to login when token refresh fails', async () => {
      vi.mocked(auth.getRefreshToken).mockReturnValue('refresh-token')

      const originalLocation = window.location
      delete (window as any).location
      window.location = { ...originalLocation, href: '' } as any

      mock.onGet('/protected').reply(401)
      mock.onPost('/api/v1/auth/refresh').reply(401)

      try {
        await api.get('/protected')
      } catch (error) {
        // Expected to fail
      }

      expect(auth.clearTokens).toHaveBeenCalled()
      expect(window.location.href).toBe('/login')

      window.location = originalLocation
    })

    it('should not retry request twice', async () => {
      vi.mocked(auth.getRefreshToken).mockReturnValue('refresh-token')

      // Both requests fail with 401
      mock.onGet('/protected').reply(401)
      mock.onPost('/api/v1/auth/refresh').reply(200, {
        access_token: 'new-token',
        refresh_token: 'new-refresh',
      })

      let requestCount = 0
      mock.onGet('/protected').reply(() => {
        requestCount++
        return [401]
      })

      try {
        await api.get('/protected')
      } catch (error) {
        // Expected to fail
      }

      // Should only retry once (original + 1 retry = 2 total)
      expect(requestCount).toBeLessThanOrEqual(2)
    })

    it('should handle non-401 errors normally', async () => {
      mock.onGet('/error').reply(500, { detail: 'Server error' })

      await expect(api.get('/error')).rejects.toThrow()
    })
  })

  describe('handleApiError', () => {
    it('should extract error message from response detail', () => {
      const error = {
        isAxiosError: true,
        response: {
          status: 400,
          data: { detail: 'Validation error' },
        },
      } as AxiosError

      const message = handleApiError(error)
      expect(message).toBe('Validation error')
    })

    it('should extract error message from response message', () => {
      const error = {
        isAxiosError: true,
        response: {
          status: 400,
          data: { message: 'Custom error message' },
        },
      } as AxiosError

      const message = handleApiError(error)
      expect(message).toBe('Custom error message')
    })

    it('should return status code when no message available', () => {
      const error = {
        isAxiosError: true,
        response: {
          status: 404,
          data: {},
        },
      } as AxiosError

      const message = handleApiError(error)
      expect(message).toBe('Error: 404')
    })

    it('should handle network errors', () => {
      const error = {
        isAxiosError: true,
        request: {},
      } as AxiosError

      const message = handleApiError(error)
      expect(message).toContain('No response from server')
    })

    it('should handle unknown errors', () => {
      const message = handleApiError(new Error('Unknown'))
      expect(message).toBe('An unexpected error occurred.')
    })

    it('should handle non-error objects', () => {
      const message = handleApiError('string error')
      expect(message).toBe('An unexpected error occurred.')
    })
  })

  describe('apiRequest', () => {
    it('should make GET request', async () => {
      mock.onGet('/users').reply(200, { users: [] })

      const data = await apiRequest('get', '/users')
      expect(data).toEqual({ users: [] })
    })

    it('should make POST request with data', async () => {
      const postData = { name: 'Test' }
      mock.onPost('/users', postData).reply(201, { id: 1, ...postData })

      const data = await apiRequest('post', '/users', postData)
      expect(data).toEqual({ id: 1, name: 'Test' })
    })

    it('should make PUT request', async () => {
      const putData = { name: 'Updated' }
      mock.onPut('/users/1', putData).reply(200, { id: 1, ...putData })

      const data = await apiRequest('put', '/users/1', putData)
      expect(data.name).toBe('Updated')
    })

    it('should make PATCH request', async () => {
      const patchData = { active: false }
      mock.onPatch('/users/1', patchData).reply(200, { id: 1, ...patchData })

      const data = await apiRequest('patch', '/users/1', patchData)
      expect(data.active).toBe(false)
    })

    it('should make DELETE request', async () => {
      mock.onDelete('/users/1').reply(204)

      await apiRequest('delete', '/users/1')
    })

    it('should throw error with message on failure', async () => {
      mock.onGet('/error').reply(500, { detail: 'Internal error' })

      await expect(apiRequest('get', '/error')).rejects.toThrow('Internal error')
    })

    it('should pass custom config', async () => {
      mock.onGet('/users').reply((config) => {
        expect(config.params).toEqual({ page: 1 })
        return [200, []]
      })

      await apiRequest('get', '/users', undefined, { params: { page: 1 } })
    })
  })

  describe('API Configuration', () => {
    it('should use correct base URL from environment', () => {
      // The baseURL is set during module initialization
      expect(api.defaults.baseURL).toBeDefined()
    })

    it('should have correct timeout', () => {
      expect(api.defaults.timeout).toBeGreaterThan(0)
    })

    it('should have JSON content type', () => {
      expect(api.defaults.headers['Content-Type']).toBe('application/json')
    })
  })

  describe('Edge Cases', () => {
    it('should handle empty response', async () => {
      mock.onGet('/empty').reply(200)

      const response = await api.get('/empty')
      expect(response.data).toBeUndefined()
    })

    it('should handle null response data', async () => {
      mock.onGet('/null').reply(200, null)

      const response = await api.get('/null')
      expect(response.data).toBeNull()
    })

    it('should handle large response', async () => {
      const largeData = { items: new Array(1000).fill({ id: 1, data: 'test' }) }
      mock.onGet('/large').reply(200, largeData)

      const response = await api.get('/large')
      expect(response.data.items.length).toBe(1000)
    })

    it('should handle unicode in request/response', async () => {
      const unicodeData = { message: '你好世界 🌍' }
      mock.onPost('/unicode', unicodeData).reply(200, unicodeData)

      const response = await api.post('/unicode', unicodeData)
      expect(response.data.message).toBe('你好世界 🌍')
    })

    it('should handle timeout', async () => {
      mock.onGet('/timeout').timeout()

      await expect(api.get('/timeout')).rejects.toThrow()
    })

    it('should handle network error', async () => {
      mock.onGet('/network').networkError()

      await expect(api.get('/network')).rejects.toThrow()
    })
  })
})