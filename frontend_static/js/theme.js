(function() {
  const icon = document.getElementById('theme-icon');
  const text = document.getElementById('theme-text');

  function setDark() {
    document.documentElement.classList.add('dark');
    if (icon) icon.textContent = '☀️';
    if (text) text.textContent = 'Light';
    localStorage.setItem('theme', 'dark');
  }

  function setLight() {
    document.documentElement.classList.remove('dark');
    if (icon) icon.textContent = '🌙';
    if (text) text.textContent = 'Dark';
    localStorage.setItem('theme', 'light');
  }

  window.toggleTheme = function() {
    if (document.documentElement.classList.contains('dark')) {
      setLight();
    } else {
      setDark();
    }
  };

  document.addEventListener('DOMContentLoaded', () => {
    const saved = localStorage.getItem('theme');
    if (saved === 'dark') setDark();
    else setLight();
  });
})();
