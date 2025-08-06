import React from 'react'
import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'

// Test a simple component to ensure React testing works
function WelcomeMessage({ name }: { name: string }) {
  return <h1>Welcome, {name}!</h1>
}

// Test a button component with event handling
function ClickCounter() {
  const [count, setCount] = React.useState(0)
  
  return (
    <div>
      <p>Count: {count}</p>
      <button onClick={() => setCount(count + 1)}>
        Increment
      </button>
    </div>
  )
}

describe('Component Tests', () => {
  it('renders welcome message with name', () => {
    render(<WelcomeMessage name="John" />)
    expect(screen.getByText('Welcome, John!')).toBeInTheDocument()
  })

  it('renders counter with initial count', () => {
    render(<ClickCounter />)
    expect(screen.getByText('Count: 0')).toBeInTheDocument()
    expect(screen.getByText('Increment')).toBeInTheDocument()
  })

  it('increments counter when button is clicked', async () => {
    const userEvent = await import('@testing-library/user-event')
    const user = userEvent.default.setup()
    
    render(<ClickCounter />)
    
    const button = screen.getByText('Increment')
    await user.click(button)
    
    expect(screen.getByText('Count: 1')).toBeInTheDocument()
  })
})