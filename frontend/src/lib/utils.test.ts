/**
 * Comprehensive tests for frontend/src/lib/utils.ts
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import {
  cn,
  formatDate,
  formatDateTime,
  truncate,
  sleep,
  formatFileSize,
  debounce,
  generateId,
  isEmpty,
} from './utils'

describe('Class Name Utilities', () => {
  describe('cn', () => {
    it('should merge class names', () => {
      const result = cn('class1', 'class2')
      expect(result).toContain('class1')
      expect(result).toContain('class2')
    })

    it('should handle conditional classes', () => {
      const result = cn('base', true && 'active', false && 'disabled')
      expect(result).toContain('base')
      expect(result).toContain('active')
      expect(result).not.toContain('disabled')
    })

    it('should handle Tailwind conflicts', () => {
      const result = cn('p-4', 'p-8')
      // Should only have p-8 (later value wins)
      expect(result).toContain('p-8')
    })

    it('should handle empty inputs', () => {
      expect(cn()).toBe('')
      expect(cn('')).toBe('')
    })

    it('should handle arrays', () => {
      const result = cn(['class1', 'class2'])
      expect(result).toContain('class1')
      expect(result).toContain('class2')
    })
  })
})

describe('Date Formatting', () => {
  describe('formatDate', () => {
    it('should format Date object', () => {
      const date = new Date('2024-01-15')
      const result = formatDate(date)
      
      expect(result).toContain('January')
      expect(result).toContain('15')
      expect(result).toContain('2024')
    })

    it('should format date string', () => {
      const result = formatDate('2024-01-15')
      
      expect(result).toContain('January')
      expect(result).toContain('15')
      expect(result).toContain('2024')
    })

    it('should handle ISO date strings', () => {
      const result = formatDate('2024-06-30T12:00:00Z')
      
      expect(result).toContain('June')
      expect(result).toContain('30')
      expect(result).toContain('2024')
    })
  })

  describe('formatDateTime', () => {
    it('should format Date object with time', () => {
      const date = new Date('2024-01-15T14:30:00')
      const result = formatDateTime(date)
      
      expect(result).toContain('January')
      expect(result).toContain('15')
      expect(result).toContain('2024')
      expect(result).toMatch(/\d{2}:\d{2}/)
    })

    it('should format date string with time', () => {
      const result = formatDateTime('2024-01-15T14:30:00')
      
      expect(result).toContain('January')
      expect(result).toMatch(/\d{2}:\d{2}/)
    })

    it('should handle midnight', () => {
      const date = new Date('2024-01-15T00:00:00')
      const result = formatDateTime(date)
      
      expect(result).toContain('January')
      expect(result).toContain('15')
    })
  })
})

describe('String Utilities', () => {
  describe('truncate', () => {
    it('should truncate long strings', () => {
      const text = 'This is a very long string'
      const result = truncate(text, 10)
      
      expect(result).toBe('This is a ...')
      expect(result.length).toBe(13)
    })

    it('should not truncate short strings', () => {
      const text = 'Short'
      const result = truncate(text, 10)
      
      expect(result).toBe('Short')
    })

    it('should handle exact length', () => {
      const text = 'Exactly10!'
      const result = truncate(text, 10)
      
      expect(result).toBe('Exactly10!')
    })

    it('should handle empty string', () => {
      expect(truncate('', 10)).toBe('')
    })

    it('should handle zero length', () => {
      const result = truncate('test', 0)
      expect(result).toBe('...')
    })

    it('should handle unicode characters', () => {
      const text = '这是一个很长的字符串'
      const result = truncate(text, 5)
      
      expect(result).toBe('这是一个很...')
    })
  })
})

describe('Async Utilities', () => {
  describe('sleep', () => {
    it('should delay execution', async () => {
      const start = Date.now()
      await sleep(100)
      const end = Date.now()
      
      expect(end - start).toBeGreaterThanOrEqual(90)
    })

    it('should handle zero delay', async () => {
      const start = Date.now()
      await sleep(0)
      const end = Date.now()
      
      expect(end - start).toBeLessThan(50)
    })

    it('should return a promise', () => {
      const result = sleep(10)
      expect(result).toBeInstanceOf(Promise)
    })
  })
})

describe('File Size Formatting', () => {
  describe('formatFileSize', () => {
    it('should format bytes', () => {
      expect(formatFileSize(0)).toBe('0 Bytes')
      expect(formatFileSize(500)).toBe('500 Bytes')
      expect(formatFileSize(1023)).toBe('1023 Bytes')
    })

    it('should format kilobytes', () => {
      expect(formatFileSize(1024)).toBe('1 KB')
      expect(formatFileSize(1536)).toBe('1.5 KB')
      expect(formatFileSize(10240)).toBe('10 KB')
    })

    it('should format megabytes', () => {
      expect(formatFileSize(1048576)).toBe('1 MB')
      expect(formatFileSize(5242880)).toBe('5 MB')
    })

    it('should format gigabytes', () => {
      expect(formatFileSize(1073741824)).toBe('1 GB')
      expect(formatFileSize(5368709120)).toBe('5 GB')
    })

    it('should format terabytes', () => {
      expect(formatFileSize(1099511627776)).toBe('1 TB')
    })

    it('should handle decimal places', () => {
      expect(formatFileSize(1536)).toBe('1.5 KB')
      expect(formatFileSize(1638400)).toBe('1.56 MB')
    })

    it('should handle very large numbers', () => {
      const result = formatFileSize(9999999999999)
      expect(result).toContain('TB')
    })
  })
})

describe('Function Utilities', () => {
  describe('debounce', () => {
    beforeEach(() => {
      vi.useFakeTimers()
    })

    afterEach(() => {
      vi.restoreAllMocks()
    })

    it('should debounce function calls', () => {
      const fn = vi.fn()
      const debounced = debounce(fn, 100)
      
      debounced()
      debounced()
      debounced()
      
      expect(fn).not.toHaveBeenCalled()
      
      vi.advanceTimersByTime(100)
      
      expect(fn).toHaveBeenCalledTimes(1)
    })

    it('should pass arguments to debounced function', () => {
      const fn = vi.fn()
      const debounced = debounce(fn, 100)
      
      debounced('arg1', 'arg2')
      vi.advanceTimersByTime(100)
      
      expect(fn).toHaveBeenCalledWith('arg1', 'arg2')
    })

    it('should reset timer on subsequent calls', () => {
      const fn = vi.fn()
      const debounced = debounce(fn, 100)
      
      debounced()
      vi.advanceTimersByTime(50)
      debounced()
      vi.advanceTimersByTime(50)
      
      expect(fn).not.toHaveBeenCalled()
      
      vi.advanceTimersByTime(50)
      
      expect(fn).toHaveBeenCalledTimes(1)
    })

    it('should handle multiple debounced functions', () => {
      const fn1 = vi.fn()
      const fn2 = vi.fn()
      const debounced1 = debounce(fn1, 100)
      const debounced2 = debounce(fn2, 50)
      
      debounced1()
      debounced2()
      
      vi.advanceTimersByTime(50)
      expect(fn2).toHaveBeenCalledTimes(1)
      expect(fn1).not.toHaveBeenCalled()
      
      vi.advanceTimersByTime(50)
      expect(fn1).toHaveBeenCalledTimes(1)
    })
  })
})

describe('ID Generation', () => {
  describe('generateId', () => {
    it('should generate unique IDs', () => {
      const id1 = generateId()
      const id2 = generateId()
      
      expect(id1).not.toBe(id2)
    })

    it('should generate strings', () => {
      const id = generateId()
      expect(typeof id).toBe('string')
    })

    it('should generate IDs of consistent length', () => {
      const ids = Array.from({ length: 100 }, () => generateId())
      const lengths = ids.map(id => id.length)
      
      expect(Math.max(...lengths)).toBe(Math.min(...lengths))
    })

    it('should generate alphanumeric IDs', () => {
      const id = generateId()
      expect(id).toMatch(/^[a-z0-9]+$/)
    })
  })
})

describe('Value Checking', () => {
  describe('isEmpty', () => {
    it('should return true for null', () => {
      expect(isEmpty(null)).toBe(true)
    })

    it('should return true for undefined', () => {
      expect(isEmpty(undefined)).toBe(true)
    })

    it('should return true for empty string', () => {
      expect(isEmpty('')).toBe(true)
      expect(isEmpty('   ')).toBe(true)
    })

    it('should return false for non-empty string', () => {
      expect(isEmpty('text')).toBe(false)
      expect(isEmpty(' a ')).toBe(false)
    })

    it('should return true for empty array', () => {
      expect(isEmpty([])).toBe(true)
    })

    it('should return false for non-empty array', () => {
      expect(isEmpty([1, 2, 3])).toBe(false)
      expect(isEmpty([''])).toBe(false)
    })

    it('should return true for empty object', () => {
      expect(isEmpty({})).toBe(true)
    })

    it('should return false for non-empty object', () => {
      expect(isEmpty({ key: 'value' })).toBe(false)
      expect(isEmpty({ a: undefined })).toBe(false)
    })

    it('should return false for numbers', () => {
      expect(isEmpty(0)).toBe(false)
      expect(isEmpty(42)).toBe(false)
      expect(isEmpty(-1)).toBe(false)
    })

    it('should return false for boolean', () => {
      expect(isEmpty(false)).toBe(false)
      expect(isEmpty(true)).toBe(false)
    })

    it('should handle nested structures', () => {
      expect(isEmpty({ nested: {} })).toBe(false)
      expect(isEmpty([[], []])).toBe(false)
    })
  })
})