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

    // Update section title dynamically
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
    if (titleElement) {
        titleElement.textContent = titles[sectionId] || 'Dashboard Overview';
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

    // File preview
    answerKeyFileInput.addEventListener('change', function() {
        const file = this.files[0];
        if (file) {
            preview.style.display = 'block';
            previewFileName.textContent = file.name;

            if (file.type.startsWith('image/')) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    previewImage.src = e.target.result;
                };
                reader.readAsDataURL(file);
            } else {
                previewImage.src = '';
            }
        }
    });

    // Upload form handler
    answerKeyForm.addEventListener('submit', async (event) => {
        event.preventDefault();
        const file = answerKeyFileInput.files[0];
        if (!file) {
            alert('Please select a file to upload!');
            return;
        }

        const formData = new FormData();
        formData.append('file', file);
        formData.append('teacher', localStorage.getItem('userEmail') || 'Unknown');

        try {
            const response = await fetch('http://127.0.0.1:5000/api/upload-key', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();
            if (response.ok) {
                alert('✅ ' + data.message);
                answerKeyForm.reset();
                preview.style.display = 'none';
            } else {
                alert('❌ ' + (data.error || 'Upload failed'));
            }
        } catch (error) {
            console.error('Error:', error);
            alert('⚠️ Error connecting to the server.');
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

    // File preview for multiple images
    answerSheetFileInput.addEventListener('change', function() {
        imageGallery.innerHTML = ''; // Clear old previews
        const files = Array.from(this.files);
        if (files.length > 0) {
            previewContainer.style.display = 'block';
            files.forEach(file => {
                if (file.type.startsWith('image/')) {
                    const reader = new FileReader();
                    reader.onload = function(e) {
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

    // Upload handler
    answerSheetForm.addEventListener('submit', async (event) => {
        event.preventDefault();

        const files = answerSheetFileInput.files;
        if (!files.length) {
            alert('Please select files to upload!');
            return;
        }

        // Collect extra info
        const examName = document.getElementById('examName')?.value || '';
        const subject = document.getElementById('subject')?.value || '';
        const rollNumber = document.getElementById('rollNumber')?.value || '';
        const notes = document.getElementById('notes')?.value || '';

        const formData = new FormData();
        Array.from(files).forEach(file => formData.append('files[]', file));
        formData.append('exam_name', examName);
        formData.append('subject', subject);
        formData.append('roll_number', rollNumber);
        formData.append('notes', notes);

        try {
            const response = await fetch('http://127.0.0.1:5000/api/upload-answer', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();
            if (response.ok) {
                alert('✅ ' + data.message);
                answerSheetForm.reset();
                previewContainer.style.display = 'none';
                imageGallery.innerHTML = '';
            } else {
                alert('❌ ' + (data.error || 'Upload failed'));
            }
        } catch (error) {
            console.error('Error:', error);
            alert('⚠️ Error connecting to the server.');
        }
    });
}
