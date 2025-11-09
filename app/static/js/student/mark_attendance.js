SAAuth.ensureAuthenticated('student', '/student/login');

let locationGranted = false;

// Request location permission on page load
window.addEventListener('DOMContentLoaded', async ()=>{
	await requestLocationPermission();
});

async function requestLocationPermission(){
	const alert = document.getElementById('location-permission-alert');
	const formContainer = document.getElementById('attendance-form-container');
	const btn = document.getElementById('request-location-btn');
	
	if(btn) btn.textContent = 'Requesting...';
	
	try{
		console.log('Requesting location permission...');
		const position = await SA.getCurrentPosition();
		console.log('Location granted:', position);
		locationGranted = true;
		if(alert) alert.style.display = 'none';
		if(formContainer) formContainer.style.display = 'block';
	}catch(err){
		console.error('Location permission denied:', err);
		locationGranted = false;
		if(alert){
			alert.style.display = 'block';
			// Update alert message with error details
			const alertText = alert.querySelector('p');
			if(alertText){
				if(err.code === 1){
					alertText.textContent = 'Location access denied. Please enable location in your browser settings.';
				}else if(err.code === 2){
					alertText.textContent = 'Location unavailable. Please check your device settings.';
				}else if(err.code === 3){
					alertText.textContent = 'Location request timed out. Please try again.';
				}else{
					alertText.textContent = 'Unable to access location. Error: ' + err.message;
				}
			}
		}
		if(formContainer) formContainer.style.display = 'none';
	}finally{
		if(btn) btn.textContent = 'Grant Location Access';
	}
}

// Manual location request button
document.getElementById('request-location-btn')?.addEventListener('click', async (e)=>{
	e.preventDefault();
	await requestLocationPermission();
});

// Handle attendance form submission
let submitting = false;
document.getElementById('attendance-form')?.addEventListener('submit', async (e)=>{
	e.preventDefault();
	
	if(submitting) return;
	if(!locationGranted){
		const msg = document.getElementById('attendance-msg');
		SA.showMsg(msg, 'Location permission required', false);
		return;
	}
	
	submitting = true;
	const form = e.target;
	const submitBtn = form.querySelector('button[type="submit"]');
	const msg = document.getElementById('attendance-msg');
	
	submitBtn.disabled = true;
	submitBtn.textContent = 'Marking...';
	
	try{
		// Get fresh location
		const coords = await SA.getCurrentPosition();
		
		// Get form data
		const formData = new FormData(form);
		const body = {
			subject: formData.get('subject'),
			otp: formData.get('otp'),
			latitude: coords.latitude,
			longitude: coords.longitude,
			accuracy: coords.accuracy
		};
		
		// Submit attendance
		const res = await SA.apiFetch('student', '/student/mark_attendance', { 
			method: 'POST', 
			body: body,
			auth: true 
		});
		const data = await res.json();
		
		if(res.ok){
			SA.showMsg(msg, data.message || 'Attendance marked successfully!', true);
			form.reset();
		}else{
			SA.showMsg(msg, data.message || 'Failed to mark attendance', false);
		}
	}catch(err){
		SA.showMsg(msg, 'Error: ' + (err.message || 'Network error'), false);
	}finally{
		submitting = false;
		submitBtn.disabled = false;
		submitBtn.textContent = 'Mark Attendance';
	}
});
