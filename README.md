# Generative AI

A collection of Python demonstrations exploring practical AI, Natural Language Processing (NLP), and high-throughput spatiotemporal data pipelines.

## Overview

This repository contains two standalone Python scripts showcasing distinct applied AI and data-engineering workflows:

1. **`plagiarism_ai_detector_demo.py`** — An NLP analysis tool that detects text similarity (plagiarism) using TF-IDF vectorization and Cosine Similarity, alongside a heuristic AI-text detector based on Shannon entropy (perplexity) and sentence-length variance (burstiness).
2. **`generative_ai_demo.py`** — An asynchronous spatiotemporal telemetry ingestion and spatial indexing benchmark utilizing Uber's H3 hexagonal hierarchical spatial index (v4 API), RAM pre-index caching, and PyTorch zero-copy shared memory allocation (`share_memory_()`).

---

## Repository Structure

```text
generative-ai/
├── plagiarism_ai_detector_demo.py   # Plagiarism & heuristic AI-content detection
├── generative_ai_demo.py            # Async multi-city H3 spatial indexing & PyTorch IPC benchmark
└── README.md                        # Project documentation
