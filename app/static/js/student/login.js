document.getElementById('student-login')?.addEventListener('submit', async (e)=>{
	e.preventDefault();
	const form = e.target;
	const msg = document.getElementById('student-login-msg');
	const submitBtn = form.querySelector('button[type="submit"]');
	const body = Object.fromEntries(new FormData(form).entries());
	
	submitBtn.disabled = true;
	submitBtn.innerHTML = '<span class="spinner"></span>Logging in...';
	
	try{
		const res = await SA.apiFetch('student', '/student/login', { method: 'POST', body });
		const data = await res.json();
		if(res.ok){
			SA.setTokens('student', data);
			if(data.student && data.student.full_name){
				localStorage.setItem('student_name', data.student.full_name);
			}
			SA.showMsg(msg, 'Login successful', 'success');
			setTimeout(()=> window.location.href = '/student/dashboard', 300);
		}else{
			SA.showMsg(msg, data.message || 'Invalid credentials', 'error');
			submitBtn.disabled = false;
			submitBtn.textContent = 'Login';
		}
	}catch(err){ 
		SA.showMsg(msg, 'Network error', 'error');
		submitBtn.disabled = false;
		submitBtn.textContent = 'Login';
	}
});


