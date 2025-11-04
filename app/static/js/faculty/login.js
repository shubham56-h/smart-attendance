document.getElementById('faculty-login')?.addEventListener('submit', async (e)=>{
	e.preventDefault();
	const form = e.target;
	const msg = document.getElementById('faculty-login-msg');
	const body = Object.fromEntries(new FormData(form).entries());
	try{
		const res = await SA.apiFetch('faculty', '/faculty/login', { method: 'POST', body });
		const data = await res.json();
		if(res.ok){
			SA.setTokens('faculty', data);
			SA.showMsg(msg, 'Login successful');
			setTimeout(()=> window.location.href = '/faculty/dashboard', 300);
		}else{
			SA.showMsg(msg, data.message || 'Invalid credentials', false);
		}
	}catch(err){ SA.showMsg(msg, 'Network error', false); }
});


