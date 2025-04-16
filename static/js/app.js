// Main application JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
    const tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl)
    });
    
    // Auto-dismiss alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    alerts.forEach(alert => {
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });
    
    // Status page auto-refresh (if on status page)
    if (window.location.pathname === '/status') {
        const refreshStatusData = async () => {
            try {
                const response = await fetch('/status');
                if (response.ok) {
                    const data = await response.json();
                    updateStatusDisplay(data);
                }
            } catch (error) {
                console.error('Error fetching status:', error);
            }
        };
        
        // Update status every 30 seconds
        setInterval(refreshStatusData, 30000);
        
        function updateStatusDisplay(data) {
            document.getElementById('botStatus').textContent = data.bot_active ? 'Online' : 'Offline';
            document.getElementById('botStatus').className = data.bot_active ? 'text-success' : 'text-danger';
            document.getElementById('uptime').textContent = data.uptime;
            document.getElementById('userCount').textContent = data.users;
            document.getElementById('commandCount').textContent = data.commands_processed;
            document.getElementById('raydiumStatus').textContent = data.api_status.raydium ? 'Online' : 'Offline';
            document.getElementById('raydiumStatus').className = data.api_status.raydium ? 'text-success' : 'text-danger';
            document.getElementById('aiStatus').textContent = data.api_status.ai ? 'Online' : 'Offline';
            document.getElementById('aiStatus').className = data.api_status.ai ? 'text-success' : 'text-danger';
        }
    }
});