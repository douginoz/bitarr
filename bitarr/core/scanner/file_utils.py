"""
File utilities for Bitarr scanner.
"""
import os
import stat
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Generator

def get_file_metadata(file_path: str) -> Dict:
    """
    Get metadata for a file.
    
    Args:
        file_path: Path to the file
    
    Returns:
        Dict: File metadata including size, last_modified, and file_type
    """
    try:
        file_stat = os.stat(file_path)
        file_type = determine_file_type(file_path)
        
        return {
            "size": file_stat.st_size,
            "last_modified": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(file_stat.st_mtime)),
            "file_type": file_type,
            "is_directory": stat.S_ISDIR(file_stat.st_mode),
            "is_file": stat.S_ISREG(file_stat.st_mode),
            "is_symlink": stat.S_ISLNK(file_stat.st_mode),
            "permissions": stat.filemode(file_stat.st_mode)
        }
    except (OSError, PermissionError, FileNotFoundError):
        return {
            "size": 0,
            "last_modified": None,
            "file_type": None,
            "is_directory": False,
            "is_file": False,
            "is_symlink": False,
            "permissions": None
        }

def determine_file_type(file_path: str) -> str:
    """
    Determine file type based on extension.
    
    Args:
        file_path: Path to the file
    
    Returns:
        str: File type or "unknown"
    """
    extension = Path(file_path).suffix.lower()
    
    # Common file type mappings
    type_map = {
        # Documents
        '.txt': 'text',
        '.pdf': 'pdf',
        '.doc': 'word',
        '.docx': 'word',
        '.xls': 'excel',
        '.xlsx': 'excel',
        '.ppt': 'powerpoint',
        '.pptx': 'powerpoint',
        
        # Images
        '.jpg': 'image',
        '.jpeg': 'image',
        '.png': 'image',
        '.gif': 'image',
        '.bmp': 'image',
        '.svg': 'image',
        '.webp': 'image',
        
        # Audio
        '.mp3': 'audio',
        '.wav': 'audio',
        '.ogg': 'audio',
        '.flac': 'audio',
        '.aac': 'audio',
        
        # Video
        '.mp4': 'video',
        '.avi': 'video',
        '.mkv': 'video',
        '.mov': 'video',
        '.wmv': 'video',
        
        # Archives
        '.zip': 'archive',
        '.rar': 'archive',
        '.7z': 'archive',
        '.tar': 'archive',
        '.gz': 'archive',
        
        # Programming
        '.py': 'code',
        '.js': 'code',
        '.html': 'code',
        '.css': 'code',
        '.java': 'code',
        '.cpp': 'code',
        '.c': 'code',
        '.php': 'code',
        '.go': 'code',
        '.rb': 'code',
        
        # System
        '.exe': 'executable',
        '.dll': 'library',
        '.so': 'library',
        '.sys': 'system',
        '.conf': 'config',
        '.log': 'log',
        '.db': 'database',
        '.sqlite': 'database',
    }
    
    return type_map.get(extension, "unknown")

def walk_directory(
    top_dir: str,
    exclude_dirs: List[str] = None,
    exclude_patterns: List[str] = None,
    max_depth: int = None
) -> Generator[str, None, None]:
    """
    Walk a directory recursively and yield file paths.

    Args:
        top_dir: Top-level directory to start walking from
        exclude_dirs: List of directory names to exclude
        exclude_patterns: List of glob patterns to exclude
        max_depth: Maximum depth to traverse

    Yields:
        str: Absolute file path
    """
    exclude_dirs = exclude_dirs or []
    exclude_patterns = exclude_patterns or []

    top_dir_path = Path(top_dir)
    if not top_dir_path.exists() or not top_dir_path.is_dir():
        print(f"Error: {top_dir} is not a valid directory")
        return

    # Walk the directory
    for root, dirs, files in os.walk(top_dir):
        # Calculate current depth
        rel_path = os.path.relpath(root, top_dir)
        current_depth = 0 if rel_path == '.' else len(rel_path.split(os.sep))

        # Check max depth
        if max_depth is not None and current_depth >= max_depth:
            dirs.clear()  # Don't go deeper
            continue

        # Exclude directories (in-place to avoid traversing them)
        dirs[:] = [d for d in dirs if d not in exclude_dirs]

        # Process files
        for file in files:
            file_path = os.path.join(root, file)

            # Check exclude patterns
            exclude_file = False
            for pattern in exclude_patterns:
                if Path(file_path).match(pattern):
                    exclude_file = True
                    break

            if exclude_file:
                continue

            yield file_path

def get_storage_device_info(path: str) -> Dict:
    """
    Get information about the storage device containing the path.
    
    Args:
        path: Path to check
    
    Returns:
        Dict: Storage device information
    """
    try:
        path_obj = Path(path)
        if not path_obj.exists():
            return {"error": "Path does not exist"}
        
        # Get disk usage statistics
        usage = os.statvfs(path)
        total_size = usage.f_frsize * usage.f_blocks
        free_size = usage.f_frsize * usage.f_bfree
        used_size = total_size - free_size
        
        # Try to determine device type (basic detection)
        device_type = "unknown"
        mount_point = "/"
        device_id = None
        
        # On Linux, we can read /proc/mounts for more information
        if os.path.exists('/proc/mounts'):
            with open('/proc/mounts', 'r') as f:
                mounts = f.readlines()
            
            # Find the mount point that is a parent of the path
            mount_points = []
            for mount in mounts:
                parts = mount.split()
                if len(parts) >= 2:
                    device, mount_point = parts[0], parts[1]
                    if path.startswith(mount_point):
                        mount_points.append((mount_point, device))
            
            # Get the most specific mount point (longest path)
            if mount_points:
                mount_points.sort(key=lambda x: len(x[0]), reverse=True)
                mount_point, device_id = mount_points[0]
                
                # Determine device type
                if 'tmpfs' in device_id:
                    device_type = 'tmpfs'
                elif 'loop' in device_id:
                    device_type = 'loopback'
                elif 'nfs' in device_id:
                    device_type = 'network'
                elif '/dev/sd' in device_id:
                    device_type = 'internal_hdd'
                elif '/dev/nvme' in device_id:
                    device_type = 'internal_ssd'
        
        return {
            "mount_point": mount_point,
            "device_type": device_type,
            "device_id": device_id,
            "total_size": total_size,
            "used_size": used_size,
            "free_size": free_size,
            "usage_percent": (used_size / total_size) * 100 if total_size > 0 else 0
        }
    except Exception as e:
        return {
            "error": f"Failed to get storage device info: {str(e)}",
            "mount_point": "/",
            "device_type": "unknown",
            "device_id": None,
            "total_size": 0,
            "used_size": 0,
            "free_size": 0,
            "usage_percent": 0
        }

def split_path_components(file_path: str) -> Tuple[str, str, str]:
    """
    Split a file path into directory, filename, and path.
    
    Args:
        file_path: Path to split
    
    Returns:
        Tuple: (directory, filename, path)
    """
    path_obj = Path(file_path)
    directory = str(path_obj.parent)
    filename = path_obj.name
    path = str(path_obj)
    
    return directory, filename, path
