// ===============================
// DASHBOARD.JS (Student + Teacher)
// ===============================

// SECTION SWITCHING
function showSection(sectionId) {
    document.querySelectorAll(".content-section").forEach(section => section.classList.remove("active"));
    document.getElementById(sectionId)?.classList.add("active");

    const titles = {
        overview: "Dashboard Overview",
        upload: "Upload Answer Sheet",
        results: "View Results",
        performance: "Performance Analytics",
        "upload-key": "Upload Answer Key",
        submissions: "View Submissions"
    };
    document.getElementById("section-title").textContent = titles[sectionId] || "Dashboard Overview";

    // If switching to overview, refresh stats dynamically
    if (sectionId === "overview") loadDashboardStats();
}

// STATUS DISPLAY
function updateStatus(id, message, success = true) {
    const el = document.getElementById(id);
    if (!el) return;
    el.innerHTML = `<div class="upload-status ${success ? "success" : "error"}">${success ? "✅" : "❌"} ${message}</div>`;
    setTimeout(() => (el.innerHTML = ""), 5000);
}

// ========== TEACHER UPLOAD KEY ==========
const answerKeyForm = document.getElementById("answerKeyForm");
if (answerKeyForm) {
    answerKeyForm.addEventListener("submit", async e => {
        e.preventDefault();
        const file = document.getElementById("answerKeyFile").files[0];
        if (!file) return updateStatus("teacherUploadStatus", "No file selected", false);

        const formData = new FormData();
        formData.append("file", file);
        formData.append("teacher", localStorage.getItem("userEmail") || "Unknown");

        const res = await fetch("http://127.0.0.1:5000/api/upload-key", { method: "POST", body: formData });
        const data = await res.json();
        updateStatus("teacherUploadStatus", res.ok ? data.message : data.error, res.ok);
        if (res.ok) loadStudentSubmissions();
    });
}

// ========== STUDENT UPLOAD ==========
const answerSheetForm = document.getElementById("answerSheetForm");
if (answerSheetForm) {
    const fileInput = document.getElementById("answerSheetFile");
    const previewContainer = document.getElementById("answerSheetPreview");
    const gallery = document.getElementById("imageGallery");

    fileInput.addEventListener("change", () => {
        gallery.innerHTML = "";
        const files = Array.from(fileInput.files);
        if (!files.length) return (previewContainer.style.display = "none");

        previewContainer.style.display = "block";
        files.forEach(f => {
            const div = document.createElement("div");
            div.classList.add("preview-item");
            if (f.type.startsWith("image/")) {
                const img = document.createElement("img");
                img.classList.add("preview-thumb");
                img.src = URL.createObjectURL(f);
                div.appendChild(img);
            } else {
                div.textContent = `📄 ${f.name}`;
                div.classList.add("pdf-preview");
            }
            gallery.appendChild(div);
        });
    });

    answerSheetForm.addEventListener("submit", async e => {
        e.preventDefault();
        const files = Array.from(fileInput.files);
        if (!files.length) return updateStatus("studentUploadStatus", "Please select files", false);

        const formData = new FormData();
        files.forEach(f => formData.append("files", f));
        formData.append("exam_name", document.getElementById("examDropdown").value);
        formData.append("subject", document.getElementById("subjectDropdown").value);
        formData.append("roll_number", document.getElementById("rollNumber").value);
        formData.append("notes", document.getElementById("notes").value);
        formData.append("answer_sheet_type", document.getElementById("answerSheetTypeDropdown").value);
        formData.append("student", localStorage.getItem("userEmail") || "Unknown");

        const res = await fetch("http://127.0.0.1:5000/api/upload-answer", { method: "POST", body: formData });
        const data = await res.json();
        updateStatus("studentUploadStatus", res.ok ? data.message : data.error, res.ok);

        if (res.ok) {
            await loadStudentResults();
            await loadDashboardStats(); // ✅ Update stats instantly after upload
            showSection("results");
        }
    });
}

// ========== LOAD STUDENT RESULTS ==========
async function loadStudentResults() {
    const grid = document.querySelector(".results-grid");
    if (!grid) return;
    const studentEmail = localStorage.getItem("userEmail");
    grid.innerHTML = "<p>⏳ Loading submissions...</p>";

    try {
        const res = await fetch(`http://127.0.0.1:5000/api/get-student-submissions?student=${studentEmail}`);
        const data = await res.json();

        if (res.ok && data.submissions.length) {
            grid.innerHTML = data.submissions.map(sub => {
                const isEvaluated = sub.status === "evaluated";
                const marksText = isEvaluated
                    ? `<div class="exam-score">
                        <span class="score-large">${sub.marks_obtained}</span>
                        <span class="score-total">/ ${sub.total_marks || 100}</span>
                       </div>`
                    : `<div class="exam-score"><span class="score-pending">⏳ Pending</span></div>`;

                const feedbackText = isEvaluated && sub.feedback
                    ? `<div class="feedback-text"><strong>Feedback:</strong> ${sub.feedback}</div>`
                    : "";

                const statusBadge = `<span class="badge ${isEvaluated ? "badge-evaluated" : "badge-pending"}">
                                        ${isEvaluated ? "Evaluated ✅" : "Pending ⏳"}
                                     </span>`;

                return `
                    <div class="exam-result-card card">
                        <div class="exam-header">
                            <h4>${sub.exam_name} - ${sub.subject}</h4>
                            ${statusBadge}
                        </div>
                        ${marksText}
                        <div class="exam-details">
                            <p><strong>Roll No:</strong> ${sub.roll_number}</p>
                            <p><strong>Type:</strong> ${sub.answer_sheet_type}</p>
                            <p><strong>Uploaded:</strong> ${new Date(sub.timestamp).toLocaleString()}</p>
                        </div>
                        ${feedbackText}
                        <div class="file-list">
                            ${(sub.file_urls || []).map(url => `
                                <a href="${url}" target="_blank" class="file-link">
                                    ${url.endsWith(".pdf") ? "📄 PDF File" : "🖼️ Image"}
                                </a>`).join("<br>")}
                        </div>
                    </div>
                `;
            }).join("");
        } else {
            grid.innerHTML = "<p>❌ No submissions found.</p>";
        }
    } catch (err) {
        console.error(err);
        grid.innerHTML = "<p>⚠️ Failed to load submissions.</p>";
    }
}

// ========== DASHBOARD OVERVIEW STATS ==========
async function loadDashboardStats() {
    const studentEmail = localStorage.getItem("userEmail");
    const examsTakenEl = document.querySelector("#examsTaken");
    const evaluatedEl = document.querySelector("#evaluatedCount");
    const pendingEl = document.querySelector("#pendingCount");
    const averageScoreEl = document.querySelector("#averageScore");

    try {
        const res = await fetch(`http://127.0.0.1:5000/api/get-student-submissions?student=${studentEmail}`);
        const data = await res.json();

        if (!res.ok || !data.submissions.length) {
            updateStatUI(0, 0, 0, 0);
            return;
        }

        const submissions = data.submissions;
        const totalExams = submissions.length;
        const evaluated = submissions.filter(s => s.status === "evaluated");
        const pending = submissions.filter(s => s.status !== "evaluated");

        const avgScore =
            evaluated.length > 0
                ? (
                    evaluated.reduce((sum, s) => sum + (s.marks_obtained || 0), 0) /
                    evaluated.reduce((sum, s) => sum + (s.total_marks || 100), 0)
                  ) * 100
                : 0;

        updateStatUI(totalExams, evaluated.length, pending.length, avgScore);
    } catch (err) {
        console.error("Failed to load dashboard stats:", err);
        updateStatUI(0, 0, 0, 0);
    }

    // Helper to animate number updates
    function updateStatUI(total, evaluated, pending, avgScore) {
        animateValue(examsTakenEl, total);
        animateValue(evaluatedEl, evaluated);
        animateValue(pendingEl, pending);
        averageScoreEl.textContent = `${avgScore.toFixed(1)}%`;
    }
}

// ========== COUNT-UP ANIMATION ==========
function animateValue(el, endValue) {
    if (!el) return;
    const duration = 800;
    const startValue = parseInt(el.textContent) || 0;
    const startTime = performance.now();

    function update(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        const value = Math.floor(startValue + (endValue - startValue) * progress);
        el.textContent = value;
        if (progress < 1) requestAnimationFrame(update);
    }

    requestAnimationFrame(update);
}

// ========== TEACHER VIEW ==========
async function loadStudentSubmissions() {
    const container = document.getElementById("studentSubmissions");
    if (!container) return;
    container.innerHTML = "<p>⏳ Loading submissions...</p>";

    try {
        const res = await fetch("http://127.0.0.1:5000/api/student-submissions");
        const data = await res.json();

        if (res.ok && data.submissions.length) {
            container.innerHTML = data.submissions.map(sub => `
                <div class="submission-card">
                    <h4>${sub.exam_name} - ${sub.subject}</h4>
                    <p><b>Roll:</b> ${sub.roll_number}</p>
                    <div>${(sub.file_urls || []).map(u => `<a href="${u}" target="_blank">${u.endsWith(".pdf") ? "📄" : "🖼️"}</a>`).join(" ")}</div>
                </div>
            `).join("");
        } else container.innerHTML = "<p>No student submissions yet.</p>";
    } catch {
        container.innerHTML = "<p>⚠️ Failed to load submissions.</p>";
    }
}
// ========== TEACHER EVALUATION PANEL ==========
async function loadPendingSubmissions() {
    const grid = document.getElementById("pendingSubmissionsGrid");
    if (!grid) return;
    grid.innerHTML = "<p>⏳ Loading pending submissions...</p>";

    try {
        const res = await fetch("http://127.0.0.1:5000/api/pending-answers");
        const data = await res.json();

        if (res.ok && data.pending.length) {
            grid.innerHTML = data.pending.map(sub => `
                <div class="submission-card" onclick="selectSubmission('${sub.roll_number}', '${sub.student}', '${sub.exam_name}', '${sub.subject}', '${(sub.file_urls && sub.file_urls[0]) || ''}')">
                    <h4>${sub.exam_name} - ${sub.subject}</h4>
                    <p><b>Roll:</b> ${sub.roll_number}</p>
                    <p><b>Student:</b> ${sub.student}</p>
                    <span class="badge badge-pending">Pending ⏳</span>
                </div>
            `).join("");
        } else {
            grid.innerHTML = "<p>✅ All submissions evaluated!</p>";
        }
    } catch (err) {
        grid.innerHTML = "<p>⚠️ Failed to load pending submissions.</p>";
    }
}

// Select a submission for evaluation
function selectSubmission(roll, student, exam, subject, fileUrl) {
    document.getElementById("studentName").textContent = student;
    document.getElementById("examName").textContent = `${exam} (${subject})`;
    document.getElementById("previewPlaceholder").innerHTML =
        fileUrl ? `<iframe src="${fileUrl}" width="100%" height="400px"></iframe>` : "No preview available.";

    const btn = document.getElementById("startEvaluationBtn");
    btn.dataset.roll = roll;
    document.getElementById("evaluationStatus").innerHTML = "";
}

// Start Evaluation (mock AI process)
document.getElementById("startEvaluationBtn")?.addEventListener("click", async e => {
    const roll = e.target.dataset.roll;
    if (!roll) return alert("⚠️ Please select a submission first.");

    const statusDiv = document.getElementById("evaluationStatus");
    statusDiv.innerHTML = "🧠 Running AI Evaluation... Please wait...";

    try {
        const res = await fetch(`http://127.0.0.1:5000/api/start-evaluation/${roll}`, { method: "POST" });
        const data = await res.json();

        if (res.ok) {
            statusDiv.innerHTML = `✅ ${data.message}<br>Marks: ${data.marks_obtained}/100<br>Feedback: ${data.feedback}`;
            await loadPendingSubmissions(); // Refresh list
        } else {
            statusDiv.innerHTML = `❌ ${data.error}`;
        }
    } catch {
        statusDiv.innerHTML = "⚠️ Evaluation failed.";
    }
});


// ========== TEACHER SEARCH + FILTER ==========
document.addEventListener("DOMContentLoaded", () => {
    const searchInput = document.getElementById("submissionSearch");
    const filterSelect = document.getElementById("submissionFilter");
    const submissionsContainer = document.getElementById("studentSubmissions");

    if (searchInput && filterSelect && submissionsContainer) {
        searchInput.addEventListener("input", filterSubmissions);
        filterSelect.addEventListener("change", filterSubmissions);
    }

    function filterSubmissions() {
        const searchText = searchInput.value.toLowerCase();
        const filter = filterSelect.value;

        document.querySelectorAll(".submission-card").forEach(card => {
            const text = card.textContent.toLowerCase();
            const isEvaluated = card.innerHTML.includes("Evaluated ✅");
            const isPending = card.innerHTML.includes("Pending ⏳");

            const matchesSearch = text.includes(searchText);
            const matchesFilter =
                filter === "all" ||
                (filter === "evaluated" && isEvaluated) ||
                (filter === "pending" && isPending);

            card.style.display = matchesSearch && matchesFilter ? "block" : "none";
        });
    }
});

// INIT
document.addEventListener("DOMContentLoaded", () => {
    if (document.getElementById("studentSubmissions")) loadStudentSubmissions();
    if (document.querySelector(".results-grid")) loadStudentResults();
    if (document.getElementById("overview")) loadDashboardStats(); // ✅ Added auto load for stats
});
