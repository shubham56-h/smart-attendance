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
	submitBtn.innerHTML = '<span class="spinner"></span>Marking...';
	
	try{
		// Get fresh location
		const coords = await SA.getCurrentPosition();
		console.log('Student location:', coords);
		
		// Get form data
		const formData = new FormData(form);
		const body = {
			subject: formData.get('subject'),
			otp: formData.get('otp'),
			latitude: coords.latitude,
			longitude: coords.longitude,
			accuracy: coords.accuracy
		};
		
		console.log('Submitting attendance:', body);
		
		// Submit attendance
		const res = await SA.apiFetch('student', '/student/mark_attendance', { 
			method: 'POST', 
			body: body,
			auth: true 
		});
		const data = await res.json();
		
		if(res.ok){
			// Show success animation
			showSuccessAnimation(data.message || 'Attendance marked successfully!', data.distance);
			if(data.distance) {
				console.log(`Distance from faculty: ${data.distance}m`);
			}
			form.reset();
		}else{
			console.error('Attendance failed:', data);
			SA.showMsg(msg, data.message || 'Failed to mark attendance', 'error');
			// Show debug info if available
			if(data.debug) {
				console.log('Debug info:', data.debug);
			}
		}
	}catch(err){
		SA.showMsg(msg, 'Error: ' + (err.message || 'Network error'), 'error');
	}finally{
		submitting = false;
		submitBtn.disabled = false;
		submitBtn.textContent = 'Mark Attendance';
	}
});

// Success animation modal
function showSuccessAnimation(message, distance) {
	const modal = document.createElement('div');
	modal.className = 'success-modal';
	modal.innerHTML = `
		<div class="success-modal-content">
			<div class="success-checkmark">
				<div class="check-icon">
					<span class="icon-line line-tip"></span>
					<span class="icon-line line-long"></span>
				</div>
			</div>
			<h2 style="margin-top: 1.5rem; font-size: 1.5rem; font-weight: 700; color: #10b981;">Success!</h2>
			<p style="margin-top: 0.5rem; color: #6b7280;">${message}</p>
			${distance ? `<p style="margin-top: 0.5rem; color: #6b7280; font-size: 0.875rem;">Distance: ${distance}m from faculty</p>` : ''}
		</div>
	`;
	document.body.appendChild(modal);
	
	// Auto-close after 3 seconds
	setTimeout(() => {
		modal.style.opacity = '0';
		setTimeout(() => modal.remove(), 300);
	}, 3000);
	
	// Click to close
	modal.addEventListener('click', () => {
		modal.style.opacity = '0';
		setTimeout(() => modal.remove(), 300);
	});
}
