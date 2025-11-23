import { apiClient } from '@/lib/api-client'

// Mock fetch
global.fetch = jest.fn()

describe('ApiClient', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    // Clear localStorage
    localStorage.clear()
  })

  describe('Authentication', () => {
    it('should set and store authentication token', () => {
      const token = 'test-token-123'
      apiClient.setToken(token)

      expect(localStorage.getItem('auth_token')).toBe(token)
    })

    it('should include auth token in request headers', async () => {
      const token = 'test-token-123'
      apiClient.setToken(token)

      const mockResponse = { data: 'test' }
      ;(global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      })

      await apiClient.get('/test')

      expect(global.fetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          headers: expect.objectContaining({
            Authorization: `Bearer ${token}`,
          }),
        })
      )
    })

    it('should clear token', () => {
      apiClient.setToken('test-token')
      apiClient.clearToken()

      expect(localStorage.getItem('auth_token')).toBeNull()
    })
  })

  describe('HTTP Methods', () => {
    it('should make GET request', async () => {
      const mockData = { id: 1, name: 'Test' }
      ;(global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockData,
      })

      const result = await apiClient.get('/test')

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/test'),
        expect.objectContaining({
          method: 'GET',
        })
      )
      expect(result).toEqual(mockData)
    })

    it('should make POST request with data', async () => {
      const mockData = { id: 1, name: 'Created' }
      const postData = { name: 'New Item' }

      ;(global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockData,
      })

      const result = await apiClient.post('/test', postData)

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/test'),
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify(postData),
        })
      )
      expect(result).toEqual(mockData)
    })

    it('should make PUT request', async () => {
      const mockData = { id: 1, name: 'Updated' }
      const putData = { name: 'Updated Item' }

      ;(global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockData,
      })

      const result = await apiClient.put('/test/1', putData)

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/test/1'),
        expect.objectContaining({
          method: 'PUT',
          body: JSON.stringify(putData),
        })
      )
      expect(result).toEqual(mockData)
    })

    it('should make DELETE request', async () => {
      ;(global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ message: 'Deleted' }),
      })

      const result = await apiClient.delete('/test/1')

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/test/1'),
        expect.objectContaining({
          method: 'DELETE',
        })
      )
      expect(result).toEqual({ message: 'Deleted' })
    })
  })

  describe('Error Handling', () => {
    it('should throw error for non-ok response', async () => {
      ;(global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        status: 404,
        statusText: 'Not Found',
        json: async () => ({ detail: 'Resource not found' }),
      })

      await expect(apiClient.get('/test')).rejects.toThrow()
    })

    it('should include error details in thrown error', async () => {
      const errorDetail = 'Validation failed'
      ;(global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        status: 400,
        statusText: 'Bad Request',
        json: async () => ({ detail: errorDetail }),
      })

      try {
        await apiClient.get('/test')
        fail('Should have thrown error')
      } catch (error: any) {
        expect(error.detail).toBe(errorDetail)
        expect(error.status).toBe(400)
      }
    })

    it('should handle network errors', async () => {
      ;(global.fetch as jest.Mock).mockRejectedValueOnce(
        new Error('Network error')
      )

      await expect(apiClient.get('/test')).rejects.toThrow('Network error')
    })
  })

  describe('Content-Type', () => {
    it('should set Content-Type to application/json', async () => {
      ;(global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({}),
      })

      await apiClient.post('/test', { data: 'test' })

      expect(global.fetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
          }),
        })
      )
    })
  })
})
