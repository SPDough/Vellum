import { describe, it, expect } from 'vitest'

describe('Component Tests', () => {
  it('basic component test', () => {
    expect('component').toBe('component')
  })

  it('array test', () => {
    const arr = [1, 2, 3]
    expect(arr).toHaveLength(3)
  })
})