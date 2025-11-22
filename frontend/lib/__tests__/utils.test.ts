import { cn, formatCurrency, formatDate, formatDateTime } from '../utils'

describe('Utils', () => {
  describe('cn', () => {
    it('should merge class names correctly', () => {
      const result = cn('px-2', 'py-1')
      expect(result).toBe('px-2 py-1')
    })

    it('should handle conditional class names', () => {
      const isActive = true
      const result = cn('base-class', isActive && 'active-class')
      expect(result).toBe('base-class active-class')
    })

    it('should handle tailwind conflicts', () => {
      const result = cn('px-2', 'px-4')
      expect(result).toBe('px-4')
    })

    it('should handle arrays', () => {
      const result = cn(['px-2', 'py-1'], 'mt-2')
      expect(result).toBe('px-2 py-1 mt-2')
    })

    it('should handle objects', () => {
      const result = cn({ 'px-2': true, 'py-1': false, 'mt-2': true })
      expect(result).toBe('px-2 mt-2')
    })

    it('should handle undefined and null', () => {
      const result = cn('px-2', undefined, null, 'py-1')
      expect(result).toBe('px-2 py-1')
    })
  })

  describe('formatCurrency', () => {
    it('should format positive numbers correctly', () => {
      expect(formatCurrency(100)).toBe('R$ 100,00')
      expect(formatCurrency(1234.56)).toBe('R$ 1.234,56')
      expect(formatCurrency(1000000)).toBe('R$ 1.000.000,00')
    })

    it('should format zero correctly', () => {
      expect(formatCurrency(0)).toBe('R$ 0,00')
    })

    it('should format negative numbers correctly', () => {
      expect(formatCurrency(-50)).toBe('-R$ 50,00')
      expect(formatCurrency(-1234.56)).toBe('-R$ 1.234,56')
    })

    it('should handle decimal numbers', () => {
      expect(formatCurrency(99.99)).toBe('R$ 99,99')
      expect(formatCurrency(0.5)).toBe('R$ 0,50')
      expect(formatCurrency(0.01)).toBe('R$ 0,01')
    })

    it('should round to 2 decimal places', () => {
      expect(formatCurrency(10.999)).toBe('R$ 11,00')
      expect(formatCurrency(10.995)).toBe('R$ 11,00')
    })
  })

  describe('formatDate', () => {
    it('should format Date object correctly', () => {
      const date = new Date('2025-11-22T10:30:00')
      const result = formatDate(date)

      // The exact format depends on locale, but should contain the date
      expect(result).toMatch(/22\/11\/2025/)
    })

    it('should format date string correctly', () => {
      const result = formatDate('2025-11-22')
      expect(result).toMatch(/22\/11\/2025/)
    })

    it('should handle ISO date strings', () => {
      const result = formatDate('2025-11-22T10:30:00.000Z')
      expect(result).toMatch(/22\/11\/2025/)
    })

    it('should format different dates correctly', () => {
      expect(formatDate('2025-01-01')).toMatch(/01\/01\/2025/)
      expect(formatDate('2025-12-31')).toMatch(/31\/12\/2025/)
    })
  })

  describe('formatDateTime', () => {
    it('should format Date object with time', () => {
      const date = new Date('2025-11-22T14:30:00')
      const result = formatDateTime(date)

      // Should contain both date and time
      expect(result).toMatch(/22\/11\/2025/)
      expect(result).toMatch(/14:30/)
    })

    it('should format date string with time', () => {
      const result = formatDateTime('2025-11-22T14:30:00')

      expect(result).toMatch(/22\/11\/2025/)
      expect(result).toMatch(/14:30/)
    })

    it('should handle midnight correctly', () => {
      const result = formatDateTime('2025-11-22T00:00:00')

      expect(result).toMatch(/22\/11\/2025/)
      expect(result).toMatch(/00:00/)
    })

    it('should handle noon correctly', () => {
      const result = formatDateTime('2025-11-22T12:00:00')

      expect(result).toMatch(/22\/11\/2025/)
      expect(result).toMatch(/12:00/)
    })

    it('should format different times correctly', () => {
      expect(formatDateTime('2025-01-01T09:15:00')).toMatch(/01\/01\/2025/)
      expect(formatDateTime('2025-12-31T23:59:00')).toMatch(/31\/12\/2025/)
    })
  })
})
