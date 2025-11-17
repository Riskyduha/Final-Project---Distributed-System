# Simulasi Aplikasi Chat Real-Time dengan Arsitektur Event-Driven

## Tujuan Percobaan

Percobaan ini bertujuan untuk memahami dan mengimplementasikan konsep-konsep fundamental dalam sistem terdistribusi, khususnya:

1. **Arsitektur Event-Driven (Berbasis Kejadian)**
   - Memahami bagaimana sistem dapat bereaksi secara asinkron terhadap kejadian (event) yang terjadi
   - Mengimplementasikan komunikasi real-time antara komponen sistem yang berbeda
   - Mempelajari pola desain yang memisahkan producer (pengirim event) dan consumer (penerima event)

2. **Paradigma Komunikasi Publish-Subscribe**
   - Memahami model komunikasi di mana pengirim (publisher) tidak perlu tahu siapa penerimanya (subscriber)
   - Mengimplementasikan mekanisme topic-based messaging untuk decoupling antar komponen
   - Membandingkan efektivitas pub-sub dengan komunikasi point-to-point langsung

3. **Multi-threading untuk Konkruensi**
   - Mengelola banyak koneksi pengguna secara bersamaan menggunakan thread
   - Memahami bagaimana thread dapat meningkatkan responsiveness sistem
   - Mengimplementasikan sinkronisasi data menggunakan lock untuk menghindari race condition

4. **Analisis Performa Metode Pengiriman Pesan**
   - Membandingkan karakteristik dua metode pengiriman: Direct (langsung) vs PubSub (publish-subscribe)
   - Mengukur metrik penting: latency (waktu tunda), throughput (jumlah pesan per detik), dan packet loss
   - Memahami trade-off antara kecepatan, reliabilitas, dan kompleksitas implementasi

## Deskripsi Sistem

Aplikasi ini adalah simulasi chat real-time berbasis web yang menggunakan Flask dan Flask-SocketIO. Sistem ini mensimulasikan komunikasi antara dua node (A dan B) dengan karakteristik jaringan yang dapat dikonfigurasi.

### Komponen Utama

**Backend (app.py)**
- Server Flask dengan Socket.IO untuk komunikasi real-time bi-directional
- Thread pool untuk menangani pengiriman pesan secara konkuren
- Sistem metrik untuk mengumpulkan data performa (latency, delivery rate, packet loss)
- Background thread untuk broadcast metrik ke semua client setiap 500ms

**Frontend (templates/index.html & static/js/app.js)**
- Interface web single-page untuk monitoring dan kontrol
- Panel terpisah untuk setiap node (A dan B)
- Real-time charts menggunakan Chart.js untuk visualisasi metrik
- Form konfigurasi untuk menyesuaikan parameter simulasi

### Dua Metode Pengiriman Pesan

#### 1. Metode Direct (Pengiriman Langsung)
**Cara Kerja:**
- Pengirim mengirim pesan langsung ke penerima tertentu
- Simulasi best-effort delivery (tidak ada jaminan sampai)
- Packet loss dan latency disimulasikan secara random

**Karakteristik:**
- ✅ Lebih cepat karena tidak ada overhead acknowledgment
- ✅ Implementasi lebih sederhana
- ❌ Tidak reliable - pesan bisa hilang tanpa notifikasi
- ❌ Tidak ada mekanisme retry otomatis

**Cocok untuk:** Aplikasi yang memprioritaskan kecepatan dan bisa mentolerir kehilangan data (misal: live streaming, gaming)

#### 2. Metode PubSub (Publish-Subscribe dengan ACK)
**Cara Kerja:**
- Pengirim publish pesan ke topic (tidak tahu siapa subscribernya)
- Semua subscriber yang terdaftar akan menerima pesan
- Setiap subscriber harus mengirim acknowledgment (ACK)
- Jika ACK tidak diterima dalam timeout, pesan akan dikirim ulang (retry)
- Maximum retry attempts dapat dikonfigurasi

**Karakteristik:**
- ✅ Reliable - ada mekanisme retry untuk memastikan pesan sampai
- ✅ Scalable - mudah menambah subscriber tanpa mengubah publisher
- ✅ Decoupled - publisher tidak perlu tahu detail subscriber
- ❌ Lebih lambat karena overhead ACK dan retry
- ❌ Implementasi lebih kompleks

**Cocok untuk:** Aplikasi yang membutuhkan reliability tinggi (misal: chat, notifikasi penting, transaksi)

### Parameter Simulasi yang Dapat Dikonfigurasi

1. **Loss Rate (%)** - Persentase paket yang hilang (0-100)
   - Mensimulasikan kondisi jaringan yang tidak stabil
   - Semakin tinggi, semakin banyak pesan yang gagal terkirim

2. **Latency Min/Max (ms)** - Range waktu tunda jaringan
   - Mensimulasikan jarak geografis atau kualitas koneksi
   - Latency actual akan random dalam range ini

3. **Max Retries** - Jumlah percobaan ulang untuk PubSub
   - Menentukan berapa kali sistem mencoba mengirim ulang jika gagal
   - Trade-off antara reliability vs resource usage

4. **ACK Timeout (ms)** - Waktu tunggu acknowledgment
   - Berapa lama menunggu konfirmasi sebelum retry
   - Timeout terlalu pendek = banyak retry unnecessary
   - Timeout terlalu panjang = sistem lambat bereaksi terhadap kegagalan

## Cara Menjalankan (Windows PowerShell)

### 1. Buat Virtual Environment (Opsional tapi Direkomendasikan)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 2. Install Dependencies

```powershell
pip install -r requirements.txt
```

### 3. Jalankan Server

```powershell
python app.py
```

Server akan berjalan di `http://localhost:5000`

### 4. Buka Browser dan Mulai Percobaan

1. Buka dua tab/window browser
2. Di tab pertama: pilih Node A lalu klik "Register"
3. Di tab kedua: pilih Node B lalu klik "Register"
4. Pilih metode pengiriman (Direct atau PubSub)
5. Ketik pesan dan klik tombol "Send"
6. Amati hasil di panel log, metrik, dan chart

## Panduan Eksperimen

### Eksperimen 1: Membandingkan Direct vs PubSub dalam Kondisi Normal
1. Set Loss Rate = 10%, Latency 50-250ms
2. Kirim 10 pesan menggunakan metode Direct
3. Kirim 10 pesan menggunakan metode PubSub
4. Bandingkan metrik: delivery rate, average latency, lost messages
5. **Hasil yang diharapkan:** PubSub lebih reliable tapi latency lebih tinggi

### Eksperimen 2: Pengujian dengan Loss Rate Tinggi
1. Set Loss Rate = 50% (kondisi jaringan buruk)
2. Kirim pesan dengan kedua metode
3. Amati berapa pesan yang berhasil terkirim
4. **Hasil yang diharapkan:** PubSub dengan retry akan tetap deliver sebagian besar pesan, Direct akan kehilangan banyak pesan

### Eksperimen 3: Pengaruh Latency terhadap Throughput
1. Eksperimen A: Set Latency 10-50ms (jaringan cepat)
2. Eksperimen B: Set Latency 200-500ms (jaringan lambat)
3. Kirim banyak pesan cepat (spam)
4. Bandingkan throughput chart kedua eksperimen
5. **Hasil yang diharapkan:** Latency tinggi menurunkan throughput keseluruhan

### Eksperimen 4: Optimasi Parameter PubSub
1. Coba berbagai kombinasi Max Retries (0, 1, 2, 5) dan ACK Timeout (300ms, 600ms, 1000ms)
2. Amati trade-off antara reliability dan latency
3. **Hasil yang diharapkan:** Retry tinggi + timeout panjang = reliable tapi lambat

## Struktur File

```
├── app.py                    # Backend server (Flask + SocketIO)
│   ├── Route handler
│   ├── Socket event handlers (register, send_message, update_config)
│   ├── Direct delivery function dengan threading
│   ├── PubSub delivery dengan ACK mechanism
│   └── Background metrics broadcaster
│
├── templates/
│   └── index.html           # Frontend HTML dengan layout dan form
│
├── static/
│   └── js/
│       └── app.js           # Client-side logic (Socket.IO + Chart.js)
│
├── requirements.txt         # Python dependencies
└── README.md               # Dokumentasi ini
```

## Fitur Teknis

### 1. Event-Driven Architecture
- Menggunakan Socket.IO untuk real-time communication
- Event-based message passing antara client dan server
- Asynchronous processing menggunakan callbacks

### 2. Multi-threading Implementation
- Setiap pengiriman pesan dijalankan di thread terpisah
- Lock mechanism untuk thread-safe access ke shared data (metrics, config)
- Background thread untuk periodic metrics broadcasting

### 3. Real-time Monitoring
- Chart latency menampilkan perbandingan response time
- Chart throughput menampilkan rate pengiriman pesan
- Update otomatis setiap 500ms
- Rolling window 20 data points

### 4. Dynamic Configuration
- Parameter dapat diubah tanpa restart server
- Perubahan di-broadcast ke semua connected clients
- Validasi input untuk mencegah nilai invalid

## Catatan Penting

- ⚠️ Ini adalah **simulasi** untuk tujuan pembelajaran - latency dan packet loss dibuat secara artificial
- ✅ Implementasi multi-threading menggunakan `threading.Thread` sesuai requirement tugas
- ✅ Tidak memerlukan XAMPP atau web server eksternal - murni Python Flask
- 🔒 Thread-safe data access menggunakan `threading.Lock()`
- 📊 Metrics dikumpulkan di memory (tidak persisten) untuk kesederhanaan

## Kesimpulan dan Pembelajaran

Dari percobaan ini, mahasiswa diharapkan dapat:
1. Memahami perbedaan fundamental antara komunikasi langsung vs publish-subscribe
2. Mengerti trade-off antara performa (speed) dan reliabilitas dalam sistem terdistribusi
3. Mengimplementasikan multi-threading untuk menangani konkurensi
4. Menganalisis metrik sistem untuk mengevaluasi kualitas komunikasi
5. Membuat keputusan arsitektural berdasarkan requirement aplikasi (kapan pakai Direct, kapan pakai PubSub)
