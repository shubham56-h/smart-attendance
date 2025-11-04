SAAuth.ensureAuthenticated('faculty', '/faculty/login');

document.getElementById('faculty-logout')?.addEventListener('click', ()=> SAAuth.logout('faculty', '/faculty/login'));

document.getElementById('faculty-update-location')?.addEventListener('click', async ()=>{
	const msg = document.getElementById('faculty-location-msg');
	try{
		const coords = await SA.getCurrentPosition();
		const res = await SA.apiFetch('faculty', '/faculty/update_location', { method: 'POST', body: coords, auth: true });
		const data = await res.json();
		SA.showMsg(msg, data.message || (res.ok ? 'Location updated' : 'Failed'), res.ok);
	}catch(err){ SA.showMsg(msg, 'Location permission denied or error', false); }
});

document.getElementById('generate-otp')?.addEventListener('click', async ()=>{
	const msg = document.getElementById('otp-msg');
	try{
		const res = await SA.apiFetch('faculty', '/faculty/generate_otp', { method: 'POST', auth: true });
		const data = await res.json();
		if(res.ok){ SA.showMsg(msg, `OTP: ${data.otp} (expires in 5 minutes)`); }
		else{ SA.showMsg(msg, data.message || 'Failed to generate OTP', false); }
	}catch(err){ SA.showMsg(msg, 'Network error', false); }
});

document.getElementById('report-filters')?.addEventListener('submit', async (e)=>{
	e.preventDefault();
	const tableBody = document.getElementById('report-rows');
	const params = new URLSearchParams(Object.fromEntries(new FormData(e.target).entries()));
	const res = await SA.apiFetch('faculty', `/faculty/view_reports?${params.toString()}`, { method: 'GET', auth: true });
	const data = await res.json();
	tableBody.innerHTML = '';
	if(res.ok && Array.isArray(data.records)){
		for(const r of data.records){
			const tr = document.createElement('tr');
			tr.innerHTML = `<td class=\"py-2 pr-4\">${r.student_name}</td>
			<td class=\"py-2 pr-4\">${r.roll_number}</td>
			<td class=\"py-2 pr-4\">${r.division}</td>
			<td class=\"py-2 pr-4\">${r.faculty_name || 'N/A'}</td>
			<td class=\"py-2 pr-4\">${r.subject}</td>
			<td class=\"py-2 pr-4\">${r.date}</td>
			<td class=\"py-2 pr-4\">${r.status}</td>`;
			tableBody.appendChild(tr);
		}
	}else{
		const tr = document.createElement('tr');
		tr.innerHTML = `<td class=\"py-2 pr-4 text-red-600\" colspan=\"7\">${data.message || 'No records or failed to load'}</td>`;
		tableBody.appendChild(tr);
	}
});


