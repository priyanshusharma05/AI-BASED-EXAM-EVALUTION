
const BASE_URL = "http://127.0.0.1:5000";

function showAlert(msg) {
  alert(msg);
}

async function postJson(url, body) {
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = await res.json().catch(() => ({}));
  return { ok: res.ok, status: res.status, data };
}

// --- LOGIN ---
document.getElementById("loginForm")?.addEventListener("submit", async function (e) {
  e.preventDefault();

  // If your login page uses different ids, update these selectors
  const email = document.getElementById("email").value.trim();
  const password = document.getElementById("password").value;
  const roleInput = document.querySelector('input[name="role"]:checked');
  const role = roleInput ? roleInput.value : "student";

  if (!email || !password) {
    showAlert("Please provide email and password.");
    return;
  }

  try {
    const { ok, status, data } = await postJson(`${BASE_URL}/api/login`, {
      email,
      password,
      role,
    });

    if (ok) {
      // login success: store minimal user data and redirect
      localStorage.setItem("userEmail", email);
      localStorage.setItem("userRole", role);
      localStorage.setItem("userName", data.name || data.fullname || "");

      showAlert(data.message || "Logged in successfully!");

      // redirect based on role
      if (role === "teacher") window.location.href = "teacher-dashboard.html";
      else window.location.href = "student-dashboard.html";
    } else {
      // show backend message if present
      showAlert(data.error || data.message || `Login failed (status ${status})`);
      console.warn("Login response:", status, data);
    }
  } catch (err) {
    console.error("Login fetch error:", err);
    showAlert("Network or server error. Check console for details.");
  }
});

// --- SIGNUP ---
document.getElementById("signupForm")?.addEventListener("submit", async function (e) {
  e.preventDefault();

  const fullname = document.getElementById("fullname").value.trim();
  const email = document.getElementById("email").value.trim();
  const password = document.getElementById("password").value;
  const roleInput = document.querySelector('input[name="role"]:checked');
  const role = roleInput ? roleInput.value : "student";

  if (!fullname || !email || !password) {
    showAlert("Please fill all the fields.");
    return;
  }

  try {
    // backend expects 'fullname' field in signup (see app.py)
    const { ok, status, data } = await postJson(`${BASE_URL}/api/signup`, {
      fullname,
      email,
      password,
      role,
    });

    if (ok || status === 201) {
      // success
      localStorage.setItem("userEmail", email);
      localStorage.setItem("userRole", role);
      localStorage.setItem("userName", fullname);

      showAlert(data.message || "Signup successful!");

      if (role === "teacher") window.location.href = "teacher-dashboard.html";
      else window.location.href = "student-dashboard.html";
    } else {
      showAlert(data.error || data.message || `Signup failed (status ${status})`);
      console.warn("Signup response:", status, data);
    }
  } catch (err) {
    console.error("Signup fetch error:", err);
    showAlert("Network or server error. Check console for details.");
  }
});
