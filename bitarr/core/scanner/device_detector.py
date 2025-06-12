"""
Storage device detection for Bitarr.
"""
import os
import re
import subprocess
from pathlib import Path
from typing import Dict, List, Optional
from .file_utils import get_storage_device_info

class DeviceDetector:
    """
    Detects and provides information about storage devices.
    """
    
    def __init__(self):
        """
        Initialize the device detector.
        """
        self.devices = {}
    
    def detect_devices(self) -> List[Dict]:
        """
        Detect all storage devices.

        Returns:
            List[Dict]: List of storage device information dictionaries
        """
        devices = []

        # List of filesystem types to exclude
        exclude_fs_types = [
            'proc', 'sysfs', 'devpts', 'cgroup', 'tmpfs', 'securityfs',
            'fusectl', 'debugfs', 'configfs', 'hugetlbfs', 'mqueue',
            'pstore', 'efivarfs', 'fuse.snapfuse', 'fuse.gvfsd-fuse',
            'squashfs', 'nsfs', 'binfmt_misc', 'rpc_pipefs', 'devtmpfs'
        ]

        # List of mount point prefixes to exclude
        exclude_mount_prefixes = [
            '/proc', '/sys', '/dev', '/run', '/snap', '/boot',
            '/opt/piavpn', '/var/snap', '/run/snapd'
        ]

        # Try to get information from /proc/mounts
        if os.path.exists('/proc/mounts'):
            with open('/proc/mounts', 'r') as f:
                mounts = f.readlines()

            for mount in mounts:
                parts = mount.split()
                if len(parts) >= 4:  # Ensure we have enough parts to check filesystem type
                    device_id, mount_point, fs_type = parts[0], parts[1], parts[2]

                    # Skip virtual and system filesystems
                    if fs_type in exclude_fs_types:
                        continue

                    # Skip specific mount points
                    if any(mount_point.startswith(prefix) for prefix in exclude_mount_prefixes):
                        continue

                    # Skip loopback devices (snap packages)
                    if 'loop' in device_id:
                        continue

                    # Skip rootfs duplicate
                    if device_id == 'rootfs':
                        continue

                    # Get device info
                    if os.path.exists(mount_point) and os.access(mount_point, os.R_OK):
                        try:
                            device_info = get_storage_device_info(mount_point)
                            device_info.update({
                                "name": self._get_device_name(device_id, mount_point, fs_type),
                                "mount_point": mount_point,
                                "device_id": device_id,
                                "fs_type": fs_type
                            })
                            devices.append(device_info)
                        except Exception as e:
                            print(f"Error getting info for {mount_point}: {str(e)}")

        # Run lsblk command if available (Linux)
        try:
            result = subprocess.run(
                ['lsblk', '-o', 'NAME,SIZE,TYPE,MOUNTPOINT', '-J'],
                capture_output=True, text=True, check=True
            )
            import json
            lsblk_data = json.loads(result.stdout)

            # Process lsblk output to enhance device info
            if 'blockdevices' in lsblk_data:
                for device in devices:
                    for blk_device in lsblk_data['blockdevices']:
                        if device['device_id'].endswith(blk_device['name']):
                            device['size_human'] = blk_device.get('size', 'Unknown')
                            device['type'] = blk_device.get('type', 'Unknown')
        except (subprocess.SubprocessError, json.JSONDecodeError, FileNotFoundError):
            # lsblk not available or failed
            pass

        return devices

    def get_device_by_path(self, path: str) -> Optional[Dict]:
        """
        Get the storage device information for a path.
        
        Args:
            path: Path to check
        
        Returns:
            Dict: Storage device information or None if not found
        """
        path_obj = Path(path)
        if not path_obj.exists():
            return None
        
        # Get all devices
        devices = self.detect_devices()
        
        # Find the device with the most specific mount point
        matching_devices = []
        for device in devices:
            if path.startswith(device['mount_point']):
                matching_devices.append(device)
        
        if not matching_devices:
            return None
        
        # Return the device with the longest mount point path
        return sorted(matching_devices, key=lambda d: len(d['mount_point']), reverse=True)[0]
    
    def _get_device_name(self, device_id: str, mount_point: str, fs_type: str = None) -> str:
        """
        Generate a friendly name for a device.

        Args:
            device_id: Device identifier
            mount_point: Mount point path
            fs_type: Filesystem type

        Returns:
            str: Friendly device name
        """
        # For network shares, use the server name
        if 'nfs' in device_id or '//' in device_id or '192.168.' in device_id:
            match = re.search(r'//([^/]+)|(\d+\.\d+\.\d+\.\d+)', device_id)
            if match:
                server = match.group(1) or match.group(2)
                return f"Network Share ({server}) - {mount_point}"
            return f"Network Share - {mount_point}"

        # For standard block devices
        if '/dev/' in device_id:
            device_type = "Storage"

            # Try to determine if it's an SSD or HDD
            if 'nvme' in device_id:
                device_type = "Internal SSD"
            elif 'sd' in device_id:
                # Try to determine if it's external
                if self._is_likely_external(device_id):
                    device_type = "External Drive"
                else:
                    device_type = "Internal HDD"

            # Include filesystem type if available
            fs_info = f" ({fs_type})" if fs_type else ""

            # Make mount point more readable
            display_mount = mount_point
            if mount_point == '/':
                display_mount = "Root"
            elif mount_point == '/home':
                display_mount = "Home"

            return f"{device_type}{fs_info} - {display_mount}"

        # For root or home directories, use standard names
        if mount_point == '/':
            return f"Root Filesystem{' (' + fs_type + ')' if fs_type else ''}"
        elif mount_point == '/home':
            return f"Home Directory{' (' + fs_type + ')' if fs_type else ''}"

        # Default: use the mount point
        return f"Storage - {mount_point}{' (' + fs_type + ')' if fs_type else ''}"
    
    def _is_likely_external(self, device_id: str) -> bool:
        """
        Check if a device is likely to be external.
        
        Args:
            device_id: Device identifier
        
        Returns:
            bool: True if likely external, False otherwise
        """
        # Try to determine by checking for USB in the sysfs path
        try:
            dev_name = os.path.basename(device_id)
            if not dev_name.startswith('sd'):
                return False
            
            # Check if the device is connected via USB
            for path in [f'/sys/block/{dev_name}/device/driver']:
                if os.path.exists(path):
                    try:
                        real_path = os.path.realpath(path)
                        return 'usb' in real_path.lower()
                    except OSError:
                        pass
        except Exception:
            pass
        
        return False
