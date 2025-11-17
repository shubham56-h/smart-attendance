SAAuth.ensureAuthenticated('faculty', '/faculty/login');

document.getElementById('faculty-logout')?.addEventListener('click', ()=> SAAuth.logout('faculty', '/faculty/login'));

// Format datetime to readable format with precise timing for recent events
function formatDateTime(isoString) {
    if (!isoString) return 'N/A';
    const date = new Date(isoString);
    const now = new Date();
    const diffMs = now - date;
    const diffSecs = Math.floor(diffMs / 1000);
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);
    
    // More precise for recent times
    if (diffSecs < 10) return 'Just now';
    if (diffSecs < 60) return `${diffSecs}s ago`;
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) {
        // Show hours and minutes for better precision
        const remainingMins = diffMins % 60;
        if (remainingMins > 0) {
            return `${diffHours}h ${remainingMins}m ago`;
        }
        return `${diffHours}h ago`;
    }
    if (diffDays < 7) return `${diffDays}d ago`;
    
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
}

// Load recent sessions
async function loadRecentSessions() {
    const tbody = document.getElementById('recent-sessions-body');
    if (!tbody) return;
    
    try {
        const res = await SA.apiFetch('faculty', '/faculty/recent_sessions', { method: 'GET', auth: true });
        const data = await res.json();
        
        if (res.ok && data.sessions && data.sessions.length > 0) {
            tbody.innerHTML = '';
            
            // Debug: log first session timestamp
            if (data.sessions[0]) {
                console.log('DEBUG: First session created_at from API:', data.sessions[0].created_at);
                console.log('DEBUG: Parsed date:', new Date(data.sessions[0].created_at));
                console.log('DEBUG: Current time:', new Date());
            }
            
            for (const session of data.sessions) {
                const tr = document.createElement('tr');
                tr.className = 'border-t border-slate-100 hover:bg-slate-50 transition-colors';
                
                // Status badge styling
                let statusClass = 'px-2 py-1 rounded text-xs font-medium';
                if (session.status === 'active') {
                    statusClass += ' bg-green-100 text-green-700';
                } else if (session.status === 'closed') {
                    statusClass += ' bg-slate-100 text-slate-700';
                } else if (session.status === 'expired') {
                    statusClass += ' bg-amber-100 text-amber-700';
                } else {
                    statusClass += ' bg-red-100 text-red-700';
                }
                
                // Debug: show both relative and absolute time
                const createdDate = new Date(session.created_at);
                const relativeTime = formatDateTime(session.created_at);
                const absoluteTime = createdDate.toLocaleString('en-US', { 
                    month: 'short', 
                    day: 'numeric', 
                    hour: '2-digit', 
                    minute: '2-digit' 
                });
                
                tr.innerHTML = `
                    <td class="py-3 pl-4 pr-4 font-mono text-xs">${session.session_code}</td>
                    <td class="py-3 pr-4 font-semibold">${session.subject}</td>
                    <td class="py-3 pr-4 text-slate-600" title="${absoluteTime}">${relativeTime}</td>
                    <td class="py-3 pr-4"><span class="${statusClass}">${session.status}</span></td>
                    <td class="py-3 pr-4 font-semibold text-purple-600">${session.total_students}</td>
                `;
                
                tbody.appendChild(tr);
            }
        } else {
            tbody.innerHTML = '<tr><td colspan="5" class="py-4 text-center text-slate-500">No recent sessions</td></tr>';
        }
    } catch (err) {
        console.error('Failed to load recent sessions:', err);
        tbody.innerHTML = '<tr><td colspan="5" class="py-4 text-center text-red-500">Failed to load sessions</td></tr>';
    }
}

// Load sessions on page load
loadRecentSessions();
