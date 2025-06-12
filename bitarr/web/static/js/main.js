// Main JavaScript for Bitarr

// Initialize socket connection
const socket = io();

// DOM elements
const menuToggle = document.getElementById('menuToggle');
const appNav = document.querySelector('.app-nav');
const newScanButton = document.getElementById('newScanButton');
const newScanModal = document.getElementById('newScanModal');
const activeScanModal = document.getElementById('activeScanModal');
const closeButtons = document.querySelectorAll('.close-button, .close-modal');
const newScanForm = document.getElementById('newScanForm');
const stopScanButton = document.getElementById('stopScanButton');

// Progress elements
const scanStatus = document.getElementById('scanStatus');
const scanPercentage = document.getElementById('scanPercentage');
const scanCurrentFile = document.getElementById('scanCurrentFile');
const scanFileCount = document.getElementById('scanFileCount');
const progressFill = document.querySelector('.progress-fill');

// Tracking active scan
let activeScanId = null;

// Toggle menu
menuToggle.addEventListener('click', () => {
    menuToggle.classList.toggle('active');
    appNav.classList.toggle('active');
    appNav.classList.toggle('collapsed');
});

// Show new scan modal
newScanButton.addEventListener('click', () => {
    newScanModal.classList.add('show');
});

// Close modals
closeButtons.forEach(button => {
    button.addEventListener('click', () => {
        newScanModal.classList.remove('show');
        activeScanModal.classList.remove('show');
    });
});

// Handle form submission
newScanForm.addEventListener('submit', (e) => {
    e.preventDefault();

    // Get form data
    const formData = new FormData(newScanForm);
    const data = {
        path: formData.get('path'),
        name: formData.get('name') || `Scan of ${formData.get('path')}`,
        checksum_method: formData.get('checksum_method'),
        threads: parseInt(formData.get('threads')) || 4
    };

    // Parse exclude dirs
    const excludeDirs = formData.get('exclude_dirs');
    if (excludeDirs) {
        data.exclude_dirs = excludeDirs.split(',').map(dir => dir.trim());
    }

    // Start scan
    fetch('/api/scan', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(result => {
        if (result.error) {
            alert(`Error: ${result.error}`);
            return;
        }

        // Close new scan modal
        newScanModal.classList.remove('show');

        // Reset progress
        updateProgress({
            status: 'starting',
            files_processed: 0,
            total_files: 0,
            percent_complete: 0
        });

        // Show active scan modal
        activeScanModal.classList.add('show');
    })
    .catch(error => {
        console.error('Error starting scan:', error);
        alert('Error starting scan. Please try again.');
    });
});

// Stop scan
stopScanButton.addEventListener('click', () => {
    if (activeScanId) {
        fetch(`/api/scan/${activeScanId}/stop`, {
            method: 'POST'
        })
        .then(response => response.json())
        .then(result => {
            console.log('Scan stopped:', result);
        })
        .catch(error => {
            console.error('Error stopping scan:', error);
        });
    } else {
        // Close modal if no active scan
        activeScanModal.classList.remove('show');
    }
});

// Socket events
socket.on('connect', () => {
    console.log('Connected to server');
});

socket.on('disconnect', () => {
    console.log('Disconnected from server');
});

socket.on('scan_progress', (data) => {
    console.log('Scan progress:', data);
    updateProgress(data);

    // Store active scan ID
    if (data.scan_id) {
        activeScanId = data.scan_id;
    }

    // Close modal if scan is completed or failed
    if (data.status === 'completed' || data.status === 'failed') {
        setTimeout(() => {
            activeScanModal.classList.remove('show');

            // Reload page if we're on scan history
            if (window.location.pathname.includes('scan_history')) {
                window.location.reload();
            }
        }, 2000);
    }
});

socket.on('scan_complete', (data) => {
    console.log('Scan complete:', data);

    // Close modal
    activeScanModal.classList.remove('show');

    // Show notification
    showNotification('Scan completed successfully', 'success');

    // Reload page if we're on scan history
    if (window.location.pathname.includes('scan_history')) {
        window.location.reload();
    }
});

socket.on('scan_error', (data) => {
    console.error('Scan error:', data);

    // Close modal
    activeScanModal.classList.remove('show');

    // Show notification
    showNotification(`Scan failed: ${data.error}`, 'error');
});

// Update progress display
function updateProgress(data) {
    // Update progress elements
    if (data.status === 'counting') {
        scanStatus.textContent = 'Counting files...';
        scanCurrentFile.textContent = data.current_path || '';
        scanFileCount.textContent = 'Calculating total files...';
        progressFill.style.width = '5%';
        scanPercentage.textContent = '5%';
    } else if (data.status === 'starting') {
        scanStatus.textContent = 'Starting scan...';
        scanCurrentFile.textContent = '';
        scanFileCount.textContent = `0 / ${data.total_files} files`;
        progressFill.style.width = '0%';
        scanPercentage.textContent = '0%';
    } else if (data.status === 'scanning') {
        scanStatus.textContent = 'Scanning...';
        scanCurrentFile.textContent = data.current_path || '';
        scanFileCount.textContent = `${data.files_processed} / ${data.total_files} files`;
        progressFill.style.width = `${data.percent_complete}%`;
        scanPercentage.textContent = `${Math.round(data.percent_complete)}%`;
    } else if (data.status === 'completed') {
        scanStatus.textContent = 'Scan completed';
        scanFileCount.textContent = `${data.files_processed} / ${data.total_files} files`;
        progressFill.style.width = '100%';
        scanPercentage.textContent = '100%';
    } else if (data.status === 'failed') {
        scanStatus.textContent = 'Scan failed';
        scanCurrentFile.textContent = data.error || 'Unknown error';
        progressFill.style.width = '100%';
        progressFill.style.backgroundColor = 'var(--danger-color)';
    }
}

// Show notification
function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `flash-message ${type}`;
    notification.textContent = message;

    // Add to container
    const container = document.querySelector('.flash-messages');
    if (container) {
        container.appendChild(notification);

        // Remove after 5 seconds
        setTimeout(() => {
            notification.remove();
        }, 5000);
    }
}

// Format file size
    if (bytes === 0) return '0 B';
function formatSize(bytes) {
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// Format timestamp as "time ago"
function formatTimeAgo(timestamp) {
    if (!timestamp) return 'Unknown';

    try {
        const date = new Date(timestamp);
        const now = new Date();
        const diff = now - date;

        if (diff < 60000) { // Less than 1 minute
            return 'Just now';
        } else if (diff < 3600000) { // Less than 1 hour
            const minutes = Math.floor(diff / 60000);
            return `${minutes} minute${minutes !== 1 ? 's' : ''} ago`;
        } else if (diff < 86400000) { // Less than 1 day
            const hours = Math.floor(diff / 3600000);
            return `${hours} hour${hours !== 1 ? 's' : ''} ago`;
        } else if (diff < 2592000000) { // Less than 30 days
            const days = Math.floor(diff / 86400000);
            return `${days} day${days !== 1 ? 's' : ''} ago`;
        } else {
            // Format as date
            const options = { year: 'numeric', month: 'short', day: 'numeric' };
            return date.toLocaleDateString(undefined, options);
        }
    } catch (e) {
        console.error('Error formatting date:', e);
        return timestamp;
    }
}

// Format file size
function formatFileSize(sizeInBytes) {
    if (!sizeInBytes) return '0 B';

    try {
        const sizeNumber = parseInt(sizeInBytes, 10);

        if (sizeNumber < 1024) {
            return `${sizeNumber} B`;
        } else if (sizeNumber < 1048576) { // 1024 * 1024
            return `${(sizeNumber / 1024).toFixed(1)} KB`;
        } else if (sizeNumber < 1073741824) { // 1024 * 1024 * 1024
            return `${(sizeNumber / 1048576).toFixed(1)} MB`;
        } else {
            return `${(sizeNumber / 1073741824).toFixed(1)} GB`;
        }
    } catch (e) {
        console.error('Error formatting file size:', e);
        return '0 B';
    }
}

// Open modal
function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = 'flex';
    }
}

// Close modal
function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = 'none';
    }
}

// Format numbers with thousands separator
function formatNumberWithCommas(number) {
    return number.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
}

// Document ready utility
function documentReady(fn) {
    if (document.readyState !== 'loading') {
        fn();
    } else {
        document.addEventListener('DOMContentLoaded', fn);
    }
}

// Initialize time ago formatting for all timestamp elements
documentReady(function() {
    // Format time ago elements
    const timeAgoElements = document.querySelectorAll('.time-ago');
    timeAgoElements.forEach(element => {
        const timestamp = element.dataset.timestamp;
        if (timestamp) {
            element.textContent = formatTimeAgo(timestamp);
        }
    });

    // Format file size elements
    const fileSizeElements = document.querySelectorAll('.file-size');
    fileSizeElements.forEach(element => {
        const size = element.dataset.size;
        if (size) {
            element.textContent = formatFileSize(size);
        }
    });
});

// Initialize tooltips
document.addEventListener('DOMContentLoaded', () => {
    // Add tooltips to elements with data-tooltip attribute
    const tooltips = document.querySelectorAll('[data-tooltip]');
    tooltips.forEach(tooltip => {
        tooltip.title = tooltip.getAttribute('data-tooltip');
    });

    // Initialize date formatters
    const timeAgoElements = document.querySelectorAll('.time-ago');
    timeAgoElements.forEach(element => {
        const timestamp = element.getAttribute('data-timestamp');
        element.textContent = formatTimeAgo(timestamp);
    });

    // Initialize size formatters
    const sizeElements = document.querySelectorAll('.file-size');
    sizeElements.forEach(element => {
        const size = element.getAttribute('data-size');
        element.textContent = formatSize(size);
    });
});
