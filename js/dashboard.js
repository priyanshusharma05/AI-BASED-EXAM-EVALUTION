// ------------------------------
// DASHBOARD.JS (Unified for Teacher & Student)
// ------------------------------

// ==============================
// SECTION SWITCHING
// ==============================
function showSection(sectionId) {
    document.querySelectorAll('.content-section').forEach(section => {
        section.classList.remove('active');
    });
    document.getElementById(sectionId).classList.add('active');

    const titles = {
        'overview': 'Dashboard Overview',
        'upload-key': 'Upload Answer Key',
        'submissions': 'View Submissions',
        'evaluate': 'Evaluate Sheets',
        'review': 'Review Results',
        'upload': 'Upload Answer Sheet',
        'results': 'View Results',
        'performance': 'Performance Analytics'
    };
    const titleElement = document.getElementById('section-title');
    if (titleElement) titleElement.textContent = titles[sectionId] || 'Dashboard Overview';
}

// ==============================
// HELPER: Update Upload Status
// ==============================
function updateStatus(containerId, message, success = true) {
    const container = document.getElementById(containerId);
    if (container) {
        container.innerHTML = `
            <div class="upload-status ${success ? 'success' : 'error'}">
                ${success ? '✅' : '❌'} ${message}
            </div>
        `;
        setTimeout(() => { container.innerHTML = ''; }, 5000);
    }
}

// ==============================
// TEACHER: UPLOAD ANSWER KEY
// ==============================
const answerKeyForm = document.getElementById('answerKeyForm');
if (answerKeyForm) {
    const answerKeyFileInput = document.getElementById('answerKeyFile');
    const preview = document.getElementById('answerKeyPreview');
    const previewImage = document.getElementById('answerKeyImage');
    const previewFileName = document.getElementById('answerKeyFileName');

    answerKeyFileInput.addEventListener('change', function() {
        const file = this.files[0];
        if (file) {
            preview.style.display = 'block';
            previewFileName.textContent = file.name;

            if (file.type.startsWith('image/')) {
                const reader = new FileReader();
                reader.onload = e => previewImage.src = e.target.result;
                reader.readAsDataURL(file);
            } else {
                previewImage.src = '';
            }
        }
    });

    answerKeyForm.addEventListener('submit', async (event) => {
        event.preventDefault();
        const file = answerKeyFileInput.files[0];
        if (!file) return alert('Please select a file to upload!');

        const formData = new FormData();
        formData.append('file', file);
        formData.append('teacher', localStorage.getItem('userEmail') || 'Unknown Teacher');

        try {
            const response = await fetch('http://127.0.0.1:5000/api/upload-key', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();
            if (response.ok) {
                updateStatus('teacherUploadStatus', data.message, true);
                answerKeyForm.reset();
                preview.style.display = 'none';
                previewImage.src = '';
                previewFileName.textContent = '';
                loadStudentSubmissions();
            } else {
                updateStatus('teacherUploadStatus', data.error || 'Upload failed', false);
            }
        } catch (error) {
            updateStatus('teacherUploadStatus', 'Error connecting to server.', false);
        }
    });
}

// ==============================
// STUDENT: UPLOAD ANSWER SHEET
// ==============================
const answerSheetForm = document.getElementById('answerSheetForm');
if (answerSheetForm) {
    const answerSheetFileInput = document.getElementById('answerSheetFile');
    const previewContainer = document.getElementById('answerSheetPreview');
    const imageGallery = document.getElementById('imageGallery');

    // Preview uploaded files
    answerSheetFileInput.addEventListener('change', function() {
        imageGallery.innerHTML = '';
        const files = Array.from(this.files);
        if (files.length > 0) {
            previewContainer.style.display = 'block';
            files.forEach(file => {
                if (file.type.startsWith('image/')) {
                    const reader = new FileReader();
                    reader.onload = e => {
                        const img = document.createElement('img');
                        img.src = e.target.result;
                        img.classList.add('preview-thumb');
                        imageGallery.appendChild(img);
                    };
                    reader.readAsDataURL(file);
                }
            });
        } else {
            previewContainer.style.display = 'none';
        }
    });

    // Submit upload form
    answerSheetForm.addEventListener('submit', async (event) => {
        event.preventDefault();

        const files = answerSheetFileInput.files;
        if (!files.length) return alert('Please select files to upload!');

        const formData = new FormData();
        Array.from(files).forEach(file => formData.append('files[]', file));

        // ✅ Collect all student input data
        formData.append('exam_name', document.querySelector('input[placeholder="e.g., Mathematics Final Exam"]')?.value || '');
        formData.append('subject', document.querySelector('input[placeholder="e.g., Mathematics"]')?.value || '');
        formData.append('roll_number', document.querySelector('input[placeholder="e.g., 2024001"]')?.value || '');
        formData.append('notes', document.querySelector('textarea[placeholder*="instructions"]')?.value || '');

        // ✅ Get answer sheet type from dropdown
        const answerSheetType = document.getElementById('answerSheetType')?.value || 'Descriptive';
        formData.append('answer_sheet_type', answerSheetType);

        // ✅ Attach student email
        formData.append('student', localStorage.getItem('userEmail') || 'Unknown Student');

        try {
            const response = await fetch('http://127.0.0.1:5000/api/upload-answer', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();
            if (response.ok) {
                updateStatus('studentUploadStatus', data.message, true);
                answerSheetForm.reset();
                previewContainer.style.display = 'none';
                imageGallery.innerHTML = '';
            } else {
                updateStatus('studentUploadStatus', data.error || 'Upload failed', false);
            }
        } catch (error) {
            updateStatus('studentUploadStatus', 'Error connecting to server.', false);
        }
    });
}

// ==============================
// TEACHER: VIEW STUDENT SUBMISSIONS
// ==============================
async function loadStudentSubmissions() {
    const container = document.getElementById('studentSubmissions');
    if (!container) return;

    try {
        const res = await fetch('http://127.0.0.1:5000/api/student-submissions');
        const data = await res.json();

        if (res.ok && data.submissions.length > 0) {
            container.innerHTML = data.submissions.map(sub => `
                <div class="submission-card">
                    <h4>${sub.exam_name || 'Untitled Exam'} - ${sub.subject || 'N/A'}</h4>
                    <p><strong>Roll No:</strong> ${sub.roll_number || 'Unknown'}</p>
                    <p><strong>Type:</strong> ${sub.answer_sheet_type || 'Descriptive'}</p>
                    <p><strong>Notes:</strong> ${sub.notes || 'None'}</p>
                    <div class="file-list">
                        ${sub.file_urls.map(url => `
                            <a href="${url}" target="_blank" class="file-link">📄 View File</a>
                        `).join('')}
                    </div>
                </div>
            `).join('');
        } else {
            container.innerHTML = '<p>No student submissions yet.</p>';
        }
    } catch (error) {
        container.innerHTML = '<p>⚠️ Failed to load submissions.</p>';
    }
}

// Auto-load student submissions for teacher
document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('studentSubmissions')) {
        loadStudentSubmissions();
    }
});
