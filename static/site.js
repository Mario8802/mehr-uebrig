'use strict';
document.documentElement.classList.add('js');
document.querySelectorAll('input[type="password"]').forEach((input) => {
  const toggle = document.createElement('button');
  toggle.type = 'button';
  toggle.className = 'password-toggle';
  toggle.textContent = 'Passwort anzeigen';
  toggle.setAttribute('aria-controls', input.id);
  toggle.setAttribute('aria-pressed', 'false');
  toggle.addEventListener('click', () => {
    const show = input.type === 'password';
    input.type = show ? 'text' : 'password';
    toggle.textContent = show ? 'Passwort verbergen' : 'Passwort anzeigen';
    toggle.setAttribute('aria-pressed', String(show));
  });
  input.insertAdjacentElement('afterend', toggle);
});
