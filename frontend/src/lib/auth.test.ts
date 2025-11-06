/**
 * Comprehensive tests for frontend/src/lib/auth.ts
 */
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import {
  getAccessToken,
  getRefreshToken,
  setTokens,
  clearTokens,
  isAuthenticated,
  getCurrentUser,
  setCurrentUser,
  decodeToken,
  hasRole,
  isAdmin,
  type User,
} from './auth'

describe('Token Management', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  afterEach(() => {
    localStorage.clear()
  })

  describe('getAccessToken', () => {
    it('should return null when no token exists', () => {
      expect(getAccessToken()).toBeNull()
    })

    it('should return token when it exists', () => {
      localStorage.setItem('access_token', 'test-token')
      expect(getAccessToken()).toBe('test-token')
    })
  })

  describe('getRefreshToken', () => {
    it('should return null when no token exists', () => {
      expect(getRefreshToken()).toBeNull()
    })

    it('should return token when it exists', () => {
      localStorage.setItem('refresh_token', 'refresh-token')
      expect(getRefreshToken()).toBe('refresh-token')
    })
  })

  describe('setTokens', () => {
    it('should store both access and refresh tokens', () => {
      setTokens('access-123', 'refresh-456')
      
      expect(localStorage.getItem('access_token')).toBe('access-123')
      expect(localStorage.getItem('refresh_token')).toBe('refresh-456')
    })

    it('should overwrite existing tokens', () => {
      setTokens('old-access', 'old-refresh')
      setTokens('new-access', 'new-refresh')
      
      expect(localStorage.getItem('access_token')).toBe('new-access')
      expect(localStorage.getItem('refresh_token')).toBe('new-refresh')
    })
  })

  describe('clearTokens', () => {
    it('should remove all tokens and user data', () => {
      localStorage.setItem('access_token', 'token')
      localStorage.setItem('refresh_token', 'refresh')
      localStorage.setItem('user', '{"id": 1}')
      
      clearTokens()
      
      expect(localStorage.getItem('access_token')).toBeNull()
      expect(localStorage.getItem('refresh_token')).toBeNull()
      expect(localStorage.getItem('user')).toBeNull()
    })

    it('should not throw when clearing empty storage', () => {
      expect(() => clearTokens()).not.toThrow()
    })
  })
})

describe('Authentication Status', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  describe('isAuthenticated', () => {
    it('should return false when no token exists', () => {
      expect(isAuthenticated()).toBe(false)
    })

    it('should return false for invalid token format', () => {
      localStorage.setItem('access_token', 'invalid-token')
      expect(isAuthenticated()).toBe(false)
    })

    it('should return true for valid non-expired token', () => {
      // Create a token that expires in 1 hour
      const futureExp = Math.floor(Date.now() / 1000) + 3600
      const payload = JSON.stringify({ exp: futureExp, sub: '123' })
      const token = `header.${btoa(payload)}.signature`
      
      localStorage.setItem('access_token', token)
      expect(isAuthenticated()).toBe(true)
    })

    it('should return false for expired token', () => {
      // Create a token that expired 1 hour ago
      const pastExp = Math.floor(Date.now() / 1000) - 3600
      const payload = JSON.stringify({ exp: pastExp, sub: '123' })
      const token = `header.${btoa(payload)}.signature`
      
      localStorage.setItem('access_token', token)
      expect(isAuthenticated()).toBe(false)
    })

    it('should return false for token with malformed payload', () => {
      const token = 'header.invalid-base64.signature'
      localStorage.setItem('access_token', token)
      expect(isAuthenticated()).toBe(false)
    })
  })
})

describe('User Management', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  const mockUser: User = {
    id: 1,
    email: 'test@example.com',
    full_name: 'Test User',
    is_active: true,
    is_superuser: false,
    is_email_verified: true,
    roles: ['user'],
  }

  describe('getCurrentUser', () => {
    it('should return null when no user data exists', () => {
      expect(getCurrentUser()).toBeNull()
    })

    it('should return user when data exists', () => {
      localStorage.setItem('user', JSON.stringify(mockUser))
      
      const user = getCurrentUser()
      expect(user).toEqual(mockUser)
    })

    it('should return null for invalid JSON', () => {
      localStorage.setItem('user', 'invalid json')
      expect(getCurrentUser()).toBeNull()
    })

    it('should handle empty string', () => {
      localStorage.setItem('user', '')
      expect(getCurrentUser()).toBeNull()
    })
  })

  describe('setCurrentUser', () => {
    it('should store user data as JSON', () => {
      setCurrentUser(mockUser)
      
      const stored = localStorage.getItem('user')
      expect(stored).toBeTruthy()
      expect(JSON.parse(stored!)).toEqual(mockUser)
    })

    it('should overwrite existing user data', () => {
      setCurrentUser(mockUser)
      
      const newUser = { ...mockUser, id: 2, email: 'new@example.com' }
      setCurrentUser(newUser)
      
      const stored = getCurrentUser()
      expect(stored?.id).toBe(2)
      expect(stored?.email).toBe('new@example.com')
    })
  })
})

describe('Token Decoding', () => {
  describe('decodeToken', () => {
    it('should decode valid JWT token', () => {
      const payload = { sub: '123', exp: 1234567890 }
      const encodedPayload = btoa(JSON.stringify(payload))
      const token = `header.${encodedPayload}.signature`
      
      const decoded = decodeToken(token)
      expect(decoded).toEqual(payload)
    })

    it('should return null for invalid token format', () => {
      expect(decodeToken('invalid')).toBeNull()
    })

    it('should return null for malformed payload', () => {
      const token = 'header.not-base64.signature'
      expect(decodeToken(token)).toBeNull()
    })

    it('should return null for empty string', () => {
      expect(decodeToken('')).toBeNull()
    })

    it('should handle token with special characters in payload', () => {
      const payload = { sub: 'user@example.com', data: 'special/chars+=' }
      const encodedPayload = btoa(JSON.stringify(payload))
      const token = `header.${encodedPayload}.signature`
      
      const decoded = decodeToken(token)
      expect(decoded?.sub).toBe('user@example.com')
    })
  })
})

describe('Role and Permission Checks', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  const adminUser: User = {
    id: 1,
    email: 'admin@example.com',
    is_active: true,
    is_superuser: true,
    is_email_verified: true,
    roles: ['admin', 'user'],
  }

  const regularUser: User = {
    id: 2,
    email: 'user@example.com',
    is_active: true,
    is_superuser: false,
    is_email_verified: true,
    roles: ['user'],
  }

  const userWithoutRoles: User = {
    id: 3,
    email: 'noroles@example.com',
    is_active: true,
    is_superuser: false,
    is_email_verified: true,
  }

  describe('hasRole', () => {
    it('should return true when user has the role', () => {
      expect(hasRole('admin', adminUser)).toBe(true)
      expect(hasRole('user', adminUser)).toBe(true)
    })

    it('should return false when user does not have the role', () => {
      expect(hasRole('admin', regularUser)).toBe(false)
    })

    it('should return false when user has no roles', () => {
      expect(hasRole('admin', userWithoutRoles)).toBe(false)
    })

    it('should return false when roles array is undefined', () => {
      const user = { ...regularUser, roles: undefined }
      expect(hasRole('user', user)).toBe(false)
    })

    it('should check against stored user when no user provided', () => {
      localStorage.setItem('user', JSON.stringify(adminUser))
      expect(hasRole('admin')).toBe(true)
    })

    it('should return false when no user provided and none stored', () => {
      expect(hasRole('admin')).toBe(false)
    })

    it('should be case-sensitive', () => {
      expect(hasRole('Admin', adminUser)).toBe(false)
      expect(hasRole('admin', adminUser)).toBe(true)
    })
  })

  describe('isAdmin', () => {
    it('should return true for superuser', () => {
      expect(isAdmin(adminUser)).toBe(true)
    })

    it('should return true for user with admin role', () => {
      const roleAdmin: User = {
        ...regularUser,
        is_superuser: false,
        roles: ['admin', 'user'],
      }
      expect(isAdmin(roleAdmin)).toBe(true)
    })

    it('should return false for regular user', () => {
      expect(isAdmin(regularUser)).toBe(false)
    })

    it('should return false when user is null', () => {
      expect(isAdmin(null)).toBe(false)
    })

    it('should check stored user when no user provided', () => {
      localStorage.setItem('user', JSON.stringify(adminUser))
      expect(isAdmin()).toBe(true)
    })

    it('should return false when no user provided and none stored', () => {
      expect(isAdmin()).toBe(false)
    })
  })
})

describe('Edge Cases and Error Handling', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  it('should handle empty role array gracefully', () => {
    const user: User = {
      id: 1,
      email: 'test@example.com',
      is_active: true,
      is_superuser: false,
      is_email_verified: true,
      roles: [],
    }
    expect(hasRole('admin', user)).toBe(false)
  })

  it('should handle very long tokens', () => {
    const longToken = 'a'.repeat(10000)
    localStorage.setItem('access_token', longToken)
    expect(isAuthenticated()).toBe(false)
  })

  it('should handle special characters in email', () => {
    const user: User = {
      id: 1,
      email: 'user+test@example.com',
      is_active: true,
      is_superuser: false,
      is_email_verified: true,
    }
    setCurrentUser(user)
    const retrieved = getCurrentUser()
    expect(retrieved?.email).toBe('user+test@example.com')
  })

  it('should handle unicode in user data', () => {
    const user: User = {
      id: 1,
      email: 'user@example.com',
      full_name: '测试用户 👤',
      is_active: true,
      is_superuser: false,
      is_email_verified: true,
    }
    setCurrentUser(user)
    const retrieved = getCurrentUser()
    expect(retrieved?.full_name).toBe('测试用户 👤')
  })
})