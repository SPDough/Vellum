# Generalized Integration Architecture

This directory contains the reusable provider framework for external custodian,
OMS, accounting, and related enterprise integrations.

## Layers

### `base/`
Provider-agnostic framework primitives:
- provider contract
- auth abstraction
- HTTP client scaffold
- exceptions
- registry
- tooling metadata
- pagination helpers

### `domain/`
Canonical normalized Vellum domain models.
These are provider-independent shapes used to normalize raw vendor payloads.

### `providers/`
Concrete provider implementations.

### `registry/`
Product-facing registration and dispatch helpers.

### `contracts/`
Lightweight loader/registry utilities for the repo-level JSON contract registry.

## Current provider #1
- `state_street`

## Design rule
The framework should remain provider-agnostic. Provider-specific logic belongs in
`providers/<provider_name>/`, while normalized domain models belong in `domain/`.
