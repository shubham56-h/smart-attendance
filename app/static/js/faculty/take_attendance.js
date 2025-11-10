SAAuth.ensureAuthenticated('faculty', '/faculty/login');

let locationGranted = false;
let sessionTimer = null;

// Check for existing session on page load
window.addEventListener('DOMContentLoaded', async ()=>{
	console.log('Page loaded, checking for existing session...');
	await checkExistingSession();
});

async function checkExistingSession(){
	try{
		const res = await SA.apiFetch('faculty', '/faculty/get_active_session', { method: 'GET', auth: true });
		const data = await res.json();
		
		if(res.ok && data.session){
			console.log('Found existing session:', data.session);
			// Show existing active session
			showActiveSession(data.session);
			document.getElementById('location-permission-alert').style.display = 'none';
			document.getElementById('session-form').style.display = 'none';
		}else{
			console.log('No existing session, showing location prompt');
		}
	}catch(err){
		console.log('No active session found or error:', err);
	}
}

async function requestLocationPermission(){
	const alert = document.getElementById('location-permission-alert');
	const form = document.getElementById('session-form');
	const btn = document.getElementById('request-location-btn');
	
	console.log('requestLocationPermission called');
	
	if(btn) btn.textContent = 'Requesting...';
	
	try{
		console.log('Calling SA.getCurrentPosition()...');
		const position = await SA.getCurrentPosition();
		console.log('Location granted:', position);
		
		locationGranted = true;
		if(alert) alert.style.display = 'none';
		if(form) form.style.display = 'block';
		
		console.log('Form should now be visible');
	}catch(err){
		console.error('Location permission error:', err);
		locationGranted = false;
		
		if(alert){
			alert.style.display = 'block';
			const alertText = alert.querySelector('p');
			if(alertText){
				if(err.code === 1){
					alertText.textContent = 'Location access denied. Please enable location in your browser settings.';
				}else if(err.code === 2){
					alertText.textContent = 'Location unavailable. Please check your device settings.';
				}else if(err.code === 3){
					alertText.textContent = 'Location request timed out. Please try again.';
				}else{
					alertText.textContent = 'Unable to access location. Error: ' + (err.message || 'Unknown error');
				}
			}
		}
		if(form) form.style.display = 'none';
	}finally{
		if(btn) btn.textContent = 'Grant Location Access';
	}
}

// Manual location request button
const requestBtn = document.getElementById('request-location-btn');
console.log('Looking for request-location-btn:', requestBtn);

if(requestBtn){
	console.log('Button found, attaching click handler');
	requestBtn.addEventListener('click', async (e)=>{
		console.log('Button clicked!');
		e.preventDefault();
		await requestLocationPermission();
	});
}else{
	console.error('request-location-btn NOT FOUND!');
}

// Enable start button when subject is selected
const subjectInput = document.getElementById('subject-input');
if(subjectInput){
	subjectInput.addEventListener('change', (e)=>{
		const btn = document.getElementById('start-session-btn');
		const subject = e.target.value.trim();
		if(btn){
			btn.disabled = !subject;
		}
	});
}

// Start session button
const startBtn = document.getElementById('start-session-btn');
if(startBtn){
	startBtn.addEventListener('click', async ()=>{
		const btn = document.getElementById('start-session-btn');
		const msg = document.getElementById('session-msg');
		const subjectInput = document.getElementById('subject-input');
		const subject = subjectInput?.value.trim();
		
		if(!subject){
			SA.showMsg(msg, 'Please select a subject', 'error');
			return;
		}
		
		if(!locationGranted){
			SA.showMsg(msg, 'Location permission required', 'error');
			return;
		}
		
		btn.disabled = true;
		btn.textContent = 'Starting...';
		
		try{
			const coords = await SA.getCurrentPosition();
			
			const res = await SA.apiFetch('faculty', '/faculty/start_session', { 
				method: 'POST', 
				body: { subject: subject, location: coords },
				auth: true 
			});
			const data = await res.json();
			
			if(res.ok){
				SA.showMsg(msg, 'Session started successfully!', 'success');
				showActiveSession(data);
				const sessionForm = document.getElementById('session-form');
				if(sessionForm) sessionForm.style.display = 'none';
			}else{
				SA.showMsg(msg, data.message || 'Failed to start session', 'error');
				btn.disabled = false;
				btn.textContent = 'Start Session';
			}
		}catch(err){
			SA.showMsg(msg, 'Error: ' + (err.message || 'Network error'), 'error');
			btn.disabled = false;
			btn.textContent = 'Start Session';
		}
	});
}

function showActiveSession(data){
	const activeDiv = document.getElementById('active-session');
	const subjectSpan = document.getElementById('active-subject');
	const otpSpan = document.getElementById('active-otp');
	const timerSpan = document.getElementById('active-timer');
	
	if(subjectSpan) subjectSpan.textContent = data.subject || '';
	if(otpSpan) otpSpan.textContent = data.otp || '';
	if(activeDiv) activeDiv.style.display = 'block';
	
	if(data.expires_at && timerSpan){
		const expiresAt = new Date(data.expires_at);
		console.log('Expires at:', expiresAt);
		console.log('Current time:', new Date());
		console.log('Difference (ms):', expiresAt - new Date());
		
		updateTimer(expiresAt, timerSpan);
		if(sessionTimer) clearInterval(sessionTimer);
		sessionTimer = setInterval(()=> updateTimer(expiresAt, timerSpan), 1000);
	}
}

function updateTimer(expiresAt, timerSpan){
	const now = new Date();
	const diff = expiresAt - now;
	
	if(diff <= 0){
		timerSpan.textContent = 'EXPIRED';
		timerSpan.style.color = '#dc2626';
		if(sessionTimer){
			clearInterval(sessionTimer);
			sessionTimer = null;
		}
		return;
	}
	
	const minutes = Math.floor(diff / 60000);
	const seconds = Math.floor((diff % 60000) / 1000);
	timerSpan.textContent = `${minutes}:${seconds.toString().padStart(2, '0')}`;
	timerSpan.style.color = minutes < 1 ? '#dc2626' : '#059669';
}

// End session button
const endBtn = document.getElementById('end-session-btn');
if(endBtn){
	endBtn.addEventListener('click', async ()=>{
		const btn = document.getElementById('end-session-btn');
		if(btn) btn.disabled = true;
		
		try{
			const res = await SA.apiFetch('faculty', '/faculty/close_session', { method: 'POST', auth: true });
			const data = await res.json();
			
			if(res.ok){
				if(sessionTimer){
					clearInterval(sessionTimer);
					sessionTimer = null;
				}
				
				const activeSession = document.getElementById('active-session');
				const sessionForm = document.getElementById('session-form');
				const subjectInput = document.getElementById('subject-input');
				const startBtn = document.getElementById('start-session-btn');
				const sessionMsg = document.getElementById('session-msg');
				const locationAlert = document.getElementById('location-permission-alert');
				
				if(activeSession) activeSession.style.display = 'none';
				if(locationAlert) locationAlert.style.display = 'block';
				if(sessionForm) sessionForm.style.display = 'none';
				if(subjectInput) subjectInput.value = '';
				if(startBtn){
					startBtn.disabled = true;
					startBtn.textContent = 'Start Session';
				}
				if(sessionMsg) SA.showMsg(sessionMsg, 'Session ended successfully', 'success');
				
				locationGranted = false;
			}else{
				alert(data.message || 'Failed to end session');
			}
		}catch(err){
			alert('Error ending session: ' + err.message);
		}finally{
			if(btn) btn.disabled = false;
		}
	});
}
