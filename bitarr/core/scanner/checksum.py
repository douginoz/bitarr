"""
Checksum calculation utilities for Bitarr.
"""
import os
import hashlib
from typing import BinaryIO, Callable, Dict, Optional

# Try to import optional dependencies gracefully
try:
    import xxhash
    XXHASH_AVAILABLE = True
except ImportError:
    XXHASH_AVAILABLE = False

try:
    import blake3
    BLAKE3_AVAILABLE = True
except ImportError:
    BLAKE3_AVAILABLE = False

# Define supported checksum algorithms and their functions
CHECKSUM_ALGORITHMS = {
    "md5": lambda: hashlib.md5(),
    "sha1": lambda: hashlib.sha1(),
    "sha256": lambda: hashlib.sha256(),
    "sha512": lambda: hashlib.sha512(),
    "blake2b": lambda: hashlib.blake2b(),
}

# Add optional algorithms if libraries are available
if XXHASH_AVAILABLE:
    CHECKSUM_ALGORITHMS["xxhash64"] = lambda: xxhash.xxh64()

if BLAKE3_AVAILABLE:
    CHECKSUM_ALGORITHMS["blake3"] = lambda: blake3.blake3()

class ChecksumCalculator:
    """
    Handles checksum calculation for files using various algorithms.
    """

    def __init__(self, algorithm: str = "sha256", block_size_mb: int = 4):
        """
        Initialize the checksum calculator.

        Args:
            algorithm: Checksum algorithm to use (md5, sha1, sha256, sha512, xxhash64, blake2b, blake3)
            block_size_mb: Size of blocks to read in MB

        Raises:
            ValueError: If algorithm is not supported
        """
        if algorithm not in CHECKSUM_ALGORITHMS:
            supported = ", ".join(CHECKSUM_ALGORITHMS.keys())
            raise ValueError(f"Unsupported checksum algorithm: {algorithm}. Supported algorithms: {supported}")

        self.algorithm = algorithm
        self.block_size = block_size_mb * 1024 * 1024  # Convert MB to bytes

    def calculate_file_checksum(self, file_path: str) -> Optional[str]:
        """
        Calculate checksum for a file.

        Args:
            file_path: Path to the file

        Returns:
            str: Hexadecimal checksum string or None if file is not accessible
        """
        try:
            with open(file_path, "rb") as f:
                return self.calculate_stream_checksum(f)
        except (IOError, PermissionError, FileNotFoundError) as e:
            print(f"Error calculating checksum for {file_path}: {str(e)}")
            return None

    def calculate_stream_checksum(self, stream: BinaryIO) -> str:
        """
        Calculate checksum for a binary stream.

        Args:
            stream: Binary stream to read from

        Returns:
            str: Hexadecimal checksum string
        """
        hasher = CHECKSUM_ALGORITHMS[self.algorithm]()

        # Read and update the hash in blocks
        while True:
            data = stream.read(self.block_size)
            if not data:
                break
            hasher.update(data)

        return hasher.hexdigest()

    def calculate_string_checksum(self, text: str) -> str:
        """
        Calculate checksum for a string.

        Args:
            text: String to calculate checksum for

        Returns:
            str: Hexadecimal checksum string
        """
        hasher = CHECKSUM_ALGORITHMS[self.algorithm]()
        hasher.update(text.encode('utf-8'))
        return hasher.hexdigest()

    @staticmethod
    def get_supported_algorithms() -> list:
        """
        Get a list of supported checksum algorithms.

        Returns:
            list: List of supported algorithm names
        """
        return list(CHECKSUM_ALGORITHMS.keys())

    @staticmethod
    def algorithm_info() -> Dict[str, Dict[str, str]]:
        """
        Get information about supported algorithms.

        Returns:
            Dict: Dictionary with algorithm information
        """
        info = {
            "md5": {
                "description": "Fast, but cryptographically broken",
                "speed": "Very fast",
                "security": "Low",
                "recommendation": "Not recommended for security purposes"
            },
            "sha1": {
                "description": "Older algorithm with known weaknesses",
                "speed": "Fast",
                "security": "Medium-Low",
                "recommendation": "Not recommended for security purposes"
            },
            "sha256": {
                "description": "Secure hash algorithm (SHA-2 family)",
                "speed": "Medium",
                "security": "High",
                "recommendation": "Good balance of security and speed"
            },
            "sha512": {
                "description": "Secure hash algorithm with larger output (SHA-2 family)",
                "speed": "Medium",
                "security": "Very High",
                "recommendation": "Good for high-security needs"
            },
            "blake2b": {
                "description": "Modern cryptographic hash function",
                "speed": "Fast",
                "security": "High",
                "recommendation": "Good balance of speed and security"
            }
        }

        # Add optional algorithms if available
        if XXHASH_AVAILABLE:
            info["xxhash64"] = {
                "description": "Extremely fast non-cryptographic hash function",
                "speed": "Extremely Fast",
                "security": "Low (not cryptographic)",
                "recommendation": "Best for performance-critical scanning"
            }

        if BLAKE3_AVAILABLE:
            info["blake3"] = {
                "description": "Latest generation hash function",
                "speed": "Very Fast",
                "security": "High",
                "recommendation": "Best balance of speed and security"
            }

        return info
