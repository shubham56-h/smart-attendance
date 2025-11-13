document.getElementById('student-register')?.addEventListener('submit', async (e)=>{
	e.preventDefault();
	const form = e.target;
	const msg = document.getElementById('student-register-msg');
	const submitBtn = form.querySelector('button[type="submit"]');
	const body = Object.fromEntries(new FormData(form).entries());
	
	submitBtn.disabled = true;
	submitBtn.innerHTML = '<span class="spinner"></span>Registering...';
	
	try{
		const res = await SA.apiFetch('student', '/student/register', { method: 'POST', body });
		const data = await res.json();
		if(res.ok){
			SA.showMsg(msg, data.message || 'Registered successfully', 'success');
			setTimeout(()=> window.location.href = '/student/login', 500);
			form.reset();
		}else{
			SA.showMsg(msg, data.message || 'Registration failed', 'error');
			submitBtn.disabled = false;
			submitBtn.textContent = 'Register';
		}
	}catch(err){ 
		SA.showMsg(msg, 'Network error', 'error');
		submitBtn.disabled = false;
		submitBtn.textContent = 'Register';
	}
});


