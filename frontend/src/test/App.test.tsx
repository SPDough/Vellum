import { describe, it, expect } from 'vitest'

describe('App Tests', () => {
  it('basic math test', () => {
    expect(2 + 2).toBe(4)
  })

  it('string test', () => {
    expect('hello').toBe('hello')
  })
})