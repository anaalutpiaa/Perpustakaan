"""Tambahan buku (total katalog 258 judul). Sumber legal: domain publik (Project Gutenberg, Wikisource),
lisensi terbuka (OpenStax, buku CC, dokumentasi resmi), dan koleksi cetak perpustakaan.
Dipanggil dari catalog.py lewat build_extra(). Verifikasi tautan dengan:  python verify_catalog.py"""

NOVEL, SASTRA = "Novel Gratis", "Sastra Indonesia Klasik"
SAINS, PROG, SEJARAH = "Sains & Teknologi", "Pemrograman & Komputer", "Sejarah & Biografi"
BISNIS, AGAMA, ANAK = "Bisnis & Pengembangan Diri", "Agama & Filsafat", "Anak-anak & Komik Edukasi"


def build_extra(gutenberg, open_book, wikisource, textbook, physical):
    B = []
    g = lambda *a: B.append(gutenberg(*a))
    ws = lambda *a: B.append(wikisource(*a))
    ob = lambda *a, **k: B.append(open_book(*a, **k))
    phys = lambda *a: B.append(physical(*a))

    # ------------------------------------------------------------ Novel Gratis (24)
    for row in [
        (2554, "Crime and Punishment", "Fyodor Dostoevsky", 1866, "Raskolnikov, mahasiswa miskin, melakukan pembunuhan dan bergulat dengan rasa bersalah."),
        (2600, "War and Peace", "Leo Tolstoy", 1869, "Epik kehidupan keluarga bangsawan Rusia pada masa invasi Napoleon."),
        (1399, "Anna Karenina", "Leo Tolstoy", 1878, "Tragedi cinta terlarang seorang wanita bangsawan dalam masyarakat Rusia yang kaku."),
        (28054, "The Brothers Karamazov", "Fyodor Dostoevsky", 1880, "Kisah tiga bersaudara dan pembunuhan ayah mereka, penuh perdebatan iman dan moral."),
        (135, "Les Misérables", "Victor Hugo", 1862, "Perjalanan Jean Valjean, mantan narapidana, mencari penebusan di Prancis abad ke-19."),
        (1184, "The Count of Monte Cristo", "Alexandre Dumas", 1844, "Edmond Dantès dipenjara secara keji dan kembali untuk membalas dendam."),
        (1257, "The Three Musketeers", "Alexandre Dumas", 1844, "Petualangan d'Artagnan bersama tiga pengawal raja di Prancis."),
        (996, "Don Quixote", "Miguel de Cervantes", 1605, "Seorang bangsawan tua yang terobsesi kisah kesatria mengembara bersama pengawalnya, Sancho."),
        (219, "Heart of Darkness", "Joseph Conrad", 1899, "Pelayaran menyusuri sungai Kongo menuju sosok misterius bernama Kurtz."),
        (5200, "The Metamorphosis", "Franz Kafka", 1915, "Gregor Samsa terbangun sebagai serangga raksasa dan keluarganya berubah."),
        (215, "The Call of the Wild", "Jack London", 1903, "Anjing bernama Buck kembali ke naluri liar di tanah Yukon yang beku."),
        (45, "Anne of Green Gables", "L. M. Montgomery", 1908, "Anne, gadis yatim berambut merah, mengubah kehidupan sebuah keluarga di Pulau Prince Edward."),
        (76, "Adventures of Huckleberry Finn", "Mark Twain", 1884, "Huck dan Jim berlayar di Sungai Mississippi mencari kebebasan."),
        (158, "Emma", "Jane Austen", 1815, "Emma Woodhouse gemar menjodohkan orang lain hingga salah menilai hatinya sendiri."),
        (730, "Oliver Twist", "Charles Dickens", 1838, "Anak yatim piatu bertahan hidup di antara rumah kerja dan kawanan pencuri London."),
        (766, "David Copperfield", "Charles Dickens", 1850, "Perjalanan hidup David dari masa kecil yang pahit menjadi penulis terkenal."),
        (46, "A Christmas Carol", "Charles Dickens", 1843, "Ebenezer Scrooge yang kikir dikunjungi tiga hantu pada malam Natal."),
        (145, "Middlemarch", "George Eliot", 1871, "Potret masyarakat kota kecil Inggris lewat kisah Dorothea Brooke dan Dr. Lydgate."),
        (110, "Tess of the d'Urbervilles", "Thomas Hardy", 1891, "Tragedi seorang gadis desa yang dihantam moralitas masyarakat Victoria."),
        (2852, "The Hound of the Baskervilles", "Arthur Conan Doyle", 1902, "Sherlock Holmes menyelidiki legenda anjing hantu di rawa Dartmoor."),
        (43, "Strange Case of Dr Jekyll and Mr Hyde", "Robert Louis Stevenson", 1886, "Seorang dokter menciptakan ramuan yang melepaskan sisi gelap dirinya."),
        (5230, "The Invisible Man", "H. G. Wells", 1897, "Ilmuwan yang menjadi tak terlihat perlahan kehilangan kendali."),
        (62, "A Princess of Mars", "Edgar Rice Burroughs", 1912, "Seorang mantan tentara Amerika terlempar ke Mars dan terlibat perang antarbangsa."),
        (829, "Gulliver's Travels", "Jonathan Swift", 1726, "Pelayaran Gulliver ke negeri orang kerdil dan raksasa, satire tajam atas masyarakat."),
    ]:
        g(row[0], row[1], row[2], row[3], NOVEL, row[4])

    # ------------------------------------------------- Sastra Indonesia Klasik (20)
    for row in [
        ("Hikayat Bayan Budiman", "Anonim", 1600, "Kumpulan cerita yang dituturkan seekor burung bayan untuk menunda kepergian tuannya."),
        ("Hikayat Seri Rama", "Anonim", 1600, "Adaptasi Melayu kisah Ramayana: Rama, Sita, dan Rawana."),
        ("Hikayat Pandawa Lima", "Anonim", 1700, "Kisah lima Pandawa dalam tradisi Melayu, berlatar epos Mahabharata."),
        ("Hikayat Amir Hamzah", "Anonim", 1600, "Petualangan paman Nabi, Amir Hamzah, dalam sastra hikayat Melayu."),
        ("Hikayat Iskandar Zulkarnain", "Anonim", 1500, "Kisah pengembaraan Iskandar Agung versi Melayu."),
        ("Hikayat Abdullah", "Abdullah bin Abdul Kadir Munsyi", 1849, "Autobiografi Munsyi Abdullah, karya penting awal sastra Melayu modern."),
        ("Syair Ken Tambuhan", "Anonim", 1700, "Syair tentang cinta Raden Menteri dan Ken Tambuhan yang berakhir tragis."),
        ("Syair Bidasari", "Anonim", 1800, "Syair kisah Bidasari yang dibuang dan akhirnya bertemu raja."),
        ("Syair Perahu", "Hamzah Fansuri", 1600, "Syair sufi tentang perjalanan hidup manusia diibaratkan sebuah perahu."),
        ("Tuhfat al-Nafis", "Raja Ali Haji", 1865, "Sejarah Kesultanan Johor-Riau dan kerabat Bugis, ditulis Raja Ali Haji."),
        ("Bustanus Salatin", "Nuruddin ar-Raniri", 1638, "Ensiklopedia sejarah dunia dan Aceh serta nasihat bagi raja."),
        ("Pararaton", "Anonim", 1500, "Kitab sejarah Singasari-Majapahit, termasuk kisah Ken Arok."),
        ("Sutasoma", "Mpu Tantular", 1380, "Kakawin tentang Pangeran Sutasoma; asal ungkapan Bhinneka Tunggal Ika."),
        ("Arjunawiwaha", "Mpu Kanwa", 1030, "Kakawin tentang pertapaan dan kemenangan Arjuna melawan raksasa."),
        ("Serat Wedhatama", "Mangkunegara IV", 1880, "Tembang Jawa berisi ajaran budi pekerti dan laku batin."),
        ("Serat Kalatidha", "R. Ng. Ranggawarsita", 1860, "Tembang renungan tentang zaman edan karya pujangga terakhir Jawa."),
        ("Serat Centhini", "Anonim", 1814, "Ensiklopedia budaya Jawa tentang agama, adat, seni, dan pengetahuan."),
        ("Azab dan Sengsara", "Merari Siregar", 1920, "Roman awal Balai Pustaka tentang adat dan kisah cinta Mariamin."),
        ("Student Hidjo", "Mas Marco Kartodikromo", 1919, "Roman tentang pelajar Jawa di Belanda dan kehidupan kolonial."),
        ("Boenga Roos dari Tjikembang", "Kwee Tek Hoay", 1927, "Novel sastra Melayu Tionghoa tentang cinta dan adat keluarga."),
    ]:
        ws(*row)

    # ------------------------------------------------------- Sains & Teknologi (20)
    for row in [
        (2300, "The Descent of Man", "Charles Darwin", 1871, "Darwin membahas asal-usul manusia dan seleksi seksual."),
        (3704, "The Voyage of the Beagle", "Charles Darwin", 1839, "Catatan perjalanan keliling dunia yang melahirkan teori evolusi."),
        (33504, "Opticks", "Isaac Newton", 1704, "Eksperimen Newton tentang cahaya, warna, dan pembiasan."),
        (21076, "The Elements (Euclid)", "Euclid", -300, "Dasar geometri yang disusun dengan definisi, aksioma, dan pembuktian."),
        (39714, "Dialogues Concerning Two New Sciences", "Galileo Galilei", 1638, "Galileo membahas kekuatan bahan dan gerak yang dipercepat."),
        (14986, "The Chemical History of a Candle", "Michael Faraday", 1861, "Ceramah populer Faraday tentang kimia di balik nyala lilin."),
        (33283, "Calculus Made Easy", "Silvanus P. Thompson", 1910, "Pengantar kalkulus yang ramah bagi pemula."),
    ]:
        g(row[0], row[1], row[2], row[3], SAINS, row[4])
    OS = "https://openstax.org/details/books/"
    for slug, title, author, year, desc in [
        ("astronomy-2e", "Astronomy 2e", "Andrew Fraknoi dkk.", 2022, "Pengantar astronomi: tata surya, bintang, galaksi, dan kosmologi."),
        ("anatomy-and-physiology-2e", "Anatomy and Physiology 2e", "J. Gordon Betts dkk.", 2022, "Struktur dan fungsi tubuh manusia secara lengkap."),
        ("microbiology", "Microbiology", "Nina Parker dkk.", 2016, "Dasar mikrobiologi: bakteri, virus, jamur, dan imunitas."),
        ("concepts-biology", "Concepts of Biology", "Samantha Fowler dkk.", 2013, "Pengantar konsep biologi untuk pembelajar non-jurusan."),
        ("college-physics-2e", "College Physics 2e", "Paul Peter Urone dkk.", 2022, "Fisika berbasis aljabar untuk perguruan tinggi."),
        ("university-physics-volume-2", "University Physics Volume 2", "Samuel J. Ling dkk.", 2016, "Termodinamika, listrik, dan magnetisme."),
        ("calculus-volume-1", "Calculus Volume 1", "Gilbert Strang & Edwin Herman", 2016, "Limit, turunan, dan integral dasar."),
        ("chemistry-atoms-first-2e", "Chemistry: Atoms First 2e", "Paul Flowers dkk.", 2019, "Kimia yang dimulai dari struktur atom."),
        ("introductory-statistics-2e", "Introductory Statistics 2e", "Barbara Illowsky & Susan Dean", 2023, "Statistika dasar dan penerapannya."),
        ("organic-chemistry", "Organic Chemistry", "Mark Blaser dkk.", 2023, "Struktur, reaksi, dan mekanisme senyawa organik."),
    ]:
        ob(title, author, year, SAINS, desc, OS + slug, "OpenStax", "OpenStax — CC BY 4.0")
    ob("The Feynman Lectures on Physics, Vol. I", "Richard P. Feynman", 1963, SAINS, "Kuliah fisika klasik Feynman: mekanika, radiasi, dan panas.", "https://www.feynmanlectures.caltech.edu/I_toc.html", "Caltech", "Dibaca gratis secara resmi oleh Caltech & Basic Books")
    ob("The Feynman Lectures on Physics, Vol. II", "Richard P. Feynman", 1964, SAINS, "Elektromagnetisme dan materi dalam gaya penjelasan Feynman.", "https://www.feynmanlectures.caltech.edu/II_toc.html", "Caltech", "Dibaca gratis secara resmi oleh Caltech & Basic Books")
    ob("Newtonian Physics (Light and Matter)", "Benjamin Crowell", 1998, SAINS, "Buku fisika mekanika bebas akses dengan penjelasan konseptual.", "https://www.lightandmatter.com/", "Light and Matter", "Creative Commons BY-SA")

    # ---------------------------------------------- Pemrograman & Komputer (22)
    for title, author, year, desc, url, pub, lic in [
        ("Dive Into Python 3", "Mark Pilgrim", 2009, "Panduan Python 3 untuk programmer yang sudah berpengalaman.", "https://diveintopython3.net/", "Mark Pilgrim", "Creative Commons BY-SA"),
        ("A Byte of Python", "Swaroop C H", 2018, "Pengantar Python untuk pemula, tersedia dalam banyak bahasa.", "https://python.swaroopch.com/", "Swaroop C H", "Creative Commons BY-SA"),
        ("Think Java (2nd Edition)", "Allen B. Downey & Chris Mayfield", 2016, "Belajar Java dan dasar pemrograman berorientasi objek.", "https://greenteapress.com/wp/think-java-2e/", "Green Tea Press", "Creative Commons BY-NC-SA"),
        ("Think Stats (2nd Edition)", "Allen B. Downey", 2014, "Statistika dan analisis data memakai Python.", "https://greenteapress.com/wp/think-stats-2e/", "Green Tea Press", "Creative Commons BY-NC"),
        ("Think Data Structures", "Allen B. Downey", 2016, "Struktur data dan algoritma dengan Java.", "https://greenteapress.com/wp/think-data-structures/", "Green Tea Press", "Creative Commons BY-NC-SA"),
        ("Learn You a Haskell for Great Good!", "Miran Lipovača", 2011, "Pengantar pemrograman fungsional dengan Haskell.", "https://learnyouahaskell.github.io/", "No Starch Press", "Creative Commons BY-NC-SA"),
        ("Structure and Interpretation of Computer Programs", "Harold Abelson & Gerald Sussman", 1996, "Teks klasik ilmu komputer MIT tentang abstraksi program.", "https://mitp-content-server.mit.edu/books/content/sectbyfn/books_pres_0/6515/sicp.zip/index.html", "MIT Press", "Creative Commons BY-SA"),
        ("How to Design Programs", "Matthias Felleisen dkk.", 2018, "Metode sistematis merancang program dari dasar.", "https://htdp.org/", "MIT Press", "Creative Commons BY-NC-ND"),
        ("Operating Systems: Three Easy Pieces", "Remzi & Andrea Arpaci-Dusseau", 2018, "Konsep sistem operasi: virtualisasi, konkurensi, dan persistensi.", "https://pages.cs.wisc.edu/~remzi/OSTEP/", "Arpaci-Dusseau Books", "Gratis dibaca (hak cipta penulis)"),
        ("Algorithms", "Jeff Erickson", 2019, "Buku algoritma dengan pembahasan pembuktian yang jernih.", "https://jeffe.cs.illinois.edu/teaching/algorithms/", "Jeff Erickson", "Creative Commons BY 4.0"),
        ("Open Data Structures", "Pat Morin", 2013, "Struktur data dan analisisnya dengan kode Java/C++.", "https://opendatastructures.org/", "AU Press", "Creative Commons BY"),
        ("The Linux Command Line", "William Shotts", 2019, "Panduan lengkap baris perintah Linux dan shell scripting.", "https://linuxcommand.org/tlcl.php", "No Starch Press", "Creative Commons BY-NC-ND"),
        ("Rust by Example", "Komunitas Rust", 2015, "Belajar Rust lewat contoh kode yang dapat dijalankan.", "https://doc.rust-lang.org/rust-by-example/", "Rust Project", "MIT / Apache-2.0"),
        ("Crafting Interpreters", "Robert Nystrom", 2021, "Membuat bahasa pemrograman sendiri dari nol.", "https://craftinginterpreters.com/", "Genever Benning", "Gratis dibaca (CC BY-NC-ND)"),
        ("Dive into Deep Learning", "Aston Zhang dkk.", 2021, "Deep learning interaktif dengan kode dan matematika.", "https://d2l.ai/", "Cambridge University Press", "Creative Commons BY-SA 4.0"),
        ("The Modern JavaScript Tutorial", "Ilya Kantor", 2020, "Tutorial JavaScript dari dasar sampai lanjut.", "https://javascript.info/", "javascript.info", "Creative Commons BY-NC-SA"),
        ("MDN: Learn Web Development", "Komunitas Mozilla", 2020, "Jalur belajar HTML, CSS, dan JavaScript dari nol.", "https://developer.mozilla.org/en-US/docs/Learn_web_development", "Mozilla", "Creative Commons BY-SA 2.5"),
        ("Django Girls Tutorial", "Django Girls", 2014, "Tutorial membuat aplikasi web pertama dengan Django.", "https://tutorial.djangogirls.org/id/", "Django Girls", "Creative Commons BY-SA"),
        ("Beej's Guide to Network Programming", "Brian Hall", 2019, "Panduan pemrograman jaringan dengan socket (bahasa C).", "https://beej.us/guide/bgnet/", "Brian Hall", "Creative Commons BY-NC-ND"),
        ("The Missing Semester of Your CS Education", "Anish Athalye dkk.", 2020, "Alat penting yang jarang diajarkan: shell, Git, debugging.", "https://missing.csail.mit.edu/", "MIT CSAIL", "Creative Commons BY-NC-SA"),
        ("Neural Networks and Deep Learning", "Michael Nielsen", 2015, "Pengantar jaringan saraf tiruan secara intuitif.", "http://neuralnetworksanddeeplearning.com/", "Determination Press", "Creative Commons BY-NC 3.0"),
        ("The Python Tutorial (Dokumentasi Resmi)", "Python Software Foundation", 2023, "Tutorial resmi Python dari tim pengembang Python.", "https://docs.python.org/3/tutorial/", "Python Software Foundation", "PSF License"),
    ]:
        ob(title, author, year, PROG, desc, url, pub, lic)

    # ------------------------------------------------------- Sejarah & Biografi (17)
    for row in [
        (2376, "Up from Slavery", "Booker T. Washington", 1901, "Autobiografi tokoh pendidikan Amerika yang lahir sebagai budak."),
        (408, "The Souls of Black Folk", "W. E. B. Du Bois", 1903, "Kumpulan esai tentang pengalaman dan perjuangan warga kulit hitam Amerika."),
        (2022, "Twelve Years a Slave", "Solomon Northup", 1853, "Kesaksian seorang pria bebas yang diculik dan dijual sebagai budak."),
        (7142, "The History of the Peloponnesian War", "Thucydides", -400, "Sejarah perang Athena melawan Sparta, tonggak historiografi."),
        (2707, "The Histories", "Herodotus", -430, "Karya sejarah awal tentang perang Yunani-Persia dan dunia kuno."),
        (10657, "Commentaries on the Gallic War", "Julius Caesar", -50, "Catatan Caesar sendiri tentang penaklukan Galia."),
        (6400, "The Twelve Caesars", "Suetonius", 121, "Biografi dua belas kaisar Romawi pertama."),
        (10636, "The Travels of Marco Polo", "Marco Polo", 1300, "Kisah perjalanan pedagang Venesia menuju Tiongkok dan Asia."),
        (815, "Democracy in America, Volume 1", "Alexis de Tocqueville", 1835, "Pengamatan klasik tentang demokrasi dan masyarakat Amerika."),
        (1404, "The Federalist Papers", "Hamilton, Madison & Jay", 1788, "Esai pendiri Amerika tentang pemerintahan dan konstitusi."),
        (4367, "Personal Memoirs of U. S. Grant", "Ulysses S. Grant", 1885, "Memoar jenderal dan presiden Amerika tentang Perang Saudara."),
        (4200, "The Diary of Samuel Pepys", "Samuel Pepys", 1669, "Catatan harian kehidupan London abad ke-17, termasuk Wabah Besar."),
    ]:
        g(row[0], row[1], row[2], row[3], SEJARAH, row[4])
    phys = lambda *a: B.append(physical(*a))
    phys("Soekarno: Penyambung Lidah Rakyat Indonesia", "Cindy Adams", 1966, SEJARAH, "Biografi Soekarno yang dituturkan langsung kepada penulis.", "Yayasan Bung Karno", 3)
    phys("Catatan Seorang Demonstran", "Soe Hok Gie", 1983, SEJARAH, "Buku harian aktivis mahasiswa tentang idealisme dan politik 1960-an.", "LP3ES", 3)
    phys("Habibie & Ainun", "B. J. Habibie", 2010, SEJARAH, "Kisah cinta dan perjalanan hidup Presiden ketiga RI bersama istrinya.", "THC Mandiri", 3)
    phys("Sejarah Indonesia Modern 1200–2008", "M. C. Ricklefs", 2008, SEJARAH, "Buku rujukan sejarah Indonesia dari masa Islam awal hingga reformasi.", "Serambi", 2)
    phys("Takdir: Riwayat Pangeran Diponegoro 1785–1855", "Peter Carey", 2014, SEJARAH, "Biografi mendalam Pangeran Diponegoro dan Perang Jawa.", "Kompas", 2)

    # ------------------------------------------- Bisnis & Pengembangan Diri (16)
    for row in [
        (368, "Acres of Diamonds", "Russell H. Conwell", 1890, "Ceramah klasik tentang menemukan peluang di tempat Anda berada."),
        (935, "Self-Help", "Samuel Smiles", 1859, "Klasik tentang ketekunan, karakter, dan kemandirian."),
        (6435, "The Principles of Scientific Management", "Frederick W. Taylor", 1911, "Dasar manajemen ilmiah dan efisiensi kerja."),
        (61, "The Communist Manifesto", "Karl Marx & Friedrich Engels", 1848, "Manifesto politik-ekonomi yang membentuk sejarah modern."),
        (833, "The Theory of the Leisure Class", "Thorstein Veblen", 1899, "Analisis konsumsi pamer dan status sosial."),
        (2130, "Utopia", "Thomas More", 1516, "Gambaran masyarakat ideal sebagai kritik atas zamannya."),
    ]:
        g(row[0], row[1], row[2], row[3], BISNIS, row[4])
    for slug, title, author, year, desc in [
        ("principles-management", "Principles of Management", "David S. Bright dkk.", 2019, "Fungsi manajemen: perencanaan, pengorganisasian, kepemimpinan, dan kontrol."),
        ("principles-economics-3e", "Principles of Economics 3e", "Steven Greenlaw dkk.", 2022, "Mikroekonomi dan makroekonomi untuk pemula."),
        ("entrepreneurship", "Entrepreneurship", "Michael Laverty & Chris Littel", 2020, "Memulai dan mengelola usaha dari ide hingga operasi."),
        ("introduction-business", "Introduction to Business", "Lawrence J. Gitman dkk.", 2018, "Pengantar dunia bisnis, pemasaran, keuangan, dan operasi."),
        ("business-ethics", "Business Ethics", "Stephen M. Byars & Kurt Stanberry", 2018, "Etika dalam pengambilan keputusan bisnis."),
        ("organizational-behavior", "Organizational Behavior", "J. Stewart Black & David S. Bright", 2019, "Perilaku individu dan tim dalam organisasi."),
        ("principles-marketing", "Principles of Marketing", "Tim Penulis OpenStax", 2023, "Dasar pemasaran: segmentasi, produk, harga, dan promosi."),
        ("college-success", "College Success", "Amy Baldwin", 2017, "Strategi belajar, manajemen waktu, dan pengembangan diri."),
    ]:
        ob(title, author, year, BISNIS, desc, OS + slug, "OpenStax", "OpenStax — CC BY 4.0")
    phys("Rich Dad Poor Dad (Edisi Indonesia)", "Robert T. Kiyosaki", 1997, BISNIS, "Pelajaran literasi keuangan dari dua sosok ayah dengan cara pandang berbeda.", "Gramedia Pustaka Utama", 3)
    phys("Berani Tidak Disukai", "Ichiro Kishimi & Fumitake Koga", 2013, BISNIS, "Dialog filosofis berbasis psikologi Adler tentang kebebasan dan kebahagiaan.", "Gramedia Pustaka Utama", 3)

    # ------------------------------------------------------- Agama & Filsafat (20)
    for row in [
        (10, "The King James Bible", "Berbagai penulis", 1611, "Terjemahan Alkitab bahasa Inggris klasik (domain publik)."),
        (2800, "The Koran (terjemahan Rodwell)", "J. M. Rodwell (penerjemah)", 1861, "Terjemahan Inggris lama Al-Qur'an, untuk kajian sejarah penerjemahan."),
        (4363, "Beyond Good and Evil", "Friedrich Nietzsche", 1886, "Kritik Nietzsche atas moralitas dan prasangka para filsuf."),
        (1998, "Thus Spake Zarathustra", "Friedrich Nietzsche", 1883, "Karya puitis filosofis tentang Übermensch dan nilai-nilai baru."),
        (4280, "Critique of Pure Reason", "Immanuel Kant", 1781, "Karya pokok Kant tentang batas dan syarat pengetahuan manusia."),
        (3207, "Leviathan", "Thomas Hobbes", 1651, "Teori negara dan kontrak sosial dari Hobbes."),
        (11224, "Utilitarianism", "John Stuart Mill", 1863, "Pembelaan etika yang menilai tindakan dari manfaatnya."),
        (34901, "On Liberty", "John Stuart Mill", 1859, "Pembahasan klasik tentang kebebasan individu dan batas kekuasaan."),
        (59, "Discourse on the Method", "René Descartes", 1637, "Metode berpikir Descartes dan dasar ungkapan 'aku berpikir, maka aku ada'."),
        (1600, "The Symposium", "Plato", -385, "Dialog tentang hakikat cinta dalam sebuah jamuan di Athena."),
        (1658, "Phaedo", "Plato", -360, "Dialog tentang jiwa dan hari-hari terakhir Socrates."),
        (3296, "The Confessions of St. Augustine", "Augustinus", 400, "Otobiografi spiritual salah satu bapa gereja."),
        (1653, "The Imitation of Christ", "Thomas à Kempis", 1418, "Renungan devosional yang sangat luas dibaca."),
        (18269, "Pensées", "Blaise Pascal", 1670, "Catatan pemikiran Pascal tentang iman, akal, dan kondisi manusia."),
        (19942, "Candide", "Voltaire", 1759, "Satire filosofis tentang optimisme dan penderitaan."),
        (2017, "The Dhammapada", "Buddha (terjemahan F. Max Müller)", -300, "Kumpulan syair ajaran Buddha tentang jalan kebijaksanaan."),
        (216, "Tao Te Ching", "Lao Tzu", -400, "Teks dasar Taoisme tentang kesederhanaan dan keselarasan."),
        (3330, "The Analects of Confucius", "Konfusius", -479, "Percakapan Konfusius tentang etika, keluarga, dan pemerintahan."),
        (3800, "Ethics (Spinoza)", "Baruch Spinoza", 1677, "Sistem filsafat Spinoza tentang Tuhan, alam, dan kebebasan manusia."),
    ]:
        g(row[0], row[1], row[2], row[3], AGAMA, row[4])
    phys("Sejarah Tuhan", "Karen Armstrong", 1993, AGAMA, "Penelusuran perkembangan konsep Tuhan dalam Yahudi, Kristen, dan Islam.", "Mizan", 2)

    # ------------------------------------------------ Anak-anak & Komik Edukasi (16)
    for row in [
        (12, "Through the Looking-Glass", "Lewis Carroll", 1871, "Alice melewati cermin dan memasuki dunia catur yang aneh."),
        (289, "The Wind in the Willows", "Kenneth Grahame", 1908, "Persahabatan Tikus Air, Tikus Tanah, Berang-berang, dan Pak Toad."),
        (113, "The Secret Garden", "Frances Hodgson Burnett", 1911, "Mary menemukan taman rahasia yang mengubah hidupnya dan sepupunya."),
        (146, "A Little Princess", "Frances Hodgson Burnett", 1905, "Sara Crewe tetap berjiwa putri meski jatuh miskin di sekolah asrama."),
        (1448, "Heidi", "Johanna Spyri", 1881, "Gadis kecil yang bahagia hidup di pegunungan Alpen bersama kakeknya."),
        (271, "Black Beauty", "Anna Sewell", 1877, "Kisah kuda yang menceritakan hidupnya dan pentingnya kasih sayang pada hewan."),
        (500, "Pinocchio", "Carlo Collodi", 1883, "Boneka kayu yang ingin menjadi anak sungguhan dan belajar jujur."),
        (1874, "The Railway Children", "E. Nesbit", 1906, "Tiga anak pindah ke desa dekat rel kereta dan berpetualang menolong orang."),
        (2781, "Just So Stories", "Rudyard Kipling", 1902, "Dongeng asal-usul binatang, seperti bagaimana gajah mendapat belalai."),
        (503, "The Blue Fairy Book", "Andrew Lang", 1889, "Kumpulan dongeng klasik dunia, termasuk Cinderella dan Beauty and the Beast."),
    ]:
        g(row[0], row[1], row[2], row[3], ANAK, row[4])
    for title, desc in [
        ("Komik Edukasi: Tubuh Manusia", "Komik bergambar tentang organ dan cara kerja tubuh untuk anak."),
        ("Komik Edukasi: Dunia Dinosaurus", "Mengenal jenis dinosaurus dan kehidupan purba lewat komik."),
        ("Komik Edukasi: Cuaca dan Iklim", "Hujan, angin, dan pemanasan global dijelaskan dengan gambar seru."),
        ("Komik Edukasi: Pahlawan Nusantara", "Kisah singkat bergambar para pahlawan nasional."),
        ("Komik Edukasi: Matematika Asyik", "Belajar hitung, pecahan, dan logika lewat petualangan tokoh komik."),
        ("Cerita Rakyat Bergambar: Si Kancil dan Malin Kundang", "Dongeng Nusantara bergambar dengan pesan moral."),
    ]:
        phys(title, "Tim Penulis Komik Sains", 2021, ANAK, desc, "Penerbit Edukomik", 4)

    # ------------------------------------ Tambahan 40 buku (5 per kategori) pengganti Buku Pelajaran
    for row in [  # Agama & Filsafat (5)
        (1657, "Crito", "Plato", -360, AGAMA, "Dialog tentang keadilan dan kesetiaan pada hukum ketika Socrates menolak melarikan diri dari penjara."),
        (621, "The Varieties of Religious Experience", "William James", 1902, AGAMA, "Kajian psikologi tentang pengalaman keagamaan pribadi dari kuliah Gifford."),
        (4705, "A Treatise of Human Nature", "David Hume", 1739, AGAMA, "Hume menelaah pikiran, kausalitas, dan moralitas dengan pendekatan empiris."),
        (46333, "The Social Contract", "Jean-Jacques Rousseau", 1762, AGAMA, "Gagasan kedaulatan rakyat dan kontrak sosial yang membentuk pemikiran politik modern."),
        (10615, "An Essay Concerning Human Understanding, Volume 1", "John Locke", 1689, AGAMA, "Locke menjelaskan asal-usul gagasan dan batas pengetahuan manusia."),
        # Anak-anak & Komik Edukasi (5)
        (54, "The Marvelous Land of Oz", "L. Frank Baum", 1904, ANAK, "Tip melarikan diri bersama Jack Kepala Labu dan bertemu kembali Scarecrow di negeri Oz."),
        (1250, "Pollyanna", "Eleanor H. Porter", 1913, ANAK, "Gadis yatim yang memainkan 'permainan gembira' dan menularkan optimisme ke seluruh kota."),
        (3836, "The Swiss Family Robinson", "Johann David Wyss", 1812, ANAK, "Sebuah keluarga terdampar di pulau tropis dan belajar bertahan hidup bersama."),
        (1937, "The Second Jungle Book", "Rudyard Kipling", 1895, ANAK, "Kelanjutan petualangan Mowgli dan kisah hewan-hewan rimba lainnya."),
        (540, "The Red Fairy Book", "Andrew Lang", 1890, ANAK, "Kumpulan dongeng klasik dari berbagai negeri, lanjutan seri buku dongeng Andrew Lang."),
        # Novel Gratis (5)
        (161, "Sense and Sensibility", "Jane Austen", 1811, NOVEL, "Dua kakak beradik Dashwood menghadapi cinta, uang, dan nama baik keluarga."),
        (105, "Persuasion", "Jane Austen", 1817, NOVEL, "Anne Elliot bertemu kembali dengan pria yang dulu ia tolak karena bujukan keluarga."),
        (18857, "A Journey to the Centre of the Earth", "Jules Verne", 1864, NOVEL, "Profesor Lidenbrock dan keponakannya turun lewat kawah gunung berapi menuju pusat bumi."),
        (159, "The Island of Doctor Moreau", "H. G. Wells", 1896, NOVEL, "Seorang terdampar di pulau tempat dokter gila menciptakan manusia-hewan."),
        (521, "The Life and Adventures of Robinson Crusoe", "Daniel Defoe", 1719, NOVEL, "Seorang pelaut bertahan hidup selama puluhan tahun di pulau terpencil."),
        # Sains & Teknologi (1 Gutenberg + 4 OpenStax)
        (201, "Flatland: A Romance of Many Dimensions", "Edwin A. Abbott", 1884, SAINS, "Fantasi matematika tentang makhluk dua dimensi yang bertemu dunia tiga dimensi."),
        # Sejarah & Biografi (3 Gutenberg + 2 koleksi cetak di bawah)
        (25717, "The History of the Decline and Fall of the Roman Empire, Volume 1", "Edward Gibbon", 1776, SEJARAH, "Karya klasik tentang kemunduran dan keruntuhan Kekaisaran Romawi."),
        (816, "Democracy in America, Volume 2", "Alexis de Tocqueville", 1840, SEJARAH, "Lanjutan pengamatan Tocqueville tentang budaya, agama, dan kehidupan sosial Amerika."),
        (147, "Common Sense", "Thomas Paine", 1776, SEJARAH, "Pamflet yang memengaruhi gerakan kemerdekaan Amerika."),
        # Bisnis & Pengembangan Diri (2 Gutenberg + 3 OpenStax di bawah)
        (205, "Walden", "Henry David Thoreau", 1854, BISNIS, "Catatan hidup sederhana di tepi danau; renungan tentang kemandirian dan kerja yang bermakna."),
        (2944, "Essays: First Series (Self-Reliance)", "Ralph Waldo Emerson", 1841, BISNIS, "Kumpulan esai Emerson, termasuk 'Self-Reliance' tentang kepercayaan pada diri sendiri."),
    ]:
        g(*row[:4], row[4], row[5])
    for slug, title, author, year, cat, desc in [
        ("calculus-volume-2", "Calculus Volume 2", "Gilbert Strang & Edwin Herman", 2016, SAINS, "Teknik integral, deret, dan persamaan diferensial dasar."),
        ("physics", "Physics (OpenStax)", "Paul Peter Urone & Roger Hinrichs", 2020, SAINS, "Fisika tingkat menengah: gerak, energi, gelombang, dan listrik."),
        ("precalculus-2e", "Precalculus 2e", "Jay Abramson dkk.", 2021, SAINS, "Fungsi, trigonometri, dan topik persiapan kalkulus."),
        ("college-algebra-2e", "College Algebra 2e", "Jay Abramson dkk.", 2021, SAINS, "Persamaan, fungsi, polinomial, dan sistem persamaan."),
        ("introductory-business-statistics", "Introductory Business Statistics", "Alexander Holmes dkk.", 2018, BISNIS, "Statistika untuk keputusan bisnis: data, probabilitas, dan inferensi."),
        ("business-law-i-essentials", "Business Law I Essentials", "Tim Penulis OpenStax", 2019, BISNIS, "Dasar hukum bisnis: kontrak, badan usaha, dan tanggung jawab hukum."),
        ("principles-finance", "Principles of Finance", "Tim Penulis OpenStax", 2022, BISNIS, "Nilai waktu uang, risiko, penganggaran modal, dan investasi."),
    ]:
        ob(title, author, year, cat, desc, OS + slug, "OpenStax", "OpenStax — CC BY 4.0")
    for title, author, year, desc, url, pub, lic in [  # Pemrograman & Komputer (5)
        ("Think Bayes (2nd Edition)", "Allen B. Downey", 2021, "Statistika Bayesian dengan kode Python.", "https://allendowney.github.io/ThinkBayes2/", "Green Tea Press", "Creative Commons BY-NC-SA"),
        ("Think OS: A Brief Introduction to Operating Systems", "Allen B. Downey", 2015, "Pengantar sistem operasi untuk programmer.", "https://greenteapress.com/wp/think-os/", "Green Tea Press", "Creative Commons BY-NC-SA"),
        ("A Tour of Go", "Tim Go", 2012, "Tur interaktif resmi untuk belajar bahasa Go.", "https://go.dev/tour/", "Go Project", "BSD-3-Clause"),
        ("The TypeScript Handbook", "Microsoft", 2020, "Panduan resmi TypeScript dari dasar hingga tipe lanjutan.", "https://www.typescriptlang.org/docs/handbook/intro.html", "Microsoft", "Apache-2.0"),
        ("Flask Documentation (Dokumentasi Resmi)", "Pallets Projects", 2023, "Dokumentasi resmi framework Flask: tutorial, panduan, dan referensi API.", "https://flask.palletsprojects.com/", "Pallets Projects", "BSD-3-Clause"),
    ]:
        ob(title, author, year, PROG, desc, url, pub, lic)
    for row in [  # Sastra Indonesia Klasik (5)
        ("Hikayat Indera Putera", "Anonim", 1600, "Hikayat Melayu tentang pengembaraan Pangeran Indera Putera dan peperangan dengan raksasa."),
        ("Hikayat Bakhtiar", "Anonim", 1600, "Hikayat bingkai dengan banyak cerita yang dituturkan untuk menyelamatkan nyawa sang pangeran."),
        ("Carita Parahyangan", "Anonim", 1580, "Naskah Sunda kuno tentang sejarah kerajaan Sunda dan Galuh."),
        ("Kakawin Bharatayuddha", "Mpu Sedah & Mpu Panuluh", 1157, "Kakawin Jawa Kuno tentang perang Pandawa dan Korawa di Kurukshetra."),
        ("Serat Wulangreh", "Pakubuwana IV", 1790, "Tembang ajaran budi pekerti bagi bangsawan dan abdi dalem Jawa."),
    ]:
        ws(*row)
    phys("Max Havelaar", "Multatuli", 1860, SEJARAH, "Novel yang mengkritik sistem tanam paksa di Hindia Belanda.", "Qanita", 2)
    phys("Habis Gelap Terbitlah Terang", "R. A. Kartini", 1911, SEJARAH, "Kumpulan surat Kartini tentang pendidikan dan emansipasi perempuan.", "Balai Pustaka", 3)
    return B
