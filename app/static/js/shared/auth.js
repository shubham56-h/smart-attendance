function ensureAuthenticated(role, redirectTo){
	const token = SA.getToken(role);
	if(!token){ window.location.href = redirectTo; }
}

function logout(role, redirectTo){
	localStorage.removeItem(`${role}_access_token`);
	localStorage.removeItem(`${role}_refresh_token`);
	window.location.href = redirectTo;
}

window.SAAuth = { ensureAuthenticated, logout };


