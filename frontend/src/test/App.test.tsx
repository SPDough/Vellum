import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'

// Simple test component
function TestComponent() {
  return <div>Hello Test World</div>
}

describe('App Tests', () => {
  it('renders test component', () => {
    render(<TestComponent />)
    expect(screen.getByText('Hello Test World')).toBeInTheDocument()
  })

  it('basic math test', () => {
    expect(2 + 2).toBe(4)
  })
})