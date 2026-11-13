/* JavaScript utama: tema gelap/terang, navbar, live search, favorit, rating, konfirmasi. */
(function () {
  'use strict';
  var csrf = (document.querySelector('meta[name="csrf-token"]') || {}).content || '';

  function debounce(fn, ms) { var t; return function () { var a = arguments, c = this; clearTimeout(t); t = setTimeout(function () { fn.apply(c, a); }, ms); }; }

  /* ----- Mode gelap/terang (disimpan di localStorage) ----- */
  var themeBtn = document.getElementById('theme-toggle');
  function paintTheme() {
    var dark = document.documentElement.getAttribute('data-theme') === 'dark';
    if (themeBtn) { themeBtn.textContent = dark ? '☀️' : '🌙'; themeBtn.setAttribute('aria-label', dark ? 'Ganti ke mode terang' : 'Ganti ke mode gelap'); }
  }
  if (themeBtn) {
    themeBtn.addEventListener('click', function () {
      var next = document.documentElement.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
      document.documentElement.setAttribute('data-theme', next);
      try { localStorage.setItem('theme', next); } catch (e) {}
      paintTheme();
    });
    paintTheme();
  }

  /* ----- Navbar mobile & dropdown ----- */
  var toggle = document.getElementById('nav-toggle'), links = document.getElementById('nav-links');
  if (toggle && links) toggle.addEventListener('click', function () {
    var open = links.classList.toggle('open'); toggle.setAttribute('aria-expanded', open);
  });
  document.querySelectorAll('.dropdown > [data-dropdown]').forEach(function (btn) {
    btn.addEventListener('click', function (e) { e.stopPropagation(); btn.parentElement.classList.toggle('open'); });
  });
  document.addEventListener('click', function () { document.querySelectorAll('.dropdown.open').forEach(function (d) { d.classList.remove('open'); }); });

  /* ----- Flash message: tutup & hilang otomatis ----- */
  document.querySelectorAll('.flash').forEach(function (f) {
    var btn = f.querySelector('button'); if (btn) btn.addEventListener('click', function () { f.remove(); });
    setTimeout(function () { f.style.opacity = '0'; f.style.transition = 'opacity .4s'; setTimeout(function () { f.remove(); }, 450); }, 7000);
  });

  /* ----- Konfirmasi sebelum aksi berbahaya (hapus, blokir, dll) ----- */
  document.addEventListener('submit', function (e) {
    var msg = e.target.getAttribute('data-confirm');
    if (msg && !window.confirm(msg)) e.preventDefault();
  });

  /* ----- Live search: fetch ke /api/search, hasil dirender dengan textContent (aman dari XSS) ----- */
  document.querySelectorAll('[data-live-search]').forEach(function (box) {
    var input = box.querySelector('input[type=search]'), list = box.querySelector('.search-results'), ctrl = null;
    function clear() { list.hidden = true; list.textContent = ''; }
    function render(results) {
      list.textContent = '';
      if (!results.length) { var e = document.createElement('div'); e.className = 'search-empty'; e.textContent = 'Tidak ada buku yang cocok.'; list.appendChild(e); }
      results.forEach(function (b) {
        var a = document.createElement('a'); a.className = 'search-item'; a.href = b.url;
        var d = document.createElement('div'), t = document.createElement('strong'), s = document.createElement('span');
        t.textContent = b.title; s.textContent = b.author + ' • ' + b.type; d.appendChild(t); d.appendChild(s); a.appendChild(d); list.appendChild(a);
      });
      list.hidden = false;
    }
    input.addEventListener('input', debounce(function () {
      var q = input.value.trim(); if (q.length < 2) return clear();
      if (ctrl) ctrl.abort(); ctrl = new AbortController();
      fetch(box.dataset.endpoint + '?q=' + encodeURIComponent(q), { signal: ctrl.signal })
        .then(function (r) { return r.json(); }).then(function (d) { render(d.results); }).catch(function () {});
    }, 250));
    document.addEventListener('click', function (e) { if (!box.contains(e.target)) clear(); });
    input.addEventListener('keydown', function (e) { if (e.key === 'Escape') clear(); });
  });

  /* ----- Katalog: filter real-time (mengganti grid tanpa reload) ----- */
  var filterForm = document.getElementById('filter-form'), results = document.getElementById('book-results');
  if (filterForm && results) {
    var run = debounce(function () {
      var params = new URLSearchParams(new FormData(filterForm));
      for (var k of Array.from(params.keys())) if (!params.get(k)) params.delete(k);
      var qs = params.toString();
      history.replaceState(null, '', location.pathname + (qs ? '?' + qs : ''));
      params.set('partial', '1');
      results.style.opacity = '.5';
      fetch(location.pathname + '?' + params.toString()).then(function (r) { return r.text(); })
        .then(function (html) { results.innerHTML = html; results.style.opacity = ''; })
        .catch(function () { filterForm.submit(); });
    }, 300);
    filterForm.addEventListener('input', run);
    filterForm.addEventListener('change', run);
    filterForm.addEventListener('submit', function (e) { e.preventDefault(); run(); });
  }

  /* ----- Favorit (toggle via fetch) ----- */
  document.querySelectorAll('[data-fav-form]').forEach(function (form) {
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      var btn = form.querySelector('button');
      fetch(form.action, { method: 'POST', headers: { 'X-CSRFToken': csrf, 'X-Requested-With': 'fetch' } })
        .then(function (r) { if (!r.ok) throw 0; return r.json(); })
        .then(function (d) {
          btn.setAttribute('aria-pressed', d.favorite);
          btn.querySelector('span').textContent = d.favorite ? 'Tersimpan di Favorit' : 'Simpan ke Favorit';
        }).catch(function () { form.submit(); });
    });
  });

  /* ----- Rating bintang interaktif ----- */
  document.querySelectorAll('.star-input').forEach(function (group) {
    var out = group.parentElement.querySelector('.star-text');
    var labels = ['', 'Buruk', 'Kurang', 'Cukup', 'Bagus', 'Luar biasa'];
    group.addEventListener('change', function (e) { if (out) out.textContent = e.target.value + '/5 — ' + labels[e.target.value]; });
  });
})();
