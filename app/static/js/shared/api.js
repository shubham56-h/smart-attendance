const API_BASE = window.location.origin;

function getToken(role){
	return localStorage.getItem(`${role}_access_token`) || '';
}

function getRefreshToken(role){
	return localStorage.getItem(`${role}_refresh_token`) || '';
}

function setTokens(role, { access_token, refresh_token }){
	if(access_token) localStorage.setItem(`${role}_access_token`, access_token);
	if(refresh_token) localStorage.setItem(`${role}_refresh_token`, refresh_token);
}

async function refreshAccessToken(role){
	const refreshToken = getRefreshToken(role);
	if(!refreshToken) return false;
	
	try {
		const res = await fetch(`${API_BASE}/${role}/refresh`, {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json',
				'Authorization': `Bearer ${refreshToken}`
			}
		});
		
		if(res.ok){
			const data = await res.json();
			if(data.access_token){
				localStorage.setItem(`${role}_access_token`, data.access_token);
				return true;
			}
		}
	} catch(e){
		console.error('Token refresh failed:', e);
	}
	return false;
}

async function apiFetch(role, path, { method = 'GET', body, auth = false, _retry = false } = {}){
	const headers = { 'Content-Type': 'application/json' };
	if(auth){
		const token = getToken(role);
		if(token) headers['Authorization'] = `Bearer ${token}`;
	}
	
	const res = await fetch(`${API_BASE}${path}`, {
		method,
		headers,
		body: body ? JSON.stringify(body) : undefined
	});
	
	// If 401 and we haven't retried yet, try to refresh token
	if(res.status === 401 && auth && !_retry){
		const refreshed = await refreshAccessToken(role);
		if(refreshed){
			// Retry the request with new token
			return apiFetch(role, path, { method, body, auth, _retry: true });
		}
	}
	
	return res;
}

function showMsg(el, text, type='error'){
	if(!el) return;
	
	// Clear any existing timeout
	if(el._hideTimeout){
		clearTimeout(el._hideTimeout);
		el._hideTimeout = null;
	}
	
	el.textContent = text;
	el.style.opacity = '1';
	el.style.transition = 'opacity 0.3s ease';
	
	// type can be: 'error', 'success', 'info'
	if(type === 'success'){
		el.className = 'msg-success';
	} else if(type === 'info'){
		el.className = 'msg-info';
	} else {
		el.className = 'msg-error';
	}
	
	// Auto-hide after 5 seconds with fade out
	el._hideTimeout = setTimeout(() => {
		el.style.opacity = '0';
		setTimeout(() => {
			el.textContent = '';
			el.className = '';
			el.style.opacity = '1';
		}, 300); // Wait for fade out to complete
	}, 5000);
}

const GEOLOCATION_OPTIONS = {
	enableHighAccuracy: true,
	timeout: 15000,
	maximumAge: 0
};

async function getCurrentPosition(){
	return new Promise((resolve, reject)=>{
		navigator.geolocation.getCurrentPosition(
			pos=> resolve({
				latitude: pos.coords.latitude,
				longitude: pos.coords.longitude,
				accuracy: pos.coords.accuracy
			}),
			reject,
			GEOLOCATION_OPTIONS
		);
	});
}

window.SA = { apiFetch, showMsg, setTokens, getToken, getCurrentPosition };


