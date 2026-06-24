# AGENTS.md

## Project Overview

This project is planned as a backend service for generating product listing images for pet merchandise.

The service will support workflows for creating, preparing, and managing listing-ready visuals for pet products such as toys, food, accessories, grooming items, apparel, and related goods. Its backend responsibilities may include accepting product metadata and source assets, coordinating image generation or enhancement jobs, storing generation results, tracking job status, and exposing APIs that can be consumed by internal tools or frontend applications.

The intended goal is to help sellers and operators produce consistent, high-quality, marketplace-ready product images with less manual design work.

The `doc/domain/` directory describes the business domains and domain concepts intended to be implemented in this project. Treat the materials in that directory as planning and domain reference for future implementation work.

## Command Running Rules

- Use a local virtual environment for project work, preferably the `.venv` environment managed by `uv`.
- Run Python commands through `uv run`, for example `uv run python script.py` or `uv run pytest`.
- Do not run project Python scripts directly with global Python commands such as `python3 script.py`.
