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
    if (sectionId === "evaluate") loadPendingSubmissions(); // Load pending submissions when entering evaluate section
}

// STATUS DISPLAY
function updateStatus(id, message, success = true) {
    const el = document.getElementById(id);
    if (!el) return;
    el.innerHTML = `<div class="upload-status ${success ? "success" : "error"}">${success ? "✅" : "❌"} ${message}</div>`;
    setTimeout(() => (el.innerHTML = ""), 5000);
}

// TOAST NOTIFICATION
function showToast(message, type = "success") {
    let container = document.querySelector(".toast-container");
    if (!container) {
        container = document.createElement("div");
        container.className = "toast-container";
        document.body.appendChild(container);
    }

    const toast = document.createElement("div");
    toast.className = `toast ${type}`;

    const icon = type === "success" ? "✅" : type === "error" ? "❌" : "ℹ️";

    toast.innerHTML = `
        <span class="toast-icon">${icon}</span>
        <span class="toast-message">${message}</span>
    `;

    container.appendChild(toast);

    // Remove after 4 seconds
    setTimeout(() => {
        toast.style.animation = "fadeOut 0.5s ease forwards";
        setTimeout(() => toast.remove(), 500);
    }, 4000);
}

// ========== TEACHER UPLOAD KEY ==========
const answerKeyForm = document.getElementById("answerKeyForm");
if (answerKeyForm) {
    answerKeyForm.addEventListener("submit", async e => {
        e.preventDefault();
        const file = document.getElementById("answerKeyFile").files[0];
        if (!file) return updateStatus("teacherUploadStatus", "No file selected", false);

        console.log("📂 File selected:", file.name);
        console.log("📏 File size:", file.size, "bytes");
        console.log("📄 File type:", file.type);

        // Validate file size (10MB limit)
        const MAX_SIZE = 10 * 1024 * 1024; // 10MB
        if (file.size > MAX_SIZE) {
            console.error("❌ File too large:", file.size);
            return updateStatus("teacherUploadStatus", "File is too large. Max allowed size is 10MB.", false);
        }

        const formData = new FormData();
        formData.append("file", file);
        formData.append("exam_name", document.getElementById("examNameKey").value);
        formData.append("subject", document.getElementById("subjectKey").value);
        formData.append("total_marks", document.getElementById("totalMarks").value);
        formData.append("key_type", document.getElementById("keyType").value);
        formData.append("teacher", localStorage.getItem("userEmail") || "Unknown");

        // Debug logging
        for (let pair of formData.entries()) {
            console.log(pair[0] + ', ' + pair[1]);
        }

        try {
            const res = await fetch(`${window.API_BASE_URL}/api/upload-key`, { method: "POST", body: formData });
            console.log("Upload response status:", res.status);

            const data = await res.json();
            console.log("Upload response data:", data);

            if (!res.ok) {
                console.error("Upload failed:", data);
                let errorMsg = data.detail || data.error || "Upload failed";
                if (typeof errorMsg === 'object') {
                    errorMsg = JSON.stringify(errorMsg);
                }
                updateStatus("teacherUploadStatus", `Error: ${errorMsg}`, false);
            } else {
                updateStatus("teacherUploadStatus", data.message, true);
                loadStudentSubmissions();
            }
        } catch (err) {
            console.error("Upload network error:", err);
            updateStatus("teacherUploadStatus", "Network error or server offline", false);
        }
    });
}

// ========== STUDENT UPLOAD ==========
const answerSheetForm = document.getElementById("answerSheetForm");
if (answerSheetForm) {
    // Load available exams on init
    loadAvailableExams();

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

        const examSelect = document.getElementById("examDropdown");
        const selectedOption = examSelect.options[examSelect.selectedIndex];
        const examName = selectedOption.value;
        const subject = selectedOption.dataset.subject || "General";

        if (!examName) return updateStatus("studentUploadStatus", "Please select an exam", false);

        const formData = new FormData();
        files.forEach(f => formData.append("files", f));
        formData.append("exam_name", examName);
        formData.append("subject", subject);
        formData.append("roll_number", document.getElementById("rollNumber").value);
        formData.append("notes", document.getElementById("notes").value);
        formData.append("answer_sheet_type", document.getElementById("answerSheetTypeDropdown").value);
        formData.append("student", localStorage.getItem("userEmail") || "Unknown");

        const res = await fetch(`${window.API_BASE_URL}/api/upload-answer`, { method: "POST", body: formData });
        const data = await res.json();
        updateStatus("studentUploadStatus", res.ok ? data.message : data.error, res.ok);

        if (res.ok) {
            showToast("Answer sheet uploaded successfully! 🚀", "success");
            await loadStudentResults();
            await loadDashboardStats(); // ✅ Update stats instantly after upload
            showSection("results");
        }
    });
}

// Fetch available exams for dropdown
async function loadAvailableExams() {
    const examSelect = document.getElementById("examDropdown");
    if (!examSelect) return;

    try {
        const res = await fetch(`${window.API_BASE_URL}/api/get-exams`);
        const data = await res.json();

        if (res.ok && data.exams) {
            examSelect.innerHTML = '<option value="">-- Select Exam --</option>';
            data.exams.forEach(exam => {
                const option = document.createElement("option");
                option.value = exam.exam_name;
                option.textContent = exam.exam_name;
                option.dataset.subject = exam.subject;
                examSelect.appendChild(option);
            });
        }
    } catch (err) {
        console.error("Failed to load exams:", err);
    }
}

// ========== LOAD STUDENT RESULTS ==========
async function loadStudentResults() {
    const grid = document.querySelector(".results-grid");
    if (!grid) return;
    const studentEmail = localStorage.getItem("userEmail");
    grid.innerHTML = "<p>⏳ Loading submissions...</p>";

    try {
        const res = await fetch(`${window.API_BASE_URL}/api/get-student-submissions?student=${studentEmail}`);
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
                            <p><strong>Submitted Answer Sheet:</strong></p>
                            ${(sub.file_urls || []).map(url => `
                                <a href="${url}" target="_blank" class="btn btn-sm btn-outline">
                                    ${url.endsWith(".pdf") ? "📄 View PDF" : "🖼️ View Image"}
                                </a>`).join(" ")}
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
    if (document.getElementById("totalExams")) {
        await loadTeacherStats();
    } else if (document.getElementById("examsTaken")) {
        await loadStudentStats();
    }
}

async function loadStudentStats() {
    const studentEmail = localStorage.getItem("userEmail");
    const examsTakenEl = document.querySelector("#examsTaken");
    const evaluatedEl = document.querySelector("#evaluatedCount");
    const pendingEl = document.querySelector("#pendingCount");
    const averageScoreEl = document.querySelector("#averageScore");

    try {
        const res = await fetch(`${window.API_BASE_URL}/api/get-student-submissions?student=${studentEmail}`);
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
        console.error("Failed to load student stats:", err);
        updateStatUI(0, 0, 0, 0);
    }

    function updateStatUI(total, evaluated, pending, avgScore) {
        animateValue(examsTakenEl, total);
        animateValue(evaluatedEl, evaluated);
        animateValue(pendingEl, pending);
        if (averageScoreEl) averageScoreEl.textContent = `${avgScore.toFixed(1)}%`;
    }
}

async function loadTeacherStats() {
    const totalExamsEl = document.querySelector("#totalExams");
    const totalSubmissionsEl = document.querySelector("#totalSubmissions");
    const evaluatedEl = document.querySelector("#evaluatedCount");
    const pendingEl = document.querySelector("#pendingCount");

    try {
        const res = await fetch(`${window.API_BASE_URL}/api/dashboard-stats`);
        const data = await res.json();

        if (res.ok) {
            animateValue(totalExamsEl, data.total_exams || 0);
            animateValue(totalSubmissionsEl, data.total_submissions || 0);
            animateValue(evaluatedEl, data.evaluated || 0);
            animateValue(pendingEl, data.pending || 0);
        }
    } catch (err) {
        console.error("Failed to load teacher stats:", err);
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
        const res = await fetch(`${window.API_BASE_URL}/api/student-submissions`);
        const data = await res.json();

        if (res.ok && data.submissions.length) {
            container.innerHTML = data.submissions.map(sub => {
                const isEvaluated = sub.status === "evaluated";
                const statusBadge = `<span class="badge ${isEvaluated ? "badge-evaluated" : "badge-pending"}">
                    ${isEvaluated ? "Evaluated ✅" : "Pending ⏳"}
                </span>`;

                const marksDisplay = isEvaluated
                    ? `<p><b>Marks:</b> ${sub.marks_obtained}/${sub.total_marks || 100}</p>`
                    : "";

                return `
                    <div class="submission-card">
                        <div class="submission-header">
                            <h4>${sub.exam_name} - ${sub.subject}</h4>
                            ${statusBadge}
                        </div>
                        <p><b>Roll:</b> ${sub.roll_number}</p>
                        <p><b>Student:</b> ${sub.student}</p>
                        <p><b>Type:</b> ${sub.answer_sheet_type}</p>
                        ${marksDisplay}
                        <p><b>Submitted:</b> ${new Date(sub.timestamp).toLocaleString()}</p>
                        <div class="file-links">
                            ${(sub.file_urls || []).map(u =>
                    `<a href="${u}" target="_blank" class="btn btn-sm btn-outline">
                                    ${u.endsWith(".pdf") ? "📄 View PDF" : "🖼️ View Image"}
                                </a>`
                ).join(" ")}
                        </div>
                    </div>
                `;
            }).join("");
        } else {
            container.innerHTML = "<p>No student submissions yet.</p>";
        }
    } catch (err) {
        console.error("Error loading submissions:", err);
        container.innerHTML = "<p>⚠️ Failed to load submissions.</p>";
    }
}
// ========== TEACHER EVALUATION PANEL ==========
async function loadPendingSubmissions() {
    const grid = document.getElementById("pendingSubmissionsGrid");
    if (!grid) return;

    console.log("🔄 Loading pending submissions...");
    grid.innerHTML = "<p>⏳ Loading pending submissions...</p>";

    try {
        const res = await fetch(`${window.API_BASE_URL}/api/pending-answers`);
        console.log("📡 Response status:", res.status);

        if (!res.ok) {
            throw new Error(`Server returned ${res.status}`);
        }

        const data = await res.json();
        console.log("📦 Data received:", data);

        if (data.pending && data.pending.length > 0) {
            grid.innerHTML = data.pending.map(sub => {
                // Escape quotes to prevent syntax errors in onclick
                const safeExam = (sub.exam_name || "").replace(/'/g, "\\'");
                const safeSubject = (sub.subject || "").replace(/'/g, "\\'");
                const safeStudent = (sub.student || "").replace(/'/g, "\\'");
                const safeRoll = (sub.roll_number || "").replace(/'/g, "\\'");
                const safeFile = ((sub.file_urls && sub.file_urls[0]) || "").replace(/'/g, "\\'");

                return `
                <div class="submission-card" onclick="selectSubmission('${safeRoll}', '${safeStudent}', '${safeExam}', '${safeSubject}', '${safeFile}')">
                    <h4>${sub.exam_name} - ${sub.subject}</h4>
                    <p><b>Roll:</b> ${sub.roll_number}</p>
                    <p><b>Student:</b> ${sub.student}</p>
                    <span class="badge badge-pending">Pending ⏳</span>
                </div>
            `}).join("");
        } else {
            grid.innerHTML = "<p>✅ All submissions evaluated!</p>";
        }
    } catch (err) {
        console.error("❌ Error loading submissions:", err);
        grid.innerHTML = `<p class="error-msg">⚠️ Failed to load pending submissions: ${err.message}</p>`;
    }
}

// Select a submission for evaluation
function selectSubmission(roll, student, exam, subject, fileUrl) {
    document.getElementById("studentName").textContent = student;
    document.getElementById("examName").textContent = `${exam} (${subject})`;

    // Update preview
    const previewDiv = document.getElementById("previewPlaceholder");
    if (fileUrl) {
        if (fileUrl.toLowerCase().endsWith('.pdf')) {
            previewDiv.innerHTML = `<iframe src="${fileUrl}" width="100%" height="500px" style="border:none;"></iframe>`;
        } else {
            previewDiv.innerHTML = `<img src="${fileUrl}" style="max-width:100%; max-height:500px; border-radius:8px;">`;
        }
    } else {
        previewDiv.innerHTML = "<p>No preview available.</p>";
    }

    // Enable button
    const btn = document.getElementById("startEvaluationBtn");
    btn.dataset.roll = roll;
    btn.disabled = false;
    btn.textContent = "Start AI Evaluation";

    // Reset status and results
    document.getElementById("evaluationStatus").innerHTML = "";
    document.getElementById("evaluationResult").style.display = "none";
}

// Start Evaluation (Real AI process)
document.getElementById("startEvaluationBtn")?.addEventListener("click", async e => {
    const btn = e.target;
    const roll = btn.dataset.roll;
    if (!roll) return alert("⚠️ Please select a submission first.");

    const statusDiv = document.getElementById("evaluationStatus");
    const resultDiv = document.getElementById("evaluationResult");

    // UI Loading State
    btn.disabled = true;
    btn.textContent = "🧠 AI is Evaluating...";
    statusDiv.innerHTML = `
        <div class="evaluation-loader">
            <div class="spinner"></div>
            <p>Analyzing answer sheet... This may take a minute.</p>
        </div>
    `;
    resultDiv.style.display = "none";

    try {
        // Call Real AI Endpoint
        const res = await fetch(`${window.API_BASE_URL}/api/ai-evaluate/${roll}`, { method: "POST" });
        const data = await res.json();

        if (res.ok) {
            // Success
            statusDiv.innerHTML = `<div class="upload-status success">✅ Evaluation Complete!</div>`;

            // Show Results
            resultDiv.style.display = "block";
            document.getElementById("resultScore").textContent = data.marks_obtained;
            document.getElementById("resultFeedback").textContent = data.feedback;

            // Refresh pending list
            await loadPendingSubmissions();

            btn.textContent = "Evaluation Done";
        } else {
            // Error from API
            statusDiv.innerHTML = `<div class="upload-status error">❌ ${data.detail || data.error || "Evaluation failed"}</div>`;
            btn.disabled = false;
            btn.textContent = "Retry Evaluation";
        }
    } catch (err) {
        console.error(err);
        statusDiv.innerHTML = `<div class="upload-status error">⚠️ Network error or server offline.</div>`;
        btn.disabled = false;
        btn.textContent = "Retry Evaluation";
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
