"""Katalog awal: kategori & daftar buku (sumber legal). Dipakai oleh seed.py dan make_covers.py.
Buku digital: domain publik (Project Gutenberg, Wikisource), lisensi terbuka (OpenStax, buku CC),
dan koleksi cetak perpustakaan. Buku "Fisik/Pinjam" = katalog koleksi cetak perpustakaan."""
import re


def slugify(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:60] or "buku"


CATEGORIES = [
    ("Novel Gratis", "Novel klasik dunia berstatus domain publik.", "📖"),
    ("Sastra Indonesia Klasik", "Hikayat, syair, dan naskah klasik Nusantara.", "📜"),
    ("Sains & Teknologi", "Fisika, biologi, kimia, dan ilmu alam.", "🔬"),
    ("Pemrograman & Komputer", "Belajar coding dari buku terbuka.", "💻"),
    ("Sejarah & Biografi", "Kisah tokoh dan peristiwa penting.", "🏛️"),
    ("Bisnis & Pengembangan Diri", "Ekonomi, strategi, dan kebiasaan baik.", "💼"),
    ("Agama & Filsafat", "Pemikiran dan kitab klasik.", "🕊️"),
    ("Anak-anak & Komik Edukasi", "Dongeng dan bacaan seru untuk anak.", "🧸"),
]

GUT = "Project Gutenberg"
BSE = "Kemendikbudristek (BSE)"


def gutenberg(gid, title, author, year, cat, desc, lang="Inggris"):
    return dict(cover_url=f"https://www.gutenberg.org/cache/epub/{gid}/pg{gid}.cover.medium.jpg", title=title, author=author, year=year, cat=cat, description=desc, publisher=GUT,
                language=lang, book_type="digital", stock=0,
                read_url=f"https://www.gutenberg.org/cache/epub/{gid}/pg{gid}-images.html",
                download_url=f"https://www.gutenberg.org/ebooks/{gid}.epub.images",
                source=f"Project Gutenberg #{gid} — Domain Publik")


def open_book(title, author, year, cat, desc, url, publisher, license_, lang="Inggris", dl=None):
    return dict(title=title, author=author, year=year, cat=cat, description=desc, publisher=publisher,
                language=lang, book_type="digital", stock=0, read_url=url, download_url=dl or url,
                source=license_)


def wikisource(title, author, year, desc):
    url = "https://id.wikisource.org/wiki/Special:Search?search=" + title.replace(" ", "+")
    return open_book(title, author, year, "Sastra Indonesia Klasik", desc, url, "Wikisource Indonesia",
                     "Wikisource — Domain Publik / naskah klasik", "Melayu/Indonesia")


def textbook(title, desc):
    return open_book(title, "Tim Penulis Kemendikbudristek", 2022, "Buku Pelajaran", desc,
                     "https://buku.kemdikbud.go.id/", BSE,
                     "Buku Sekolah Elektronik — Kemendikbudristek (lisensi terbuka)", "Indonesia")


def physical(title, author, year, cat, desc, publisher, stock):
    return dict(title=title, author=author, year=year, cat=cat, description=desc, publisher=publisher,
                language="Indonesia", book_type="physical", stock=stock, read_url=None, download_url=None,
                source="Koleksi cetak perpustakaan")


BOOKS = [
    # --- Novel Gratis (domain publik, Project Gutenberg)
    gutenberg(1342, "Pride and Prejudice", "Jane Austen", 1813, "Novel Gratis", "Kisah Elizabeth Bennet dan Mr. Darcy tentang prasangka, kelas sosial, dan cinta di Inggris abad ke-19."),
    gutenberg(1661, "The Adventures of Sherlock Holmes", "Arthur Conan Doyle", 1892, "Novel Gratis", "Dua belas kasus detektif Sherlock Holmes yang dicatat oleh sahabatnya, Dr. Watson."),
    gutenberg(11, "Alice's Adventures in Wonderland", "Lewis Carroll", 1865, "Novel Gratis", "Alice jatuh ke lubang kelinci dan menemukan dunia ajaib penuh teka-teki."),
    gutenberg(345, "Dracula", "Bram Stoker", 1897, "Novel Gratis", "Novel epistolari horor gotik tentang Count Dracula dan upaya menghentikannya."),
    gutenberg(84, "Frankenstein", "Mary Shelley", 1818, "Novel Gratis", "Viktor Frankenstein menciptakan makhluk hidup dan menghadapi akibat ambisinya."),
    gutenberg(2701, "Moby Dick", "Herman Melville", 1851, "Novel Gratis", "Perburuan Kapten Ahab terhadap paus putih raksasa di samudra."),
    gutenberg(1400, "Great Expectations", "Charles Dickens", 1861, "Novel Gratis", "Perjalanan Pip dari anak yatim miskin menjadi pria terpandang di London."),
    gutenberg(98, "A Tale of Two Cities", "Charles Dickens", 1859, "Novel Gratis", "Kisah cinta dan pengorbanan di London dan Paris pada masa Revolusi Prancis."),
    gutenberg(1260, "Jane Eyre", "Charlotte Brontë", 1847, "Novel Gratis", "Perjalanan seorang yatim piatu yang mandiri menjadi guru privat di Thornfield Hall."),
    gutenberg(768, "Wuthering Heights", "Emily Brontë", 1847, "Novel Gratis", "Kisah cinta Heathcliff dan Catherine di dataran tinggi Yorkshire yang suram."),
    gutenberg(174, "The Picture of Dorian Gray", "Oscar Wilde", 1890, "Novel Gratis", "Potret seorang pemuda menua menggantikan dirinya, sementara ia terjerumus hedonisme."),
    gutenberg(120, "Treasure Island", "Robert Louis Stevenson", 1883, "Novel Gratis", "Petualangan Jim Hawkins mencari harta karun bersama para bajak laut."),
    gutenberg(35, "The Time Machine", "H. G. Wells", 1895, "Novel Gratis", "Seorang penemu berkelana ke tahun 802.701 dan menemukan masa depan umat manusia."),
    gutenberg(36, "The War of the Worlds", "H. G. Wells", 1898, "Novel Gratis", "Invasi makhluk Mars ke Inggris dalam salah satu fiksi ilmiah awal paling berpengaruh."),
    gutenberg(164, "Twenty Thousand Leagues Under the Sea", "Jules Verne", 1870, "Novel Gratis", "Penjelajahan dasar laut bersama Kapten Nemo dan kapal selam Nautilus."),
    gutenberg(103, "Around the World in Eighty Days", "Jules Verne", 1872, "Novel Gratis", "Phileas Fogg bertaruh mengelilingi dunia dalam delapan puluh hari."),
    gutenberg(514, "Little Women", "Louisa May Alcott", 1868, "Novel Gratis", "Kisah empat saudari March yang tumbuh dewasa pada masa Perang Saudara Amerika."),
    gutenberg(74, "The Adventures of Tom Sawyer", "Mark Twain", 1876, "Novel Gratis", "Petualangan Tom Sawyer yang nakal di tepi Sungai Mississippi."),
    # --- Sastra Indonesia klasik (naskah klasik / domain publik)
    wikisource("Hikayat Hang Tuah", "Anonim", 1700, "Hikayat Melayu klasik tentang kesetiaan dan keperkasaan laksamana Hang Tuah."),
    wikisource("Sejarah Melayu", "Tun Sri Lanang (penyusun)", 1612, "Kronik Kesultanan Melaka yang juga dikenal sebagai Sulalatus Salatin."),
    wikisource("Gurindam Dua Belas", "Raja Ali Haji", 1847, "Dua belas pasal gurindam nasihat tentang agama, akhlak, dan kehidupan."),
    wikisource("Hikayat Si Miskin", "Anonim", 1800, "Hikayat rakyat tentang pasangan miskin yang akhirnya menjadi raja dan permaisuri."),
    wikisource("Syair Abdul Muluk", "Siti Saleha", 1846, "Syair kisah Abdul Muluk, ditulis oleh seorang penulis perempuan Melayu."),
    wikisource("Hikayat Raja-raja Pasai", "Anonim", 1350, "Naskah tertua tentang awal berdirinya kerajaan Islam Samudra Pasai."),
    wikisource("Babad Tanah Jawi", "Anonim", 1700, "Babad sejarah Jawa dari masa awal hingga kerajaan Mataram."),
    wikisource("Negarakertagama", "Mpu Prapanca", 1365, "Kakawin tentang kejayaan Majapahit pada masa Hayam Wuruk."),
    # --- Sains & Teknologi
    gutenberg(5001, "Relativity: The Special and General Theory", "Albert Einstein", 1916, "Sains & Teknologi", "Penjelasan Einstein sendiri tentang teori relativitas untuk pembaca umum."),
    gutenberg(1228, "On the Origin of Species", "Charles Darwin", 1859, "Sains & Teknologi", "Karya dasar teori evolusi melalui seleksi alam."),
    open_book("University Physics Volume 1", "Samuel J. Ling dkk.", 2016, "Sains & Teknologi", "Buku fisika universitas: mekanika, gelombang, dan termodinamika.", "https://openstax.org/details/books/university-physics-volume-1", "OpenStax", "OpenStax — CC BY 4.0"),
    open_book("Biology 2e", "Mary Ann Clark dkk.", 2018, "Sains & Teknologi", "Buku biologi komprehensif tentang sel, genetika, evolusi, dan ekologi.", "https://openstax.org/details/books/biology-2e", "OpenStax", "OpenStax — CC BY 4.0"),
    open_book("Chemistry 2e", "Paul Flowers dkk.", 2019, "Sains & Teknologi", "Dasar-dasar kimia: atom, ikatan, reaksi, dan termokimia.", "https://openstax.org/details/books/chemistry-2e", "OpenStax", "OpenStax — CC BY 4.0"),
    # --- Pemrograman & Komputer
    open_book("Think Python (2nd Edition)", "Allen B. Downey", 2015, "Pemrograman & Komputer", "Pengantar pemrograman Python dengan pendekatan berpikir seperti ilmuwan komputer.", "https://greenteapress.com/wp/think-python-2e/", "Green Tea Press", "Creative Commons BY-NC"),
    open_book("Automate the Boring Stuff with Python", "Al Sweigart", 2019, "Pemrograman & Komputer", "Otomatisasi tugas harian dengan Python untuk pemula.", "https://automatetheboringstuff.com/", "No Starch Press", "Creative Commons BY-NC-SA"),
    open_book("Eloquent JavaScript", "Marijn Haverbeke", 2018, "Pemrograman & Komputer", "Panduan modern JavaScript: bahasa, browser, dan Node.js.", "https://eloquentjavascript.net/", "No Starch Press", "Creative Commons BY-NC"),
    open_book("Pro Git", "Scott Chacon & Ben Straub", 2014, "Pemrograman & Komputer", "Buku resmi Git: dari dasar hingga lanjutan.", "https://git-scm.com/book/id/v2", "Apress", "Creative Commons BY-NC-SA"),
    open_book("The Rust Programming Language", "Steve Klabnik & Carol Nichols", 2018, "Pemrograman & Komputer", "Buku resmi bahasa Rust yang aman dan cepat.", "https://doc.rust-lang.org/book/", "Rust Project", "MIT / Apache-2.0"),
    open_book("Python for Everybody", "Charles Severance", 2016, "Pemrograman & Komputer", "Pengantar Python, data, dan web untuk semua orang.", "https://www.py4e.com/book", "Charles Severance", "Creative Commons BY"),
    # --- Sejarah & Biografi
    gutenberg(20203, "The Autobiography of Benjamin Franklin", "Benjamin Franklin", 1791, "Sejarah & Biografi", "Kisah hidup negarawan, ilmuwan, dan penulis Amerika."),
    gutenberg(23, "Narrative of the Life of Frederick Douglass", "Frederick Douglass", 1845, "Sejarah & Biografi", "Kesaksian seorang budak yang berhasil bebas dan menjadi tokoh abolisionis."),
    gutenberg(2397, "The Story of My Life", "Helen Keller", 1903, "Sejarah & Biografi", "Perjalanan hidup Helen Keller yang tuli dan buta dalam menaklukkan bahasa."),
    gutenberg(1232, "The Prince", "Niccolò Machiavelli", 1532, "Sejarah & Biografi", "Risalah politik klasik tentang kekuasaan dan strategi pemerintahan."),
    # --- Bisnis & Pengembangan Diri
    gutenberg(3300, "The Wealth of Nations", "Adam Smith", 1776, "Bisnis & Pengembangan Diri", "Karya dasar ekonomi modern tentang pasar, pembagian kerja, dan kekayaan."),
    gutenberg(132, "The Art of War", "Sun Tzu", -500, "Bisnis & Pengembangan Diri", "Risalah strategi Tiongkok kuno yang dipakai juga dalam bisnis dan kepemimpinan."),
    gutenberg(4507, "As a Man Thinketh", "James Allen", 1903, "Bisnis & Pengembangan Diri", "Esai singkat tentang kekuatan pikiran dalam membentuk karakter dan hidup."),
    physical("Atomic Habits (Edisi Indonesia)", "James Clear", 2019, "Bisnis & Pengembangan Diri", "Cara praktis membangun kebiasaan kecil yang memberi hasil besar.", "Gramedia Pustaka Utama", 4),
    physical("Filosofi Teras", "Henry Manampiring", 2018, "Bisnis & Pengembangan Diri", "Pengantar filsafat Stoa untuk menghadapi emosi negatif dalam hidup modern.", "Kompas", 3),
    # --- Agama & Filsafat
    gutenberg(2680, "Meditations", "Marcus Aurelius", 180, "Agama & Filsafat", "Catatan pribadi kaisar Romawi tentang ketenangan, kewajiban, dan kebajikan."),
    gutenberg(1497, "The Republic", "Plato", -380, "Agama & Filsafat", "Dialog Plato tentang keadilan, negara ideal, dan filsuf-raja."),
    gutenberg(8438, "The Nicomachean Ethics", "Aristoteles", -340, "Agama & Filsafat", "Pembahasan Aristoteles tentang kebajikan dan kebahagiaan sebagai tujuan hidup."),
    gutenberg(1656, "Apology", "Plato", -399, "Agama & Filsafat", "Pembelaan Socrates di hadapan pengadilan Athena."),
    physical("Dunia Sophie", "Jostein Gaarder", 1991, "Agama & Filsafat", "Novel pengantar sejarah filsafat Barat melalui surat-surat misterius.", "Mizan", 3),
    # --- Anak-anak & Komik Edukasi
    gutenberg(11339, "Aesop's Fables", "Aesop", -550, "Anak-anak & Komik Edukasi", "Kumpulan fabel dengan pesan moral tentang hewan dan manusia."),
    gutenberg(2591, "Grimms' Fairy Tales", "Jacob & Wilhelm Grimm", 1812, "Anak-anak & Komik Edukasi", "Dongeng klasik seperti Hansel dan Gretel serta Putri Salju."),
    gutenberg(1597, "Andersen's Fairy Tales", "Hans Christian Andersen", 1837, "Anak-anak & Komik Edukasi", "Dongeng Si Itik Buruk Rupa, Putri Duyung, dan lainnya."),
    gutenberg(236, "The Jungle Book", "Rudyard Kipling", 1894, "Anak-anak & Komik Edukasi", "Petualangan Mowgli yang dibesarkan serigala di hutan India."),
    gutenberg(55, "The Wonderful Wizard of Oz", "L. Frank Baum", 1900, "Anak-anak & Komik Edukasi", "Dorothy menyusuri Jalan Bata Kuning menuju Kota Zamrud."),
    gutenberg(16, "Peter Pan", "J. M. Barrie", 1911, "Anak-anak & Komik Edukasi", "Anak laki-laki yang tak mau dewasa dan petualangannya di Neverland."),
    physical("Komik Edukasi: Menjelajah Tata Surya", "Tim Penulis Komik Sains", 2020, "Anak-anak & Komik Edukasi", "Komik sains bergambar tentang planet, bintang, dan roket untuk anak.", "Penerbit Edukomik", 5),
    # --- Koleksi cetak (khusus pinjam)
    physical("Laskar Pelangi", "Andrea Hirata", 2005, "Sastra Indonesia Klasik", "Kisah sepuluh anak Belitung yang berjuang bersekolah di tengah keterbatasan.", "Bentang Pustaka", 4),
    physical("Bumi Manusia", "Pramoedya Ananta Toer", 1980, "Sastra Indonesia Klasik", "Kisah Minke pada masa kolonial, bagian pertama Tetralogi Buru.", "Lentera Dipantara", 3),
    physical("Sapiens: Riwayat Singkat Umat Manusia", "Yuval Noah Harari", 2011, "Sejarah & Biografi", "Sejarah manusia dari zaman batu hingga era teknologi.", "Kepustakaan Populer Gramedia", 3),
    physical("Clean Code (Edisi Indonesia)", "Robert C. Martin", 2008, "Pemrograman & Komputer", "Prinsip menulis kode yang bersih, mudah dibaca, dan mudah dirawat.", "Prentice Hall", 2),
    physical("Ensiklopedia Sains Anak Indonesia", "Tim Redaksi", 2018, "Anak-anak & Komik Edukasi", "Ensiklopedia bergambar tentang alam, tubuh manusia, dan teknologi.", "Erlangga", 4),
]


# ---- Tambahan buku (catalog_extra.py): 71 buku awal + 187 = 258 ----
from catalog_extra import build_extra  # noqa: E402

BOOKS.extend(build_extra(gutenberg, open_book, wikisource, textbook, physical))

# Setiap buku mendapat gambar sampul lokal (static/img/covers/<slug>.png) sebagai cadangan.
# Buku Project Gutenberg juga memakai sampul asli dari situs Gutenberg bila internet tersedia.
for _b in BOOKS:
    _b["cover_fallback"] = "img/covers/" + slugify(_b["title"]) + ".png"
