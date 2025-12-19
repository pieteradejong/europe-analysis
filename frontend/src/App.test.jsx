import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import App from './App'

// Mock fetch for API calls
const mockFetch = vi.fn()
global.fetch = mockFetch

// Helper to create successful API responses
const createSuccessResponse = (data) => ({
  ok: true,
  json: () => Promise.resolve(data),
})

// Standard mock responses
const mockStatsResponse = {
  total_sources: 2,
  total_regions: 5,
  demographics: {
    total_records: 1000,
    years_covered: '2020-2023',
  },
  industrial: {
    total_records: 500,
    years_covered: '2020-2023',
    nace_codes: ['B-D', 'C'],
  },
}

const mockRegionsResponse = {
  regions: [
    { id: 1, code: 'DE', name: 'Germany', level: 'country' },
    { id: 2, code: 'FR', name: 'France', level: 'country' },
    { id: 3, code: 'IT', name: 'Italy', level: 'country' },
  ],
}

const mockSourcesResponse = {
  sources: [
    { id: 1, name: 'Eurostat Population', type: 'api', last_updated: '2023-12-01T00:00:00Z' },
    { id: 2, name: 'Eurostat Industrial', type: 'api', last_updated: '2023-12-15T00:00:00Z' },
  ],
}

const mockDemographicsResponse = {
  count: 3,
  data: [
    { id: 1, year: 2023, age_min: 0, age_max: 5, gender: 'M', population: 2000000 },
    { id: 2, year: 2023, age_min: 0, age_max: 5, gender: 'F', population: 1900000 },
    { id: 3, year: 2023, age_min: 5, age_max: 10, gender: 'M', population: 2100000 },
  ],
}

const mockIndustrialResponse = {
  count: 3,
  data: [
    { id: 1, year: 2023, month: 10, nace_code: 'B-D', index_value: 98 },
    { id: 2, year: 2023, month: 11, nace_code: 'B-D', index_value: 97 },
    { id: 3, year: 2023, month: 12, nace_code: 'C', index_value: 95 },
  ],
}

// Setup mock fetch implementation
const setupMockFetch = (overrides = {}) => {
  mockFetch.mockImplementation((url) => {
    if (url.includes('/stats')) {
      return Promise.resolve(createSuccessResponse(overrides.stats || mockStatsResponse))
    }
    if (url.includes('/regions')) {
      return Promise.resolve(createSuccessResponse(overrides.regions || mockRegionsResponse))
    }
    if (url.includes('/sources')) {
      return Promise.resolve(createSuccessResponse(overrides.sources || mockSourcesResponse))
    }
    if (url.includes('/demographics')) {
      return Promise.resolve(createSuccessResponse(overrides.demographics || mockDemographicsResponse))
    }
    if (url.includes('/industrial')) {
      return Promise.resolve(createSuccessResponse(overrides.industrial || mockIndustrialResponse))
    }
    return Promise.reject(new Error(`Unknown URL: ${url}`))
  })
}

describe('App', () => {
  beforeEach(() => {
    mockFetch.mockReset()
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  describe('Loading State', () => {
    it('renders loading state initially', () => {
      // Mock fetch to never resolve (stay in loading)
      mockFetch.mockImplementation(() => new Promise(() => {}))

      render(<App />)
      expect(screen.getByText('Loading European Data...')).toBeInTheDocument()
    })

    it('shows spinner during loading', () => {
      mockFetch.mockImplementation(() => new Promise(() => {}))

      render(<App />)
      expect(document.querySelector('.spinner')).toBeInTheDocument()
    })
  })

  describe('Error State', () => {
    it('displays error state when API fails', async () => {
      mockFetch.mockRejectedValue(new Error('Network error'))

      render(<App />)

      await waitFor(() => {
        expect(screen.getByText('⚠️ Connection Error')).toBeInTheDocument()
      })
    })

    it('displays error message from API failure', async () => {
      mockFetch.mockRejectedValue(new Error('Connection refused'))

      render(<App />)

      await waitFor(() => {
        expect(screen.getByText('Connection refused')).toBeInTheDocument()
      })
    })

    it('shows retry button on error', async () => {
      mockFetch.mockRejectedValue(new Error('Network error'))

      render(<App />)

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /retry/i })).toBeInTheDocument()
      })
    })

    it('handles non-ok response status', async () => {
      mockFetch.mockImplementation(() =>
        Promise.resolve({
          ok: false,
          status: 500,
          json: () => Promise.resolve({ error: 'Server error' }),
        })
      )

      render(<App />)

      await waitFor(() => {
        expect(screen.getByText('⚠️ Connection Error')).toBeInTheDocument()
      })
    })
  })

  describe('Successful Load', () => {
    it('renders the heading after data loads', async () => {
      setupMockFetch()

      render(<App />)

      await waitFor(() => {
        expect(screen.getByText('🇪🇺 Europe Analysis')).toBeInTheDocument()
      })
    })

    it('renders subtitle', async () => {
      setupMockFetch()

      render(<App />)

      await waitFor(() => {
        expect(
          screen.getByText('Explore demographic and industrial data across European regions')
        ).toBeInTheDocument()
      })
    })

    it('renders tab navigation', async () => {
      setupMockFetch()

      render(<App />)

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Demographics/i })).toBeInTheDocument()
        expect(screen.getByRole('button', { name: /Industry/i })).toBeInTheDocument()
      })
    })
  })

  describe('Statistics Display', () => {
    it('displays total sources count', async () => {
      setupMockFetch()

      render(<App />)

      await waitFor(() => {
        expect(screen.getByText('2')).toBeInTheDocument()
        expect(screen.getByText('Data Sources')).toBeInTheDocument()
      })
    })

    it('displays total regions count', async () => {
      setupMockFetch()

      render(<App />)

      await waitFor(() => {
        expect(screen.getByText('5')).toBeInTheDocument()
        expect(screen.getByText('Regions')).toBeInTheDocument()
      })
    })

    it('displays demographic data points in demographics tab', async () => {
      setupMockFetch()

      render(<App />)

      await waitFor(() => {
        expect(screen.getByText('1,000')).toBeInTheDocument()
        expect(screen.getByText('Demo Data Points')).toBeInTheDocument()
      })
    })

    it('displays years covered', async () => {
      setupMockFetch()

      render(<App />)

      await waitFor(() => {
        expect(screen.getByText('2020-2023')).toBeInTheDocument()
      })
    })
  })

  describe('Tab Navigation', () => {
    it('demographics tab is active by default', async () => {
      setupMockFetch()

      render(<App />)

      await waitFor(() => {
        const demoTab = screen.getByRole('button', { name: /Demographics/i })
        expect(demoTab).toHaveClass('active')
      })
    })

    it('can switch to industry tab', async () => {
      setupMockFetch()

      render(<App />)

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Industry/i })).toBeInTheDocument()
      })

      fireEvent.click(screen.getByRole('button', { name: /Industry/i }))

      expect(screen.getByRole('button', { name: /Industry/i })).toHaveClass('active')
      expect(screen.getByRole('button', { name: /Demographics/i })).not.toHaveClass('active')
    })

    it('shows industrial stats when industry tab is active', async () => {
      setupMockFetch()

      render(<App />)

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Industry/i })).toBeInTheDocument()
      })

      fireEvent.click(screen.getByRole('button', { name: /Industry/i }))

      await waitFor(() => {
        expect(screen.getByText('500')).toBeInTheDocument()
        expect(screen.getByText('Industrial Data Points')).toBeInTheDocument()
      })
    })
  })

  describe('Regions Panel', () => {
    it('displays regions list', async () => {
      setupMockFetch()

      render(<App />)

      await waitFor(() => {
        expect(screen.getByText('Germany')).toBeInTheDocument()
        expect(screen.getByText('France')).toBeInTheDocument()
        expect(screen.getByText('Italy')).toBeInTheDocument()
      })
    })

    it('displays region codes', async () => {
      setupMockFetch()

      render(<App />)

      await waitFor(() => {
        expect(screen.getByText('DE')).toBeInTheDocument()
        expect(screen.getByText('FR')).toBeInTheDocument()
        expect(screen.getByText('IT')).toBeInTheDocument()
      })
    })

    it('shows search input', async () => {
      setupMockFetch()

      render(<App />)

      await waitFor(() => {
        expect(screen.getByPlaceholderText('Search regions...')).toBeInTheDocument()
      })
    })

    it('filters regions by search query', async () => {
      setupMockFetch()

      render(<App />)

      await waitFor(() => {
        expect(screen.getByText('Germany')).toBeInTheDocument()
      })

      const searchInput = screen.getByPlaceholderText('Search regions...')
      fireEvent.change(searchInput, { target: { value: 'Germany' } })

      expect(screen.getByText('Germany')).toBeInTheDocument()
      expect(screen.queryByText('France')).not.toBeInTheDocument()
      expect(screen.queryByText('Italy')).not.toBeInTheDocument()
    })

    it('filters regions by code', async () => {
      setupMockFetch()

      render(<App />)

      await waitFor(() => {
        expect(screen.getByText('Germany')).toBeInTheDocument()
      })

      const searchInput = screen.getByPlaceholderText('Search regions...')
      fireEvent.change(searchInput, { target: { value: 'DE' } })

      expect(screen.getByText('Germany')).toBeInTheDocument()
      expect(screen.queryByText('France')).not.toBeInTheDocument()
    })

    it('shows empty state when no regions match search', async () => {
      setupMockFetch()

      render(<App />)

      await waitFor(() => {
        expect(screen.getByText('Germany')).toBeInTheDocument()
      })

      const searchInput = screen.getByPlaceholderText('Search regions...')
      fireEvent.change(searchInput, { target: { value: 'xyz' } })

      expect(screen.getByText('No regions match your search.')).toBeInTheDocument()
    })
  })

  describe('Demographics Tab Content', () => {
    it('shows prompt to select region initially', async () => {
      setupMockFetch()

      render(<App />)

      await waitFor(() => {
        expect(screen.getByText('Select a region to view demographic data.')).toBeInTheDocument()
      })
    })

    it('fetches demographics when region is selected', async () => {
      setupMockFetch()

      render(<App />)

      await waitFor(() => {
        expect(screen.getByText('Germany')).toBeInTheDocument()
      })

      // Click on Germany region
      fireEvent.click(screen.getByText('Germany'))

      // Should have fetched demographics
      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining('/api/data/demographics?region_code=DE')
        )
      })
    })

    it('displays demographic data table', async () => {
      setupMockFetch()

      render(<App />)

      await waitFor(() => {
        expect(screen.getByText('Germany')).toBeInTheDocument()
      })

      // Click the button containing Germany
      const germanyButton = screen.getByText('Germany').closest('button')
      fireEvent.click(germanyButton)

      await waitFor(() => {
        // Table headers
        expect(screen.getByText('Year')).toBeInTheDocument()
        expect(screen.getByText('Age Range')).toBeInTheDocument()
        expect(screen.getByText('Gender')).toBeInTheDocument()
        expect(screen.getByText('Population')).toBeInTheDocument()
      })
    })

    it('formats population with locale string', async () => {
      setupMockFetch()

      render(<App />)

      await waitFor(() => {
        expect(screen.getByText('Germany')).toBeInTheDocument()
      })

      fireEvent.click(screen.getByText('Germany'))

      await waitFor(() => {
        expect(screen.getByText('2,000,000')).toBeInTheDocument()
      })
    })
  })

  describe('Industry Tab Content', () => {
    it('shows prompt to select region in industry tab', async () => {
      setupMockFetch()

      render(<App />)

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Industry/i })).toBeInTheDocument()
      })

      fireEvent.click(screen.getByRole('button', { name: /Industry/i }))

      expect(screen.getByText('Select a region to view industrial production data.')).toBeInTheDocument()
    })

    it('fetches industrial data when region is selected', async () => {
      setupMockFetch()

      render(<App />)

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Industry/i })).toBeInTheDocument()
      })

      fireEvent.click(screen.getByRole('button', { name: /Industry/i }))
      fireEvent.click(screen.getByText('Germany'))

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining('/api/data/industrial?region_code=DE')
        )
      })
    })

    it('displays industrial data table', async () => {
      setupMockFetch()

      render(<App />)

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Industry/i })).toBeInTheDocument()
      })

      fireEvent.click(screen.getByRole('button', { name: /Industry/i }))
      fireEvent.click(screen.getByText('Germany'))

      await waitFor(() => {
        // Table headers should appear
        expect(screen.getByText('Month')).toBeInTheDocument()
        expect(screen.getByText('Industry')).toBeInTheDocument()
        expect(screen.getByText('Index (2015=100)')).toBeInTheDocument()
      })
    })

    it('formats month names correctly', async () => {
      setupMockFetch()

      render(<App />)

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Industry/i })).toBeInTheDocument()
      })

      fireEvent.click(screen.getByRole('button', { name: /Industry/i }))
      fireEvent.click(screen.getByText('Germany'))

      await waitFor(() => {
        expect(screen.getByText('Oct')).toBeInTheDocument()
        expect(screen.getByText('Nov')).toBeInTheDocument()
        expect(screen.getByText('Dec')).toBeInTheDocument()
      })
    })
  })

  describe('Data Sources Panel', () => {
    it('displays data sources', async () => {
      setupMockFetch()

      render(<App />)

      await waitFor(() => {
        expect(screen.getByText('📁 Data Sources')).toBeInTheDocument()
        expect(screen.getByText('Eurostat Population')).toBeInTheDocument()
        expect(screen.getByText('Eurostat Industrial')).toBeInTheDocument()
      })
    })

    it('displays source types', async () => {
      setupMockFetch()

      render(<App />)

      await waitFor(() => {
        const apiLabels = screen.getAllByText('api')
        expect(apiLabels.length).toBe(2)
      })
    })

    it('shows empty state when no sources', async () => {
      setupMockFetch({ sources: { sources: [] } })

      render(<App />)

      await waitFor(() => {
        expect(
          screen.getByText('No data sources configured. Use the API to acquire data.')
        ).toBeInTheDocument()
      })
    })
  })

  describe('Empty States', () => {
    it('shows empty state when no regions available', async () => {
      setupMockFetch({ regions: { regions: [] } })

      render(<App />)

      await waitFor(() => {
        expect(
          screen.getByText('No regions available. Import data to get started.')
        ).toBeInTheDocument()
      })
    })

    it('shows empty demographic data state', async () => {
      setupMockFetch({ demographics: { count: 0, data: [] } })

      render(<App />)

      await waitFor(() => {
        expect(screen.getByText('Germany')).toBeInTheDocument()
      })

      fireEvent.click(screen.getByText('Germany'))

      await waitFor(() => {
        expect(
          screen.getByText('No demographic data available for this region.')
        ).toBeInTheDocument()
      })
    })

    it('shows empty industrial data state', async () => {
      setupMockFetch({ industrial: { count: 0, data: [] } })

      render(<App />)

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Industry/i })).toBeInTheDocument()
      })

      fireEvent.click(screen.getByRole('button', { name: /Industry/i }))
      fireEvent.click(screen.getByText('Germany'))

      await waitFor(() => {
        expect(
          screen.getByText('No industrial data available for this region.')
        ).toBeInTheDocument()
      })
    })
  })

  describe('Region Selection', () => {
    it('highlights selected region', async () => {
      setupMockFetch()

      render(<App />)

      await waitFor(() => {
        expect(screen.getByText('Germany')).toBeInTheDocument()
      })

      const germanyButton = screen.getByText('Germany').closest('button')
      fireEvent.click(germanyButton)

      expect(germanyButton).toHaveClass('selected')
    })

    it('can change selected region', async () => {
      setupMockFetch()

      render(<App />)

      await waitFor(() => {
        expect(screen.getByText('Germany')).toBeInTheDocument()
      })

      // Select Germany
      fireEvent.click(screen.getByText('Germany').closest('button'))

      // Select France
      fireEvent.click(screen.getByText('France').closest('button'))

      const franceButton = screen.getByText('France').closest('button')
      expect(franceButton).toHaveClass('selected')

      const germanyButton = screen.getByText('Germany').closest('button')
      expect(germanyButton).not.toHaveClass('selected')
    })
  })

  describe('Footer', () => {
    it('renders footer with API link', async () => {
      setupMockFetch()

      render(<App />)

      await waitFor(() => {
        const link = screen.getByRole('link', { name: /localhost:8000\/docs/i })
        expect(link).toBeInTheDocument()
        expect(link).toHaveAttribute('href', 'http://localhost:8000/docs')
      })
    })
  })
})
