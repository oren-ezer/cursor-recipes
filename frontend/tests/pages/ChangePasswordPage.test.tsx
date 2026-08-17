import { render, screen, fireEvent, waitFor } from '../setup/test-utils'
import ChangePasswordPage from '../../src/pages/ChangePasswordPage'
import { vi } from 'vitest'
import { apiClient } from '../../src/lib/api-client'
import { useNavigate } from 'react-router-dom'

// Mock react-router-dom hooks
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useNavigate: vi.fn()
  }
})

vi.mock('../../src/lib/api-client', () => ({
  apiClient: {
    changePassword: vi.fn()
  },
  ApiError: class ApiError extends Error {
    constructor(message: string) {
      super(message);
      this.name = 'ApiError';
    }
  }
}))

describe('ChangePasswordPage', () => {
  const mockNavigate = vi.fn()
  
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(useNavigate).mockReturnValue(mockNavigate)
    vi.mocked(apiClient.changePassword).mockResolvedValue(undefined)
  })

  it('renders correctly', () => {
    render(<ChangePasswordPage />)
    expect(screen.getAllByText('Change Password')[0]).toBeInTheDocument()
    expect(screen.getByLabelText(/Current Password/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/^New Password/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/Confirm New Password/i)).toBeInTheDocument()
  })

  it('shows error if passwords do not match', async () => {
    render(<ChangePasswordPage />)
    
    fireEvent.change(screen.getByLabelText(/Current Password/i), { target: { value: 'oldpass' } })
    fireEvent.change(screen.getByLabelText(/^New Password/i), { target: { value: 'newpass123!' } })
    fireEvent.change(screen.getByLabelText(/Confirm New Password/i), { target: { value: 'wrongpass!' } })
    
    fireEvent.click(screen.getByRole('button', { name: 'Change Password' }))
    
    expect(screen.getByText('New passwords do not match.')).toBeInTheDocument()
    expect(apiClient.changePassword).not.toHaveBeenCalled()
  })

  it('calls API and redirects on success', async () => {
    render(<ChangePasswordPage />)
    
    fireEvent.change(screen.getByLabelText(/Current Password/i), { target: { value: 'oldpass' } })
    fireEvent.change(screen.getByLabelText(/^New Password/i), { target: { value: 'Newpass123!' } })
    fireEvent.change(screen.getByLabelText(/Confirm New Password/i), { target: { value: 'Newpass123!' } })
    
    fireEvent.click(screen.getByRole('button', { name: 'Change Password' }))
    
    await waitFor(() => {
      expect(apiClient.changePassword).toHaveBeenCalledWith('oldpass', 'Newpass123!')
    })
    
    expect(mockNavigate).toHaveBeenCalledWith('/', {
      state: {
        message: expect.any(String)
      }
    })
  })

  it('shows error message if API fails', async () => {
    // Need to use the mocked ApiError class from the api-client mock
    const { ApiError } = await import('../../src/lib/api-client')
    vi.mocked(apiClient.changePassword).mockRejectedValueOnce(new ApiError('Invalid current password'))
    
    render(<ChangePasswordPage />)
    
    fireEvent.change(screen.getByLabelText(/Current Password/i), { target: { value: 'wrongoldpass' } })
    fireEvent.change(screen.getByLabelText(/^New Password/i), { target: { value: 'Newpass123!' } })
    fireEvent.change(screen.getByLabelText(/Confirm New Password/i), { target: { value: 'Newpass123!' } })
    
    fireEvent.click(screen.getByRole('button', { name: 'Change Password' }))
    
    await waitFor(() => {
      expect(screen.getByText('Invalid current password')).toBeInTheDocument()
    })
  })
})
