/* Admin: form buku — ambil data dari link, pratinjau cover, cari cover otomatis, seret & lepas foto. */
(function () {
  'use strict';
  var csrf = (document.querySelector('meta[name="csrf-token"]') || {}).content || '';
  var $ = function (id) { return document.getElementById(id); };
  var quick = document.querySelector('.quick-add');
  if (!quick) return;

  var preview = $('cover-preview'), empty = $('cover-empty'), coverUrl = $('cover_url'), coverFile = $('cover');
  var status = $('quick-status'), cstatus = $('cover-status');

  function say(el, msg, bad) { el.textContent = msg; el.style.color = bad ? 'var(--danger)' : 'var(--muted)'; }
  function showPreview(src) {
    if (!src) return;
    preview.src = src; preview.hidden = false; if (empty) empty.hidden = true;
  }
  function setVal(id, v) { var el = $(id); if (el && v) el.value = v; }
  function post(url, body) {
    return fetch(url, { method: 'POST', headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf, 'X-Requested-With': 'fetch' }, body: JSON.stringify(body) })
      .then(function (r) { return r.json(); });
  }

  /* ----- 1. Ambil data dari link ----- */
  $('quick-fetch').addEventListener('click', function () {
    var url = $('quick-url').value.trim(), btn = this;
    if (!url) return say(status, 'Tempel link terlebih dahulu.', true);
    btn.disabled = true; say(status, 'Mengambil data…');
    post(quick.dataset.fetchEndpoint, { url: url }).then(function (res) {
      btn.disabled = false;
      if (!res.ok) return say(status, res.error || 'Gagal mengambil data.', true);
      var d = res.data;
      setVal('title', d.title); setVal('author', d.author); setVal('description', d.description);
      setVal('publisher', d.publisher); setVal('year', d.year); setVal('language', d.language); setVal('source', d.source);
      setVal('read_url', d.read_url); setVal('download_url', d.download_url);
      if (d.cover_url) { coverUrl.value = d.cover_url; showPreview(d.cover_url); }
      $('book_type').value = d.book_type || 'digital'; toggleType();
      say(status, '✔ Data terisi. ' + (d.notes || []).join(' '));
    }).catch(function () { btn.disabled = false; say(status, 'Terjadi kesalahan jaringan.', true); });
  });
  $('quick-url').addEventListener('keydown', function (e) { if (e.key === 'Enter') { e.preventDefault(); $('quick-fetch').click(); } });

  /* ----- 2. Pratinjau cover ----- */
  coverFile.addEventListener('change', function () {
    var f = coverFile.files[0];
    if (!f) return;
    if (f.size > 2 * 1024 * 1024) { say(cstatus, 'Ukuran foto melebihi 2 MB.', true); coverFile.value = ''; return; }
    showPreview(URL.createObjectURL(f)); say(cstatus, 'Foto dipilih: ' + f.name + ' (akan diutamakan dibanding URL).');
  });
  coverUrl.addEventListener('change', function () { showPreview(coverUrl.value.trim()); });
  preview.addEventListener('error', function () { if (coverUrl.value) say(cstatus, 'Gambar dari URL ini tidak bisa dimuat. Coba URL lain.', true); });

  /* ----- 3. Seret & lepas foto ----- */
  var dz = $('dropzone');
  ['dragenter', 'dragover'].forEach(function (ev) { dz.addEventListener(ev, function (e) { e.preventDefault(); dz.classList.add('over'); }); });
  ['dragleave', 'drop'].forEach(function (ev) { dz.addEventListener(ev, function (e) { e.preventDefault(); dz.classList.remove('over'); }); });
  dz.addEventListener('drop', function (e) {
    if (e.dataTransfer.files.length) { coverFile.files = e.dataTransfer.files; coverFile.dispatchEvent(new Event('change')); }
  });

  /* ----- 4. Cari cover otomatis ----- */
  $('cover-search').addEventListener('click', function () {
    var title = $('title').value.trim(), author = $('author').value.trim(), box = $('cover-results');
    if (title.length < 2) return say(cstatus, 'Isi judul buku dulu.', true);
    say(cstatus, 'Mencari sampul…'); box.textContent = '';
    fetch(quick.dataset.coverEndpoint + '?title=' + encodeURIComponent(title) + '&author=' + encodeURIComponent(author), { headers: { 'X-Requested-With': 'fetch' } })
      .then(function (r) { return r.json(); }).then(function (res) {
        if (!res.ok) return say(cstatus, res.error, true);
        if (!res.items.length) return say(cstatus, 'Tidak ada sampul yang cocok. Coba ubah judul atau upload foto sendiri.', true);
        say(cstatus, 'Klik gambar untuk memilih:');
        res.items.forEach(function (it) {
          var b = document.createElement('button'); b.type = 'button'; b.title = it.title + ' — ' + it.author;
          var img = document.createElement('img'); img.src = it.thumb; img.alt = it.title; img.loading = 'lazy'; img.referrerPolicy = 'no-referrer';
          b.appendChild(img);
          b.addEventListener('click', function () {
            coverUrl.value = it.cover_url; showPreview(it.cover_url); say(cstatus, '✔ Sampul dipilih.');
            box.querySelectorAll('button').forEach(function (x) { x.classList.remove('picked'); }); b.classList.add('picked');
          });
          box.appendChild(b);
        });
      }).catch(function () { say(cstatus, 'Pencarian gagal (periksa koneksi internet).', true); });
  });

  /* ----- 5. Sesuaikan form dengan jenis buku ----- */
  function toggleType() {
    var digital = $('book_type').value === 'digital';
    $('stock-field').style.display = digital ? 'none' : '';
    document.querySelectorAll('.digital-only').forEach(function (el) { el.style.display = digital ? '' : 'none'; });
  }
  $('book_type').addEventListener('change', toggleType); toggleType();
})();
