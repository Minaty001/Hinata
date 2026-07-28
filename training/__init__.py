"""
Hinata - Training & Data Pipeline Package

Implements the auto-training pipeline: every interaction is encoded as a
structured training sample, embedded into vectors, and fed into the
continuous learning system.

Sub-packages:
- formats/      — JSON schemas for training data
- *.py          — Pipeline stages (encoder, embedder, scorer, ...)
"""
