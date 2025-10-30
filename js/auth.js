const API_BASE = "http://172.16.56.61:5000/api";

// LOGIN
document.getElementById('loginForm')?.addEventListener('submit', async function (e) {
  e.preventDefault();

  const email = document.getElementById('email').value;
  const password = document.getElementById('password').value;
  const role = document.querySelector('input[name="role"]:checked').value;

  try {
    const res = await fetch(`${API_BASE}/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password, role })
    });

    const data = await res.json();
    if (res.ok) {
      alert('Login successful!');
      localStorage.setItem('userRole', role);
      localStorage.setItem('userEmail', email);
      localStorage.setItem('userName', data.name || '');
      
      if (role === 'teacher') {
        window.location.href = 'teacher-dashboard.html';
      } else {
        window.location.href = 'student-dashboard.html';
      }
    } else {
      alert(data.error || 'Invalid credentials');
    }
  } catch (error) {
    alert('Server error: ' + error.message);
  }
});

// SIGNUP
document.getElementById('signupForm')?.addEventListener('submit', async function (e) {
  e.preventDefault();

  const fullname = document.getElementById('fullname').value;
  const email = document.getElementById('email').value;
  const password = document.getElementById('password').value;
  const role = document.querySelector('input[name="role"]:checked').value;

  try {
    const res = await fetch(`${API_BASE}/signup`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ fullname, email, password, role })
    });

    const data = await res.json();
    if (res.ok) {
      alert('Signup successful!');
      localStorage.setItem('userRole', role);
      localStorage.setItem('userEmail', email);
      localStorage.setItem('userName', fullname);

      if (role === 'teacher') {
        window.location.href = 'teacher-dashboard.html';
      } else {
        window.location.href = 'student-dashboard.html';
      }
    } else {
      alert(data.error || 'Signup failed');
    }
  } catch (error) {
    alert('Server error: ' + error.message);
  }
});
