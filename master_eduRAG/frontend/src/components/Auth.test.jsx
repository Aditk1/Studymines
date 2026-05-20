/**
 * Component tests for the authentication screen.
 */
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import axios from 'axios'
import Auth from './Auth'

vi.mock('axios', () => ({
  default: {
    post: vi.fn()
  }
}))

vi.mock('../supabase', () => ({
  supabase: {}
}))

describe('Auth', () => {
  it('logs in with email and password', async () => {
    const onLogin = vi.fn()
    axios.post.mockResolvedValueOnce({
      data: {
        success: true,
        access_token: 'token',
        user: { id: 'u1', email: 'ada@example.edu', role: 'student' }
      }
    })

    render(<Auth onLogin={onLogin} />)
    await userEvent.type(screen.getByPlaceholderText(/institutional email/i), 'ada@example.edu')
    await userEvent.type(screen.getByPlaceholderText(/archive passcode/i), 'secret')
    await userEvent.click(screen.getByRole('button', { name: /access archive/i }))

    await waitFor(() => expect(onLogin).toHaveBeenCalledWith(
      expect.objectContaining({ email: 'ada@example.edu' }),
      'token'
    ))
  })

  it('shows an error when login fails', async () => {
    axios.post.mockRejectedValueOnce({ response: { data: { error: 'Invalid email or password' } } })

    render(<Auth onLogin={vi.fn()} />)
    await userEvent.type(screen.getByPlaceholderText(/institutional email/i), 'bad@example.edu')
    await userEvent.type(screen.getByPlaceholderText(/archive passcode/i), 'wrong')
    await userEvent.click(screen.getByRole('button', { name: /access archive/i }))

    expect(await screen.findByText(/invalid email or password/i)).toBeInTheDocument()
  })

  it('switches to signup and submits role and level fields', async () => {
    const onLogin = vi.fn()
    axios.post.mockResolvedValueOnce({
      data: {
        success: true,
        access_token: 'signup-token',
        user: { id: 'u2', email: 'teacher@example.edu', role: 'teacher' }
      }
    })

    render(<Auth onLogin={onLogin} />)
    await userEvent.click(screen.getByRole('button', { name: /no credentials/i }))
    await userEvent.type(screen.getByPlaceholderText(/scholar name/i), 'Professor Ada')
    await userEvent.click(screen.getByRole('button', { name: /^teacher$/i }))
    await userEvent.type(screen.getByPlaceholderText(/institutional email/i), 'teacher@example.edu')
    await userEvent.type(screen.getByPlaceholderText(/archive passcode/i), 'secret')
    await userEvent.click(screen.getByRole('button', { name: /create credentials/i }))

    await waitFor(() => expect(onLogin).toHaveBeenCalled())
  })
})
