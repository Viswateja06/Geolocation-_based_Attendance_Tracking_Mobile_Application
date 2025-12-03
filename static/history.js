let authToken = null;

// API functions
const api = {
    async history(startDate, endDate) {
        const url = new URL(window.location.origin + '/student/history');
        if (startDate && endDate) { 
            url.searchParams.set('startDate', startDate); 
            url.searchParams.set('endDate', endDate); 
        }
        const r = await fetch(url.toString(), { 
            headers: { 'Authorization': `Bearer ${authToken}` } 
        });
        return r.ok ? r.json() : [];
    },
    
    async logout() {
        await fetch('/logout', { 
            method: 'POST',
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        window.location.href = '/';
    }
};

// Format date to YYYY-MM-DD
function formatDate(date) {
    return date.toISOString().split('T')[0];
}

// Format time to HH:MM:SS AM/PM
function formatTime(dateStr) {
    if (!dateStr) return '-';
    const date = new Date(dateStr);
    return date.toLocaleTimeString('en-IN', {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: true,
        timeZone: 'Asia/Kolkata'
    });
}

// Calculate duration between two times
function calculateDuration(start, end) {
    if (!start || !end) return '-';
    const diffMs = new Date(end) - new Date(start);
    const hours = Math.floor(diffMs / 3600000);
    const minutes = Math.floor((diffMs % 3600000) / 60000);
    return `${hours}h ${minutes}m`;
}

// Render history table
function renderHistory(logs) {
    const holder = document.getElementById('historyList');
    if (!Array.isArray(logs) || !logs.length) { 
        holder.innerHTML = '<div class="no-data">No attendance records found for the selected period.</div>';
        return; 
    }
    
    const header = `
        <table class="history-table">
            <thead>
                <tr>
                    <th>Date</th>
                    <th>Check-In</th>
                    <th>Check-Out</th>
                    <th>Duration</th>
                    <th>Location</th>
                </tr>
            </thead>
            <tbody>`;
    
    const rows = logs.map(log => {
        const checkInTime = formatTime(log.check_in_time || log.checkInTime);
        const checkOutTime = formatTime(log.check_out_time || log.checkOutTime);
        const duration = calculateDuration(
            log.check_in_time || log.checkInTime,
            log.check_out_time || log.checkOutTime
        );
        
        return `
            <tr>
                <td>${log.date || '-'}</td>
                <td>${checkInTime}</td>
                <td>${checkOutTime}</td>
                <td>${duration}</td>
                <td>${log.location_name || log.location || '-'}</td>
            </tr>`;
    }).join('');
    
    holder.innerHTML = `${header}${rows}</tbody></table>`;
}

// Initialize the page
async function init() {
    // Get token from localStorage
    authToken = localStorage.getItem('authToken');
    if (!authToken) {
        window.location.href = '/';
        return;
    }

    // Set default date range (last 30 days)
    const endDate = new Date();
    const startDate = new Date();
    startDate.setDate(startDate.getDate() - 30);
    
    document.getElementById('histStart').value = formatDate(startDate);
    document.getElementById('histEnd').value = formatDate(endDate);

    // Load initial history
    await loadHistory();

    // Event Listeners
    document.getElementById('loadHistoryBtn').addEventListener('click', loadHistory);
    document.getElementById('logoutBtn').addEventListener('click', () => api.logout());
}

// Load history based on selected dates
async function loadHistory() {
    try {
        const startDate = document.getElementById('histStart').value;
        const endDate = document.getElementById('histEnd').value;
        
        if (!startDate || !endDate) {
            toast('Please select both start and end dates', 'error');
            return;
        }
        
        document.getElementById('historyList').textContent = 'Loading...';
        const logs = await api.history(startDate, endDate);
        renderHistory(logs);
    } catch (error) {
        console.error('Error loading history:', error);
        toast('Failed to load history', 'error');
    }
}

// Initialize the page when DOM is loaded
document.addEventListener('DOMContentLoaded', init);
