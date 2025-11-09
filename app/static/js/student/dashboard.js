SAAuth.ensureAuthenticated('student', '/student/login');

document.getElementById('student-logout')?.addEventListener('click', ()=> SAAuth.logout('student', '/student/login'));
