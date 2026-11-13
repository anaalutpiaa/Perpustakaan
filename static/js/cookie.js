/* Cookie consent: banner, pengaturan, simpan pilihan 365 hari di cookie "cookie_consent".
   Format nilai: n=1&a=<0|1>&m=<0|1>. Server (Flask) juga membaca & memvalidasi cookie ini. */
(function () {
  var banner = document.getElementById('cookie-banner');
  var modal = document.getElementById('cookie-modal');
  if (!banner || !modal) return;
  var csrf = (document.querySelector('meta[name="csrf-token"]') || {}).content || '';
  var chkA = document.getElementById('cc-analytics');
  var chkM = document.getElementById('cc-marketing');

  function setCookie(a, m) {
    var d = new Date();
    d.setTime(d.getTime() + 365 * 24 * 60 * 60 * 1000); // 365 hari
    var value = 'n=1&a=' + (a ? 1 : 0) + '&m=' + (m ? 1 : 0);
    document.cookie = 'cookie_consent=' + value + '; expires=' + d.toUTCString() + '; path=/; SameSite=Lax' +
      (location.protocol === 'https:' ? '; Secure' : '');
  }

  function save(a, m) {
    setCookie(a, m);
    // Kirim ke Flask agar pilihan divalidasi dan dicatat ulang di sisi server
    fetch(banner.dataset.endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf, 'X-Requested-With': 'fetch' },
      body: JSON.stringify({ analytics: a, marketing: m })
    }).catch(function () {});
    banner.hidden = true;
    modal.hidden = true;
    banner.dataset.analytics = a ? '1' : '0';
    banner.dataset.marketing = m ? '1' : '0';
  }

  function openSettings() {
    chkA.checked = banner.dataset.analytics === '1';
    chkM.checked = banner.dataset.marketing === '1';
    modal.hidden = false;
    chkA.focus();
  }

  document.getElementById('cc-accept').addEventListener('click', function () { save(true, true); });
  document.getElementById('cc-necessary').addEventListener('click', function () { save(false, false); });
  document.getElementById('cc-settings').addEventListener('click', openSettings);
  document.getElementById('cc-save').addEventListener('click', function () { save(chkA.checked, chkM.checked); });
  document.getElementById('cc-close').addEventListener('click', function () { modal.hidden = true; });
  modal.addEventListener('click', function (e) { if (e.target === modal) modal.hidden = true; });
  document.addEventListener('keydown', function (e) { if (e.key === 'Escape') modal.hidden = true; });
  // Tombol "Pengaturan Cookie" di footer
  document.querySelectorAll('[data-open-cookie]').forEach(function (b) { b.addEventListener('click', openSettings); });
})();
