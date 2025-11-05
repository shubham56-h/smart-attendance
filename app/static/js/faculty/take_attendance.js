SAAuth.ensureAuthenticated('faculty', '/faculty/login');

// Track state
let locationUpdated = false;

// Initialize state on page load
window.addEventListener('DOMContentLoaded', ()=>{
	const subjectInput = document.getElementById('subject-input');
	const msg = document.getElementById('subject-msg');
	const storedSubject = localStorage.getItem('current_subject');
	if(storedSubject && subjectInput){
		subjectInput.value = storedSubject;
		SA.showMsg(msg, `Selected subject: ${storedSubject}`, true);
	}else{
		SA.showMsg(msg, 'No subject selected', false);
	}
});

// Subject selection - direct from dropdown
document.getElementById('subject-input')?.addEventListener('change', (e)=>{
	const input = e.target;
	const msg = document.getElementById('subject-msg');
	const subject = (input.value || '').trim();
	if(!subject){ 
		localStorage.removeItem('current_subject');
		msg.textContent = '';
		return; 
	}
	localStorage.setItem('current_subject', subject);
	SA.showMsg(msg, `Selected subject: ${subject}`, true);
});

// Update location
document.getElementById('faculty-update-location')?.addEventListener('click', async ()=>{
	const msg = document.getElementById('faculty-location-msg');
	const subject = localStorage.getItem('current_subject');
	
	if(!subject){
		SA.showMsg(msg, 'Please select a subject first', false);
		return;
	}
	
	try{
		const coords = await SA.getCurrentPosition();
		const res = await SA.apiFetch('faculty', '/faculty/update_location', { method: 'POST', body: coords, auth: true });
		const data = await res.json();
		if(res.ok){
			locationUpdated = true;
			SA.showMsg(msg, data.message || 'Location updated', true);
		}else{
			locationUpdated = false;
			SA.showMsg(msg, data.message || 'Failed', false);
		}
	}catch(err){ 
		locationUpdated = false;
		SA.showMsg(msg, 'Location permission denied or error', false); 
	}
});

// Generate OTP button (manual trigger - validates subject and location first)
document.getElementById('generate-otp')?.addEventListener('click', async ()=>{
	const msg = document.getElementById('otp-msg');
	const subject = localStorage.getItem('current_subject');
	
	if(!subject){
		SA.showMsg(msg, 'Please select a subject first', false);
		return;
	}
	
	if(!locationUpdated){
		SA.showMsg(msg, 'Please update your location first', false);
		return;
	}
	
	try{
		const res = await SA.apiFetch('faculty', '/faculty/generate_otp', { 
			method: 'POST', 
			body: { subject: subject },
			auth: true 
		});
		const data = await res.json();
		if(res.ok){
			SA.showMsg(msg, `OTP for ${data.subject || subject}: ${data.otp} (expires in 5 minutes)`);
		}else{
			SA.showMsg(msg, data.message || 'Failed to generate OTP', false);
		}
	}catch(err){ 
		SA.showMsg(msg, 'Network error', false); 
	}
});


