# Vellum Contract Loader Utility

This module provides a lightweight programmatic interface to the repo-level
`contracts/` registry.

## Purpose
- load versioned contract schemas
- load short dictionary metadata
- load optional FIBO alignment metadata
- expose standardized result-envelope helpers for provider-backed tools
- avoid heavyweight registry infrastructure early

## Current approach
The contract registry is file-based and code-managed.
This keeps it simple, reviewable, and implementable for the current stage of Vellum.
