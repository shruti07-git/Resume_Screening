// upload.js — shows selected files and enables drag-drop
document.addEventListener('DOMContentLoaded', () => {
  const dropzone = document.getElementById('dropzone');
  const fileInput = document.getElementById('resumes');
  const fileList = document.getElementById('fileList');
  const resetBtn = document.getElementById('resetBtn');

  function updateFileList() {
    const files = Array.from(fileInput.files || []);
    if (!files.length) {
      fileList.textContent = 'No files selected';
      return;
    }
    fileList.innerHTML = files.map(f => `${f.name} <span class="muted small">(${Math.round(f.size/1024)} KB)</span>`).join('<br>');
  }

  dropzone.addEventListener('click', (e) => fileInput.click());
  dropzone.addEventListener('dragover', (e) => { e.preventDefault(); dropzone.style.borderColor = '#cfe8ff'; });
  dropzone.addEventListener('dragleave', (e) => { dropzone.style.borderColor = ''; });
  dropzone.addEventListener('drop', (e) => {
    e.preventDefault();
    if (e.dataTransfer.files) {
      fileInput.files = e.dataTransfer.files;
      updateFileList();
    }
  });

  fileInput.addEventListener('change', updateFileList);
  if (resetBtn) resetBtn.addEventListener('click', () => { fileInput.value = ''; updateFileList(); });
});
