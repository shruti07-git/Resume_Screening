// results.js — filter, sort, toggle snippet
document.addEventListener('DOMContentLoaded', () => {
  const searchInput = document.getElementById('searchInput');
  const sortSelect = document.getElementById('sortSelect');
  const rowsContainer = document.getElementById('rows');

  // Toggle snippet view
  rowsContainer.addEventListener('click', (e) => {
    if (e.target && e.target.classList.contains('toggle-snippet')) {
      const rowWrap = e.target.closest('.row-wrap');
      if (!rowWrap) return;
      const snippet = rowWrap.querySelector('.snippet-box');
      if (!snippet) return;
      snippet.classList.toggle('hidden');
      e.target.textContent = snippet.classList.contains('hidden') ? 'View' : 'Hide';
    }
  });

  // Filter by search (name, email, skills)
  searchInput.addEventListener('input', () => {
    const q = searchInput.value.trim().toLowerCase();
    Array.from(rowsContainer.children).forEach((wrap) => {
      const name = (wrap.dataset.name || '').toLowerCase();
      const skills = (wrap.dataset.skills || '').toLowerCase();
      const score = (wrap.dataset.score || '');
      if (!q || name.includes(q) || skills.includes(q) || score.includes(q)) {
        wrap.style.display = '';
      } else {
        wrap.style.display = 'none';
      }
    });
  });

  // Sorting function — reorders row-wrap elements
  function sortRows(mode) {
    const rows = Array.from(rowsContainer.children);
    const getName = (wrap) => (wrap.dataset.name || '').toLowerCase();
    if (mode === 'score_desc') {
      rows.sort((a,b) => parseFloat(b.dataset.score||0) - parseFloat(a.dataset.score||0));
    } else if (mode === 'score_asc') {
      rows.sort((a,b) => parseFloat(a.dataset.score||0) - parseFloat(b.dataset.score||0));
    } else if (mode === 'name_asc') {
      rows.sort((a,b) => getName(a).localeCompare(getName(b)));
    } else if (mode === 'name_desc') {
      rows.sort((a,b) => getName(b).localeCompare(getName(a)));
    }
    rows.forEach(r => rowsContainer.appendChild(r));
  }

  sortSelect.addEventListener('change', () => sortRows(sortSelect.value));
  // initial sort by score descending
  sortRows('score_desc');
});
