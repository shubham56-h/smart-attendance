SAAuth.ensureAuthenticated('student', '/student/login');

document.getElementById('student-logout')?.addEventListener('click', ()=> SAAuth.logout('student', '/student/login'));

document.getElementById('student-update-location')?.addEventListener('click', async ()=>{
	const msg = document.getElementById('student-location-msg');
	try{
		const coords = await SA.getCurrentPosition();
		const res = await SA.apiFetch('student', '/student/update_location', { method: 'POST', body: coords, auth: true });
		const data = await res.json();
		SA.showMsg(msg, data.message || (res.ok ? 'Location updated' : 'Failed'), res.ok);
	}catch(err){ SA.showMsg(msg, 'Location permission denied or error', false); }
});

document.getElementById('student-attendance')?.addEventListener('submit', async (e)=>{
	e.preventDefault();
	const form = e.target;
	const msg = document.getElementById('student-attendance-msg');
	const body = Object.fromEntries(new FormData(form).entries());
	try{
		const res = await SA.apiFetch('student', '/student/fill_attendance', { method: 'POST', body, auth: true });
		const data = await res.json();
		SA.showMsg(msg, data.message || (res.ok ? 'Marked present' : 'Failed'), res.ok);
		if(res.ok){ form.reset(); }
	}catch(err){ SA.showMsg(msg, 'Network error', false); }
});


