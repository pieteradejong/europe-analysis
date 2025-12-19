import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import App from './App'

// Mock fetch for API calls
const mockFetch = vi.fn()
global.fetch = mockFetch

describe('App', () => {
  beforeEach(() => {
    mockFetch.mockReset()
  })

  it('renders loading state initially', () => {
    // Mock fetch to never resolve (stay in loading)
    mockFetch.mockImplementation(() => new Promise(() => {}))
    
    render(<App />)
    expect(screen.getByText('Loading European Data...')).toBeInTheDocument()
  })

  it('renders the heading after data loads', async () => {
    // Mock successful API responses
    mockFetch.mockImplementation((url) => {
      if (url.includes('/stats')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ total_sources: 0, total_regions: 0 })
        })
      }
      if (url.includes('/regions')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ regions: [] })
        })
      }
      if (url.includes('/sources')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ sources: [] })
        })
      }
      return Promise.reject(new Error('Unknown URL'))
    })

    render(<App />)
    
    await waitFor(() => {
      expect(screen.getByText('🇪🇺 Europe Analysis')).toBeInTheDocument()
    })
  })

  it('renders tab navigation', async () => {
    mockFetch.mockImplementation((url) => {
      if (url.includes('/stats')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ total_sources: 0, total_regions: 0 })
        })
      }
      if (url.includes('/regions')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ regions: [] })
        })
      }
      if (url.includes('/sources')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ sources: [] })
        })
      }
      return Promise.reject(new Error('Unknown URL'))
    })

    render(<App />)
    
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /Demographics/i })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /Industry/i })).toBeInTheDocument()
    })
  })

  it('displays error state when API fails', async () => {
    mockFetch.mockRejectedValue(new Error('Network error'))

    render(<App />)
    
    await waitFor(() => {
      expect(screen.getByText('⚠️ Connection Error')).toBeInTheDocument()
    })
  })
})
