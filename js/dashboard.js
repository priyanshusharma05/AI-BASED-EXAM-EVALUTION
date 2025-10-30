const API_BASE = "http://172.16.56.61:5000/api";

// ✅ Upload Answer Key (Teacher)
document.getElementById('answerKeyForm')?.addEventListener('submit', async function(e) {
  e.preventDefault();
  const fileInput = document.getElementById('answerKeyFile');
  const file = fileInput.files[0];
  const teacher = localStorage.getItem('userEmail');

  if (!file) return alert("Please select a file first.");

  const formData = new FormData();
  formData.append("file", file);
  formData.append("teacher", teacher);

  try {
    const res = await fetch(`${API_BASE}/upload-key`, {
      method: "POST",
      body: formData
    });

    const data = await res.json();
    alert(data.message || data.error);
  } catch (error) {
    alert("Upload failed: " + error.message);
  }
});

// ✅ Upload Answer Sheets (Student)
document.getElementById('answerSheetForm')?.addEventListener('submit', async function(e) {
  e.preventDefault();
  const files = document.getElementById('answerSheetFile').files;
  const student = localStorage.getItem('userEmail');

  if (files.length === 0) return alert("Please select at least one file.");

  const formData = new FormData();
  for (let i = 0; i < files.length; i++) {
    formData.append("files[]", files[i]);
  }
  formData.append("student", student);

  try {
    const res = await fetch(`${API_BASE}/upload-sheet`, {
      method: "POST",
      body: formData
    });

    const data = await res.json();
    alert(data.message || data.error);
  } catch (error) {
    alert("Upload failed: " + error.message);
  }
});
