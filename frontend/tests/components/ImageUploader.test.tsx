import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '../setup/test-utils'
import ImageUploader from '../../src/components/ImageUploader'
import * as apiModule from '../../src/lib/api-client'

// jsdom does not implement URL.createObjectURL / revokeObjectURL
let objectUrlCounter = 0
globalThis.URL.createObjectURL = vi.fn(() => `blob:mock/${++objectUrlCounter}`)
globalThis.URL.revokeObjectURL = vi.fn()

const mockUploadImages = vi.fn()
vi.spyOn(apiModule.apiClient, 'uploadImages').mockImplementation(mockUploadImages)

function createMockFile(name: string, type = 'image/png', sizeKb = 1): File {
  const bytes = new Uint8Array(sizeKb * 1024)
  return new File([bytes], name, { type })
}

describe('ImageUploader', () => {
  beforeEach(() => {
    mockUploadImages.mockClear()
    objectUrlCounter = 0
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  it('renders the drop zone', () => {
    render(<ImageUploader />)
    expect(screen.getByText(/drag and drop/i)).toBeInTheDocument()
    expect(screen.getByText(/click to browse/i)).toBeInTheDocument()
  })

  it('adds file previews on selection', async () => {
    render(<ImageUploader />)
    const input = screen.getByTestId('file-input')
    const file = createMockFile('photo.png')

    fireEvent.change(input, { target: { files: [file] } })

    await waitFor(() => {
      expect(screen.getByText('photo.png')).toBeInTheDocument()
    })
  })

  it('shows upload button when files are selected', async () => {
    render(<ImageUploader />)
    const input = screen.getByTestId('file-input')
    fireEvent.change(input, { target: { files: [createMockFile('a.png')] } })

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /upload/i })).toBeInTheDocument()
    })
  })

  it('removes a preview when remove button is clicked', async () => {
    render(<ImageUploader />)
    const input = screen.getByTestId('file-input')
    fireEvent.change(input, { target: { files: [createMockFile('a.png')] } })

    await waitFor(() => expect(screen.getByText('a.png')).toBeInTheDocument())

    const removeBtn = screen.getByLabelText(/remove/i)
    fireEvent.click(removeBtn)

    await waitFor(() => {
      expect(screen.queryByText('a.png')).not.toBeInTheDocument()
    })
  })

  it('rejects files exceeding max count', async () => {
    render(<ImageUploader maxFiles={1} />)
    const input = screen.getByTestId('file-input')
    const files = [createMockFile('a.png'), createMockFile('b.png')]

    fireEvent.change(input, { target: { files } })

    await waitFor(() => {
      expect(screen.getByRole('alert')).toBeInTheDocument()
    })
  })

  it('rejects unsupported file types', async () => {
    render(<ImageUploader />)
    const input = screen.getByTestId('file-input')
    const pdfFile = createMockFile('doc.pdf', 'application/pdf')

    fireEvent.change(input, { target: { files: [pdfFile] } })

    await waitFor(() => {
      expect(screen.getByRole('alert')).toBeInTheDocument()
    })
  })

  it('calls apiClient.uploadImages and shows success', async () => {
    mockUploadImages.mockResolvedValueOnce({
      images: [
        { image_id: 'uuid-1', serving_url: '/api/v1/images/uuid-1', filename: 'photo.png', size_bytes: 1024 },
      ],
    })

    const onComplete = vi.fn()
    render(<ImageUploader onUploadComplete={onComplete} />)

    const input = screen.getByTestId('file-input')
    fireEvent.change(input, { target: { files: [createMockFile('photo.png')] } })

    await waitFor(() => screen.getByRole('button', { name: /upload/i }))
    fireEvent.click(screen.getByRole('button', { name: /upload/i }))

    await waitFor(() => {
      expect(mockUploadImages).toHaveBeenCalledTimes(1)
      expect(screen.getByText(/uploaded successfully/i)).toBeInTheDocument()
      expect(onComplete).toHaveBeenCalledWith([
        expect.objectContaining({ image_id: 'uuid-1' }),
      ])
    })
  })

  it('shows error message on upload failure', async () => {
    mockUploadImages.mockRejectedValueOnce(new Error('Network error'))

    render(<ImageUploader />)
    const input = screen.getByTestId('file-input')
    fireEvent.change(input, { target: { files: [createMockFile('photo.png')] } })

    await waitFor(() => screen.getByRole('button', { name: /upload/i }))
    fireEvent.click(screen.getByRole('button', { name: /upload/i }))

    await waitFor(() => {
      expect(screen.getByRole('alert')).toBeInTheDocument()
      expect(screen.getByText(/network error/i)).toBeInTheDocument()
    })
  })

  it('disables interaction when disabled prop is set', () => {
    render(<ImageUploader disabled />)
    const input = screen.getByTestId('file-input') as HTMLInputElement
    expect(input.disabled).toBe(true)
  })
})
