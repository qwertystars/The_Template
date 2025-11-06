/**
 * Authentication utilities for token management
 */

const ACCESS_TOKEN_KEY = 'access_token'
const REFRESH_TOKEN_KEY = 'refresh_token'
const USER_KEY = 'user'

/**
 * User type
 */
export interface User {
  id: number
  email: string
  full_name?: string
  avatar_url?: string
  is_active: boolean
  is_superuser: boolean
  is_email_verified: boolean
  roles?: string[]
}

/**
 * Get access token from storage
 */
export function getAccessToken(): string | null {
  return localStorage.getItem(ACCESS_TOKEN_KEY)
}

/**
 * Get refresh token from storage
 */
export function getRefreshToken(): string | null {
  return localStorage.getItem(REFRESH_TOKEN_KEY)
}

/**
 * Set tokens in storage
 */
export function setTokens(accessToken: string, refreshToken: string): void {
  localStorage.setItem(ACCESS_TOKEN_KEY, accessToken)
  localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken)
}

/**
 * Clear tokens from storage
 */
export function clearTokens(): void {
  localStorage.removeItem(ACCESS_TOKEN_KEY)
  localStorage.removeItem(REFRESH_TOKEN_KEY)
  localStorage.removeItem(USER_KEY)
}

/**
 * Check if user is authenticated
 */
export function isAuthenticated(): boolean {
  const token = getAccessToken()
  if (!token) return false

  try {
    // Check if token is expired
    const payload = decodeToken(token)
    if (!payload || !payload.exp) return false

    const exp = payload.exp * 1000 // Convert to milliseconds
    return Date.now() < exp
  } catch {
    return false
  }
}

/**
 * Get current user from storage
 */
export function getCurrentUser(): User | null {
  const userStr = localStorage.getItem(USER_KEY)
  if (!userStr) return null

  try {
    return JSON.parse(userStr)
  } catch {
    return null
  }
}

/**
 * Set current user in storage
 */
export function setCurrentUser(user: User): void {
  localStorage.setItem(USER_KEY, JSON.stringify(user))
}

/**
 * JWT token payload interface
 */
interface TokenPayload {
  sub: string
  exp: number
  type: string
  [key: string]: unknown
}

/**
 * Decode JWT token
 */
export function decodeToken(token: string): TokenPayload | null {
  try {
    const payload = JSON.parse(atob(token.split('.')[1])) as TokenPayload
    return payload
  } catch {
    return null
  }
}

/**
 * Check if user has role
 */
export function hasRole(role: string, user?: User | null): boolean {
  const currentUser = user || getCurrentUser()
  if (!currentUser?.roles) return false

  return currentUser.roles.includes(role)
}

/**
 * Check if user is admin
 */
export function isAdmin(user?: User | null): boolean {
  const currentUser = user || getCurrentUser()
  return currentUser?.is_superuser || hasRole('admin', currentUser)
}
