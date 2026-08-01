"""
Version Metadata Manager for Pi Arcade OS.

Stores version constants, build identifier, author credits, and release information.
Supports Python 3.9+ typing.
"""

VERSION: str = "1.0.0"
BUILD: str = "2026.08.01-RC1"
AUTHOR: str = "Hector Pacheco"
RELEASE_DATE: str = "August 2026"
OS_NAME: str = "Pi Arcade OS"
DESCRIPTION: str = "Embedded Retro Arcade Operating System for Raspberry Pi 5"


def get_version_info() -> str:
    """Returns formatted version string."""
    return f"{OS_NAME} v{VERSION} (Build {BUILD}) by {AUTHOR}"
