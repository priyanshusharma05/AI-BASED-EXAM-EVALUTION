document.getElementById('loginForm')?.addEventListener('submit', function(e) {
  e.preventDefault();
  
  const email = document.getElementById('email').value;
  const password = document.getElementById('password').value;
  const role = document.querySelector('input[name="role"]:checked').value;
  
  localStorage.setItem('userRole', role);
  localStorage.setItem('userEmail', email);
  
  if (role === 'teacher') {
    window.location.href = 'teacher-dashboard.html';
  } else {
    window.location.href = 'student-dashboard.html';
  }
});

document.getElementById('signupForm')?.addEventListener('submit', function(e) {
  e.preventDefault();
  
  const fullname = document.getElementById('fullname').value;
  const email = document.getElementById('email').value;
  const password = document.getElementById('password').value;
  const role = document.querySelector('input[name="role"]:checked').value;
  
  localStorage.setItem('userRole', role);
  localStorage.setItem('userEmail', email);
  localStorage.setItem('userName', fullname);
  
  if (role === 'teacher') {
    window.location.href = 'teacher-dashboard.html';
  } else {
    window.location.href = 'student-dashboard.html';
  }
});
