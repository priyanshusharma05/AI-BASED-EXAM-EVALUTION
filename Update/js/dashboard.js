// ------------------------------
// DASHBOARD.JS (Updated)
// ------------------------------

// Handle section switching (existing feature)
function showSection(sectionId) {
    document.querySelectorAll('.content-section').forEach(section => {
        section.classList.remove('active');
    });
    document.getElementById(sectionId).classList.add('active');

    // Update title dynamically
    const titles = {
        'overview': 'Dashboard Overview',
        'upload-key': 'Upload Answer Key',
        'submissions': 'View Submissions',
        'evaluate': 'Evaluate Sheets',
        'review': 'Review Results'
    };
    document.getElementById('section-title').textContent = titles[sectionId] || 'Dashboard Overview';
}

// ------------------------------
// File Upload Logic
// ------------------------------
const answerKeyForm = document.getElementById('answerKeyForm');
const answerKeyFileInput = document.getElementById('answerKeyFile');
const preview = document.getElementById('answerKeyPreview');
const previewImage = document.getElementById('answerKeyImage');
const previewFileName = document.getElementById('answerKeyFileName');

// Show preview when a file is selected
answerKeyFileInput.addEventListener('change', function() {
    const file = this.files[0];
    if (file) {
        preview.style.display = 'block';
        previewFileName.textContent = file.name;

        // Show image preview if image file
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

// Handle form submit
answerKeyForm.addEventListener('submit', async (event) => {
    event.preventDefault(); // stop page reload

    const file = answerKeyFileInput.files[0];
    if (!file) {
        alert('Please select a file to upload!');
        return;
    }

    // Prepare data for Flask
    const formData = new FormData();
    formData.append('file', file);

    try {
        const response = await fetch('http://127.0.0.1:5000/api/upload-key', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();
        if (response.ok) {
            alert('✅ ' + data.message);
            console.log('Uploaded:', data);
        } else {
            alert('❌ ' + (data.error || 'Upload failed'));
        }
    } catch (error) {
        console.error('Error:', error);
        alert('⚠️ Error connecting to the server.');
    }
});
