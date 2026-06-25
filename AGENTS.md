# AGENTS.md

## Project Overview

This project is planned as a backend service for generating product listing images for pet merchandise.

The service will support workflows for creating, preparing, and managing listing-ready visuals for pet products such as toys, food, accessories, grooming items, apparel, and related goods. Its backend responsibilities may include accepting product metadata and source assets, coordinating image generation or enhancement jobs, storing generation results, tracking job status, and exposing APIs that can be consumed by internal tools or frontend applications.

The intended goal is to help sellers and operators produce consistent, high-quality, marketplace-ready product images with less manual design work.

The `doc/domain/` directory describes the business domains and domain concepts intended to be implemented in this project. Treat the materials in that directory as planning and domain reference for future implementation work.

## Project Rules

- Use `.venv` / `uv` for the project environment. Python scripts, tests, and project commands must run through `uv run ...`; do not use global `python` / `python3` directly.
- Business code must use `may_backend.logger` for logging. Before adding or changing log calls, read `doc/domain/logger/usage.md`.

## Test Commands

- Run all tests: `uv run pytest`
- Run logger tests: `uv run pytest tests/logger`

## Code Style Guidelines

### Type Annotations

- New functions must include type annotations.
- Public functions and application use cases must annotate parameters and return values. Avoid `Any` where a concrete type is reasonable.
- Do not use bare `dict` / `list` for complex business objects; prefer dataclasses or Pydantic models.

### Comment Style

- Do not explain self-evident code.
- Add short comments for complex business rules.
- Public APIs, domain models, and important use cases may use docstrings.
- Explain why, not what the code already says.
