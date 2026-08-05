"""Project-wide error hierarchy.

A single small typed exception hierarchy under one project base error,
per the Architecture Spine's Consistency Conventions — not one bespoke
exception class per value object.
"""


class LabyrinthesError(Exception):
    """Base class for every error raised by the `labyrinthes` project."""


class DomainValidationError(LabyrinthesError):
    """Raised when a domain value object is constructed with invalid data."""
