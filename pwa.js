(() => {
  'use strict';

  const isInstalled = window.matchMedia('(display-mode: standalone)').matches
    || window.navigator.standalone === true;

  if ('serviceWorker' in navigator && window.isSecureContext) {
    window.addEventListener('load', () => {
      navigator.serviceWorker.register('./service-worker.js', { scope: './' })
        .catch((error) => console.warn('RATIL offline support could not start:', error));
    }, { once: true });
  }

  if (isInstalled) return;

  let installPrompt = null;
  const installButton = document.createElement('button');
  installButton.type = 'button';
  installButton.className = 'ratil-install-button';
  installButton.textContent = 'تثبيت تطبيق RATIL';
  installButton.setAttribute('aria-label', 'تثبيت تطبيق RATIL على الجهاز');
  installButton.style.cssText = [
    'position:fixed',
    'inset-inline-start:16px',
    'bottom:16px',
    'z-index:10000',
    'border:0',
    'border-radius:999px',
    'padding:12px 18px',
    'background:#e67e22',
    'color:#fff',
    'font:600 14px/1.4 Segoe UI,Tahoma,sans-serif',
    'box-shadow:0 4px 14px rgba(0,0,0,.22)',
    'cursor:pointer'
  ].join(';');
  document.body.appendChild(installButton);

  window.addEventListener('beforeinstallprompt', (event) => {
    event.preventDefault();
    installPrompt = event;
  });

  installButton.addEventListener('click', async () => {
    if (!installPrompt) {
      const isAppleMobile = /iphone|ipad|ipod/i.test(navigator.userAgent);
      const instructions = isAppleMobile
        ? 'في Safari اضغط «مشاركة» ثم «إضافة إلى الشاشة الرئيسية».'
        : 'افتح قائمة المتصفح (⋮) واختر «تثبيت التطبيق» أو «إضافة إلى الشاشة الرئيسية».';
      window.alert(instructions);
      return;
    }

    installButton.disabled = true;
    try {
      await installPrompt.prompt();
      const choice = await installPrompt.userChoice;
      if (choice.outcome === 'accepted') installButton.remove();
    } catch (error) {
      console.warn('RATIL installation prompt was not completed:', error);
    } finally {
      installPrompt = null;
      if (installButton.isConnected) installButton.disabled = false;
    }
  });

  window.addEventListener('appinstalled', () => installButton.remove(), { once: true });
})();
