function showSection(sectionId) {
  const sections = document.querySelectorAll('.content-section');
  sections.forEach(section => section.classList.remove('active'));
  
  const targetSection = document.getElementById(sectionId);
  if (targetSection) {
    targetSection.classList.add('active');
  }

  const navItems = document.querySelectorAll('.nav-item');
  navItems.forEach(item => item.classList.remove('active'));
  event.target.closest('.nav-item')?.classList.add('active');

  const titles = {
    'overview': 'Dashboard Overview',
    'upload-key': 'Upload Answer Key',
    'submissions': 'Student Submissions',
    'evaluate': 'Evaluate Answer Sheets',
    'review': 'Review Results',
    'upload': 'Upload Answer Sheet',
    'results': 'Exam Results',
    'performance': 'Performance Analytics'
  };
  
  const titleElement = document.getElementById('section-title');
  if (titleElement && titles[sectionId]) {
    titleElement.textContent = titles[sectionId];
  }
}

document.getElementById('answerKeyFile')?.addEventListener('change', function(e) {
  const file = e.target.files[0];
  if (file) {
    const reader = new FileReader();
    reader.onload = function(event) {
      document.querySelector('.upload-placeholder').style.display = 'none';
      document.getElementById('answerKeyPreview').style.display = 'block';
      
      if (file.type.startsWith('image/')) {
        document.getElementById('answerKeyImage').src = event.target.result;
        document.getElementById('answerKeyImage').style.display = 'block';
      }
      document.getElementById('answerKeyFileName').textContent = file.name;
    };
    reader.readAsDataURL(file);
  }
});

document.getElementById('answerSheetFile')?.addEventListener('change', function(e) {
  const files = e.target.files;
  if (files.length > 0) {
    document.querySelector('#answerSheetUpload .upload-placeholder').style.display = 'none';
    document.getElementById('answerSheetPreview').style.display = 'block';
    
    const gallery = document.getElementById('imageGallery');
    gallery.innerHTML = '';
    
    Array.from(files).forEach(file => {
      if (file.type.startsWith('image/')) {
        const reader = new FileReader();
        reader.onload = function(event) {
          const img = document.createElement('img');
          img.src = event.target.result;
          gallery.appendChild(img);
        };
        reader.readAsDataURL(file);
      }
    });
  }
});

document.getElementById('answerKeyForm')?.addEventListener('submit', function(e) {
  e.preventDefault();
  alert('Answer key uploaded successfully!');
  this.reset();
  document.querySelector('.upload-placeholder').style.display = 'block';
  document.getElementById('answerKeyPreview').style.display = 'none';
});

document.getElementById('answerSheetForm')?.addEventListener('submit', function(e) {
  e.preventDefault();
  alert('Answer sheet submitted successfully! You will be notified once evaluation is complete.');
  this.reset();
  document.querySelector('#answerSheetUpload .upload-placeholder').style.display = 'block';
  document.getElementById('answerSheetPreview').style.display = 'none';
});

function startEvaluation() {
  const progressDiv = document.getElementById('evaluationProgress');
  const resultDiv = document.getElementById('evaluationResult');
  const progressFill = document.getElementById('progressFill');
  const progressText = document.getElementById('progressText');
  
  progressDiv.style.display = 'block';
  resultDiv.style.display = 'none';
  
  let progress = 0;
  const interval = setInterval(() => {
    progress += 10;
    progressFill.style.width = progress + '%';
    progressText.textContent = `Processing... ${progress}%`;
    
    if (progress >= 100) {
      clearInterval(interval);
      setTimeout(() => {
        progressDiv.style.display = 'none';
        resultDiv.style.display = 'block';
      }, 500);
    }
  }, 300);
}

function showDetailedResult() {
  const modal = document.getElementById('resultModal');
  if (modal) {
    modal.classList.add('active');
  }
}

function closeModal() {
  const modal = document.getElementById('resultModal');
  if (modal) {
    modal.classList.remove('active');
  }
}

window.onclick = function(event) {
  const modal = document.getElementById('resultModal');
  if (event.target === modal) {
    modal.classList.remove('active');
  }
}
