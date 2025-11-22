import React from 'react'
import { render, screen, fireEvent } from '@/__tests__/test-utils'
import { Input } from '../input'

describe('Input', () => {
  it('should render correctly', () => {
    render(<Input placeholder="Enter text" />)

    const input = screen.getByPlaceholderText('Enter text')
    expect(input).toBeInTheDocument()
  })

  it('should handle text input', () => {
    const handleChange = jest.fn()
    render(<Input onChange={handleChange} />)

    const input = screen.getByRole('textbox')
    fireEvent.change(input, { target: { value: 'test value' } })

    expect(handleChange).toHaveBeenCalled()
    expect(input).toHaveValue('test value')
  })

  it('should support different input types', () => {
    const { rerender } = render(<Input type="email" data-testid="input" />)
    expect(screen.getByTestId('input')).toHaveAttribute('type', 'email')

    rerender(<Input type="password" data-testid="input" />)
    expect(screen.getByTestId('input')).toHaveAttribute('type', 'password')

    rerender(<Input type="number" data-testid="input" />)
    expect(screen.getByTestId('input')).toHaveAttribute('type', 'number')
  })

  it('should be disabled when disabled prop is true', () => {
    render(<Input disabled placeholder="Disabled input" />)

    const input = screen.getByPlaceholderText('Disabled input')
    expect(input).toBeDisabled()
  })

  it('should apply custom className', () => {
    render(<Input className="custom-input" data-testid="input" />)

    expect(screen.getByTestId('input')).toHaveClass('custom-input')
  })

  it('should forward ref correctly', () => {
    const ref = React.createRef<HTMLInputElement>()
    render(<Input ref={ref} />)

    expect(ref.current).toBeInstanceOf(HTMLInputElement)
  })

  it('should handle default value', () => {
    render(<Input defaultValue="default text" data-testid="input" />)

    expect(screen.getByTestId('input')).toHaveValue('default text')
  })

  it('should handle controlled value', () => {
    const { rerender } = render(<Input value="initial" onChange={() => {}} />)
    expect(screen.getByRole('textbox')).toHaveValue('initial')

    rerender(<Input value="updated" onChange={() => {}} />)
    expect(screen.getByRole('textbox')).toHaveValue('updated')
  })

  it('should have correct accessibility attributes', () => {
    render(
      <Input
        aria-label="Search"
        aria-required="true"
        aria-invalid="true"
        placeholder="Search..."
      />
    )

    const input = screen.getByLabelText('Search')
    expect(input).toHaveAttribute('aria-required', 'true')
    expect(input).toHaveAttribute('aria-invalid', 'true')
  })
})
