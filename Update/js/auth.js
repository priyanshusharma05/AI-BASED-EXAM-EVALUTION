// ✅ Listen for login form submission
document.getElementById("loginForm").addEventListener("submit", async function (event) {
    event.preventDefault(); // prevent page reload

    // Get input values
    const email = document.getElementById("email").value.trim();
    const password = document.getElementById("password").value.trim();
    const role = document.querySelector('input[name="role"]:checked')?.value;

    if (!email || !password || !role) {
        alert("⚠️ Please fill in all fields.");
        return;
    }

    try {
        // Send login request to Flask backend
        const response = await fetch("http://127.0.0.1:5000/api/login", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email, password, role }),
        });

        const data = await response.json();

        if (response.ok) {
            alert(data.message);

            // ✅ Redirect to the correct dashboard
            if (data.redirect) {
                window.location.href = data.redirect;
            } else {
                alert("No redirect URL provided by server.");
            }
        } else {
            alert(data.error || "❌ Login failed. Please check your credentials.");
        }
    } catch (error) {
        console.error("Error:", error);
        alert("🚫 Server not reachable. Please ensure Flask is running on port 5000.");
    }
});
