const API_BASE = window.location.origin;

function getToken(role){
	return localStorage.getItem(`${role}_access_token`) || '';
}

function setTokens(role, { access_token, refresh_token }){
	if(access_token) localStorage.setItem(`${role}_access_token`, access_token);
	if(refresh_token) localStorage.setItem(`${role}_refresh_token`, refresh_token);
}

async function apiFetch(role, path, { method = 'GET', body, auth = false } = {}){
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
	return res;
}

function showMsg(el, text, ok=true){
	if(!el) return;
	el.textContent = text;
	el.className = `mt-2 text-sm ${ok ? 'text-green-600' : 'text-red-600'}`;
}

async function getCurrentPosition(){
	return new Promise((resolve, reject)=>{
		navigator.geolocation.getCurrentPosition(
			pos=> resolve({ latitude: pos.coords.latitude, longitude: pos.coords.longitude }),
			reject,
			{ enableHighAccuracy: true, timeout: 10000 }
		);
	});
}

window.SA = { apiFetch, showMsg, setTokens, getToken, getCurrentPosition };


