"""System utility helper functions for the CardioLab platform.

This module provides support services such as verifying model file paths on the local system.
"""

from pathlib import Path
from typing import Optional


def verify_model_files(model_file: Optional[str], protocol_file: Optional[str]) -> bool:
    """Verifies whether the required Myokit model and protocol files exist on disk.

    Args:
        model_file: Absolute path to the .mmt model file.
        protocol_file: Absolute path to the .mmt protocol file.

    Returns:
        True if both files are configured and exist, False otherwise.
    """
    if not model_file or not protocol_file:
        return False
    return Path(model_file).exists() and Path(protocol_file).exists()
