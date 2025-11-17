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

## Algoritma dan Implementasi Detail

### Algoritma 1: Direct Delivery (Pengiriman Langsung)

**Pseudocode:**
```
FUNCTION direct_delivery(msg_id, sender, target, content, timestamp):
    // Baca konfigurasi dengan thread-safe
    LOCK.acquire()
    latency_min = config['latency_min'] / 1000
    latency_max = config['latency_max'] / 1000
    loss_rate = config['loss_rate']
    LOCK.release()
    
    // Hitung delay random dalam range yang ditentukan
    random_factor = random(0, 100) / 100
    delay = latency_min + (latency_max - latency_min) * random_factor
    
    // Simulasi network latency
    SLEEP(delay)
    
    // Simulasi packet loss berdasarkan probabilitas
    random_loss = random(0, 100)
    IF random_loss < loss_rate THEN:
        // Pesan hilang
        LOCK.acquire()
        metrics['Direct']['lost'] += 1
        LOCK.release()
        
        EMIT('delivery_failed', {msg_id, method: 'Direct'})
        RETURN
    END IF
    
    // Pesan berhasil dikirim
    current_time = current_timestamp()
    payload = {
        msg_id: msg_id,
        from: sender,
        to: target,
        content: content,
        method: 'Direct',
        timestamp: current_time
    }
    
    EMIT('message', payload)
    
    // Update metrics
    LOCK.acquire()
    metrics['Direct']['delivered'] += 1
    metrics['Direct']['latencies'].append(current_time - timestamp)
    LOCK.release()
END FUNCTION
```

**Penjelasan Algoritma:**
1. **Thread Safety**: Menggunakan lock untuk membaca konfigurasi yang bisa berubah secara dinamis
2. **Random Latency**: Mensimulasikan variasi waktu pengiriman dalam rentang min-max
3. **Probabilistic Loss**: Menggunakan random number untuk mensimulasikan packet loss
4. **Metrics Collection**: Mencatat setiap kejadian (sent, delivered, lost) dengan aman menggunakan lock
5. **No Retry**: Sekali gagal, pesan langsung hilang tanpa percobaan ulang

**Kompleksitas:**
- **Time Complexity**: O(1) per pesan
- **Space Complexity**: O(n) untuk menyimpan metrics, dimana n adalah jumlah pesan

---

### Algoritma 2: PubSub Delivery dengan ACK dan Retry

**Pseudocode:**
```
FUNCTION pubsub_publish(msg_id, sender, content, timestamp):
    // Baca konfigurasi
    LOCK.acquire()
    max_retries = config['max_retries']
    ack_timeout = config['ack_timeout'] / 1000
    targets = list(subscribers)  // Semua subscriber yang terdaftar
    LOCK.release()
    
    // Buat thread untuk setiap target subscriber
    threads = []
    FOR EACH target IN targets:
        thread = CREATE_THREAD(
            pubsub_deliver_to_target,
            args: (msg_id, sender, target, content, timestamp, max_retries, ack_timeout)
        )
        thread.start()
        threads.append(thread)
    END FOR
    
    // Tunggu semua thread selesai
    FOR EACH thread IN threads:
        thread.join()
    END FOR
END FUNCTION

FUNCTION pubsub_deliver_to_target(msg_id, sender, target, content, timestamp, max_retries, ack_timeout):
    attempt = 0
    delivered = FALSE
    
    // Loop retry hingga sukses atau mencapai max attempts
    WHILE attempt <= max_retries AND NOT delivered:
        attempt += 1
        
        // Baca konfigurasi latency
        LOCK.acquire()
        latency_min = config['latency_min'] / 1000
        latency_max = config['latency_max'] / 1000
        LOCK.release()
        
        // Simulasi network latency
        random_factor = random(0, 100) / 100
        delay = latency_min + (latency_max - latency_min) * random_factor
        SLEEP(delay)
        
        // Kirim pesan ke subscriber
        payload = {
            msg_id: msg_id,
            from: sender,
            to: target,
            content: content,
            method: 'PubSub',
            attempt: attempt,
            timestamp: current_timestamp()
        }
        EMIT('pubsub_message', payload)
        
        // Tunggu ACK dengan timeout
        ack_received = FALSE
        start_time = current_timestamp()
        
        WHILE (current_timestamp() - start_time) < ack_timeout:
            LOCK.acquire()
            IF ack_store[(msg_id, target)] EXISTS THEN:
                ack_received = TRUE
                delivered = TRUE
                LOCK.release()
                BREAK
            END IF
            LOCK.release()
            
            SLEEP(0.05)  // Check setiap 50ms
        END WHILE
        
        IF delivered THEN:
            // Update metrics sukses
            LOCK.acquire()
            metrics['PubSub']['delivered'] += 1
            metrics['PubSub']['latencies'].append(current_timestamp() - timestamp)
            LOCK.release()
            BREAK
        END IF
    END WHILE
    
    // Jika tidak delivered setelah semua retry
    IF NOT delivered THEN:
        LOCK.acquire()
        metrics['PubSub']['lost'] += 1
        LOCK.release()
    END IF
END FUNCTION

// Handler untuk menerima ACK dari client
FUNCTION handle_pubsub_ack(msg_id, node):
    LOCK.acquire()
    ack_store[(msg_id, node)] = TRUE
    LOCK.release()
END FUNCTION
```

**Penjelasan Algoritma:**
1. **Topic-based Broadcasting**: Publish ke semua subscriber tanpa tahu detail mereka
2. **Concurrent Delivery**: Setiap subscriber dilayani oleh thread terpisah untuk paralelisme
3. **ACK Mechanism**: Menunggu konfirmasi dari subscriber dengan timeout
4. **Exponential Backoff (implicit)**: Setiap retry menambah total latency
5. **Retry Logic**: Mencoba ulang hingga max_retries atau sampai sukses
6. **ACK Store**: Menggunakan dictionary dengan key (msg_id, target) untuk tracking ACK

**Kompleksitas:**
- **Time Complexity**: O(s × r) dimana s = jumlah subscriber, r = max_retries
- **Space Complexity**: O(n + a) dimana n = metrics, a = ack_store size

---

### Algoritma 3: Metrics Broadcasting

**Pseudocode:**
```
FUNCTION metrics_broadcaster():
    WHILE TRUE:
        SLEEP(0.5)  // Broadcast setiap 500ms
        
        snapshot = {}
        
        LOCK.acquire()
        FOR EACH method IN ['Direct', 'PubSub']:
            data = metrics[method]
            
            // Hitung rata-rata latency
            IF data['latencies'] is NOT empty THEN:
                avg_latency = SUM(data['latencies']) / COUNT(data['latencies'])
            ELSE:
                avg_latency = 0
            END IF
            
            snapshot[method] = {
                'sent': data['sent'],
                'delivered': data['delivered'],
                'lost': data['lost'],
                'avg_latency': ROUND(avg_latency, 3)
            }
        END FOR
        LOCK.release()
        
        // Broadcast ke semua connected clients
        EMIT_BROADCAST('metrics_update', snapshot)
    END WHILE
END FUNCTION
```

**Penjelasan:**
- Berjalan sebagai daemon thread di background
- Mengambil snapshot metrics dengan thread-safe locking
- Menghitung statistik aggregate (average latency)
- Broadcast ke semua client untuk sinkronisasi UI

---

### Algoritma 4: Dynamic Configuration Update

**Pseudocode:**
```
FUNCTION handle_update_config(new_config):
    LOCK.acquire()
    
    // Validasi dan update setiap parameter
    IF 'loss_rate' IN new_config THEN:
        config['loss_rate'] = CLAMP(new_config['loss_rate'], 0, 100)
    END IF
    
    IF 'latency_min' IN new_config THEN:
        config['latency_min'] = MAX(0, new_config['latency_min'])
    END IF
    
    IF 'latency_max' IN new_config THEN:
        config['latency_max'] = MAX(config['latency_min'], new_config['latency_max'])
    END IF
    
    IF 'max_retries' IN new_config THEN:
        config['max_retries'] = MAX(0, new_config['max_retries'])
    END IF
    
    IF 'ack_timeout' IN new_config THEN:
        config['ack_timeout'] = MAX(100, new_config['ack_timeout'])
    END IF
    
    updated_config = COPY(config)
    LOCK.release()
    
    // Broadcast config baru ke semua clients
    EMIT_BROADCAST('config_updated', updated_config)
END FUNCTION
```

**Penjelasan:**
- Validasi input untuk mencegah nilai invalid (misal: latency negatif)
- Constraint checking (misal: latency_max >= latency_min)
- Atomic update menggunakan lock
- Broadcast untuk sinkronisasi UI di semua client

---

## Fitur Teknis

### 1. Event-Driven Architecture
**Implementasi Detail:**
- **WebSocket Connection**: Menggunakan Socket.IO yang built on top of WebSocket dengan fallback ke HTTP long-polling
- **Event Handlers**: 
  - `connect`: Inisialisasi koneksi client
  - `register`: Mendaftarkan node dan join ke room spesifik
  - `send_message`: Trigger pengiriman pesan dengan method yang dipilih
  - `update_config`: Update parameter simulasi secara dinamis
  - `pubsub_ack`: Menerima acknowledgment dari subscriber
  - `disconnect`: Cleanup saat client disconnect
- **Event Emitters**:
  - `message`: Broadcast pesan yang berhasil dikirim (Direct)
  - `pubsub_message`: Broadcast pesan PubSub ke subscriber
  - `metrics_update`: Periodic broadcast metrics ke semua client
  - `config_updated`: Broadcast perubahan konfigurasi
- **Asynchronous Processing**: Callback-based handling untuk non-blocking operations

### 2. Multi-threading Implementation
**Arsitektur Threading:**
```
Main Thread (Flask Server)
├── Socket.IO Event Loop
│   ├── Handle incoming events
│   └── Dispatch to handlers
│
├── Background Daemon Thread
│   └── Metrics Broadcaster (infinite loop, 500ms interval)
│
└── Dynamic Worker Threads (created on-demand)
    ├── Direct Delivery Thread (per message)
    └── PubSub Delivery Threads (per subscriber per message)
```

**Thread Safety Mechanisms:**
- **Lock Object**: `threading.Lock()` untuk mutual exclusion
- **Critical Sections**:
  - Reading/Writing `config` dictionary
  - Reading/Writing `metrics` dictionary
  - Reading/Writing `ack_store` dictionary
  - Accessing `clients` and `subscribers` sets
- **Atomic Operations**: Update counter menggunakan `+=` dalam lock context

**Keuntungan Multi-threading:**
1. **Non-blocking**: Pengiriman pesan tidak block main event loop
2. **Concurrent Processing**: Multiple pesan dapat diproses bersamaan
3. **Responsive UI**: Server tetap bisa handle request lain saat deliver pesan
4. **Scalability**: Dapat handle banyak client simultan

### 3. Real-time Monitoring
**Data Flow:**
```
Server (Python)                    Client (JavaScript)
─────────────────                  ────────────────────
Metrics Collection  ──500ms──>    Socket Event Listener
      │                                   │
      ├─> sent count                      ├─> Update metrics text
      ├─> delivered count                 ├─> Append to chart data
      ├─> lost count                      │   (rolling window: 20 points)
      └─> latencies[]                     └─> Chart.update()
                                               │
                                               ├─> Latency Line Chart
                                               └─> Throughput Line Chart
```

**Chart Implementation:**
- **Library**: Chart.js v4.4.0
- **Type**: Line chart dengan tension 0.1 (slight curve)
- **Update Mode**: 'none' untuk performa (no animation)
- **Data Structure**:
  ```javascript
  latencyData = {
    Direct: [0.05, 0.12, 0.08, ...],  // max 20 points
    PubSub: [0.15, 0.18, 0.22, ...]   // max 20 points
  }
  throughputData = {
    Direct: [5.2, 8.1, 12.3, ...],
    PubSub: [4.1, 6.8, 9.2, ...]
  }
  timeLabels = ['10:15:30', '10:15:31', ...]
  ```

### 4. Dynamic Configuration
**Configuration State Management:**
```python
config = {
    'loss_rate': 10,      # percentage (0-100)
    'latency_min': 50,    # milliseconds
    'latency_max': 250,   # milliseconds
    'max_retries': 2,     # count
    'ack_timeout': 600    # milliseconds
}
```

**Update Flow:**
```
User Input (UI) → Socket Event → Validation → Lock → Update → Broadcast
                                      ↓
                              Clamp to valid range
                              Check constraints
                              
Example Validations:
- loss_rate: 0 ≤ x ≤ 100
- latency_min: x ≥ 0
- latency_max: x ≥ latency_min
- max_retries: x ≥ 0
- ack_timeout: x ≥ 100ms
```

### 5. Room-based Messaging (Socket.IO)
**Room Structure:**
- `node-A`: Room untuk client yang register sebagai Node A
- `node-B`: Room untuk client yang register sebagai Node B
- Global: Semua client (untuk broadcast metrics dan config)

**Use Case:**
- Targeted message delivery ke node tertentu
- Efficient broadcasting tanpa perlu iterate semua clients
- Automatic cleanup saat client disconnect

## Catatan Penting

- ⚠️ Ini adalah **simulasi** untuk tujuan pembelajaran - latency dan packet loss dibuat secara artificial
- ✅ Implementasi multi-threading menggunakan `threading.Thread` sesuai requirement tugas
- ✅ Tidak memerlukan XAMPP atau web server eksternal - murni Python Flask
- 🔒 Thread-safe data access menggunakan `threading.Lock()`
- 📊 Metrics dikumpulkan di memory (tidak persisten) untuk kesederhanaan

## Diagram Arsitektur Sistem

```
┌─────────────────────────────────────────────────────────────────┐
│                         Client Browser                          │
│  ┌────────────┐  ┌────────────┐  ┌──────────────────────────┐ │
│  │  Node A UI │  │  Node B UI │  │  Config & Metrics Panel  │ │
│  └─────┬──────┘  └─────┬──────┘  └────────────┬─────────────┘ │
│        │                │                      │                │
│        └────────────────┴──────────────────────┘                │
│                         │                                       │
│                    Socket.IO Client                             │
└─────────────────────────┼───────────────────────────────────────┘
                          │ WebSocket/HTTP
                          │
┌─────────────────────────┼───────────────────────────────────────┐
│                    Socket.IO Server                             │
│                         │                                       │
│  ┌──────────────────────┴────────────────────────┐             │
│  │          Event Handler & Router               │             │
│  │  • register()  • send_message()               │             │
│  │  • disconnect()  • update_config()            │             │
│  └──────┬─────────────────────┬──────────────────┘             │
│         │                     │                                │
│    ┌────▼─────┐         ┌────▼──────┐                         │
│    │  Direct  │         │  PubSub   │                         │
│    │ Delivery │         │ Delivery  │                         │
│    └────┬─────┘         └────┬──────┘                         │
│         │                     │                                │
│    ┌────▼─────────────────────▼──────┐                        │
│    │    Thread Pool Manager          │                        │
│    │  ┌──────┐ ┌──────┐ ┌──────┐    │                        │
│    │  │Thread│ │Thread│ │Thread│... │                        │
│    │  └──────┘ └──────┘ └──────┘    │                        │
│    └─────────────┬───────────────────┘                        │
│                  │                                             │
│    ┌─────────────▼──────────────────┐                         │
│    │   Shared Data (with Lock)      │                         │
│    │  • config{}  • metrics{}        │                         │
│    │  • clients{} • ack_store{}      │                         │
│    └────────────────────────────────┘                         │
│                  │                                             │
│    ┌─────────────▼──────────────────┐                         │
│    │  Background Daemon Thread      │                         │
│    │  (Metrics Broadcaster)         │                         │
│    │  Loop every 500ms              │                         │
│    └────────────────────────────────┘                         │
└─────────────────────────────────────────────────────────────────┘
```

## Flow Diagram: Direct Delivery

```
┌──────┐                 ┌──────┐                 ┌──────┐
│NodeA │                 │Server│                 │NodeB │
└───┬──┘                 └───┬──┘                 └───┬──┘
    │                        │                        │
    │ send_message(Direct)   │                        │
    ├───────────────────────>│                        │
    │                        │                        │
    │     sent_ack           │                        │
    │<───────────────────────┤                        │
    │                        │                        │
    │                   [New Thread]                  │
    │                        │                        │
    │                    Calculate                    │
    │                   Random Delay                  │
    │                        │                        │
    │                    SLEEP(delay)                 │
    │                        │                        │
    │                   Check Loss?                   │
    │                   ┌────┴────┐                   │
    │                   │         │                   │
    │               [Lost]    [Success]               │
    │                   │         │                   │
    │  delivery_failed  │         │    message        │
    │<──────────────────┤         ├──────────────────>│
    │                   │         │                   │
    │              Update         │              Update│
    │              Metrics        │              UI   │
    │              (lost++)       │                   │
    │                             │              Send │
    │                             │           no ACK  │
    │                        Update                   │
    │                       Metrics                   │
    │                     (delivered++)               │
    │                                                  │
```

## Flow Diagram: PubSub Delivery with Retry

```
┌──────┐                 ┌──────┐                 ┌──────┐
│NodeA │                 │Server│                 │NodeB │
└───┬──┘                 └───┬──┘                 └───┬──┘
    │                        │                        │
    │ send_message(PubSub)   │                        │
    ├───────────────────────>│                        │
    │                        │                        │
    │     sent_ack           │                        │
    │<───────────────────────┤                        │
    │                        │                        │
    │              [New Thread per Subscriber]        │
    │                        │                        │
    │                   ATTEMPT 1                     │
    │                        │                        │
    │                    SLEEP(delay)                 │
    │                        │                        │
    │                        │  pubsub_message        │
    │                        ├───────────────────────>│
    │                        │                        │
    │                        │                   Display
    │                        │                   Message
    │                        │                        │
    │                        │    pubsub_ack          │
    │                        │<───────────────────────┤
    │                        │                        │
    │                   ACK Received                  │
    │                   Within Timeout?               │
    │                   ┌────┴────┐                   │
    │                   │         │                   │
    │                [YES]      [NO]                  │
    │                   │         │                   │
    │              SUCCESS    ATTEMPT 2               │
    │              Update         │                   │
    │             Metrics         │                   │
    │          (delivered++)  SLEEP(delay)            │
    │              EXIT           │                   │
    │                             │  pubsub_message   │
    │                             ├──────────────────>│
    │                             │                   │
    │                        Wait for ACK             │
    │                        with timeout...          │
    │                             │                   │
    │                    [Retry until max_retries     │
    │                     or success]                 │
    │                             │                   │
    │                    If all retries fail:         │
    │                        Update                   │
    │                       Metrics                   │
    │                       (lost++)                  │
    │                                                  │
```

## Perbandingan Kompleksitas Algoritma

| Aspek | Direct Delivery | PubSub with ACK |
|-------|----------------|-----------------|
| **Time Complexity (best case)** | O(1) | O(s) dimana s = subscribers |
| **Time Complexity (worst case)** | O(1) | O(s × r) dimana r = max_retries |
| **Space Complexity** | O(n) | O(n + a) dimana a = ACK store |
| **Network Roundtrips** | 1 (one-way) | 2 × r (message + ACK, dengan retry) |
| **Latency (avg)** | base_latency | base_latency + ack_timeout × retry_rate |
| **Reliability** | (100 - loss_rate)% | Mendekati 100% dengan retry |
| **Throughput** | Tinggi | Rendah (overhead ACK) |
| **Scalability** | O(1) per message | O(s) per message |

## State Diagram: Message Lifecycle

### Direct Method:
```
    [QUEUED]
       │
       ▼
   [SENDING] ──────> [SIMULATING NETWORK]
       │                     │
       │                     ├──> [LOST] ──> metrics.lost++
       │                     │
       │                     └──> [DELIVERED] ──> metrics.delivered++
       │
    [END]
```

### PubSub Method:
```
    [QUEUED]
       │
       ▼
  [PUBLISHING]
       │
       ├──> For each subscriber:
       │         │
       │         ▼
       │    [ATTEMPT 1] ──> [SENDING] ──> [WAIT_ACK]
       │         │                            │
       │         │                            ├──> [ACK_RECEIVED]
       │         │                            │         │
       │         │                            │         ▼
       │         │                            │    [DELIVERED]
       │         │                            │    metrics.delivered++
       │         │                            │
       │         │                            └──> [TIMEOUT]
       │         │                                      │
       │         ▼                                      ▼
       │    [ATTEMPT 2] ──────────────────────> [WAIT_ACK]
       │         │                                      │
       │         .                                      .
       │         .                                      .
       │         ▼                                      │
       │    [ATTEMPT max_retries] ─────────────> [WAIT_ACK]
       │         │                                      │
       │         │                                      │
       │         └─> [ALL FAILED] ─────────────> [LOST]
       │                                         metrics.lost++
       │
    [END]
```

## Analisis Performa Teoritis

### 1. Latency Analysis

**Direct Method:**
```
Total_Latency = Random(latency_min, latency_max)
Average_Latency = (latency_min + latency_max) / 2
```

**PubSub Method (dengan retry):**
```
Best_Case = Random(latency_min, latency_max) + ACK_processing_time
Worst_Case = Σ(i=1 to max_retries) [Random(latency_min, latency_max) + ack_timeout]
Average_Case = Best_Case × (1 - retry_probability) + 
               (Best_Case + retry_latency) × retry_probability
```

### 2. Success Rate Analysis

**Direct Method:**
```
Success_Rate = (100 - loss_rate) %
Expected_Delivered = Total_Messages × (100 - loss_rate) / 100
```

**PubSub Method:**
```
Success_Rate_Per_Attempt = (100 - loss_rate) %
Overall_Success_Rate = 1 - (loss_rate/100)^(max_retries + 1)

Contoh dengan loss_rate=30%, max_retries=2:
- Attempt 1 fails: 30%
- Attempt 2 fails: 30% × 30% = 9%
- Attempt 3 fails: 30% × 30% × 30% = 2.7%
- Success Rate: 100% - 2.7% = 97.3%
```

### 3. Throughput Analysis

**Direct Method:**
```
Throughput = Messages_Sent / (Average_Latency × Concurrency_Factor)
Karena non-blocking: Concurrency_Factor ≈ jumlah thread
```

**PubSub Method:**
```
Throughput = Messages_Sent / (Average_Total_Latency × Subscribers)
Lebih rendah karena:
- ACK overhead
- Retry delays
- Multiple roundtrips
```

## Skenario Edge Cases dan Handling

### 1. Concurrent Config Update saat Delivery
**Problem:** Thread sedang deliver message, user update config
**Solution:** Lock mechanism memastikan config read atomic
```python
# Setiap thread baca config dengan lock
LOCK.acquire()
current_config = copy(config)
LOCK.release()
# Gunakan current_config untuk delivery
```

### 2. Client Disconnect saat Waiting ACK
**Problem:** Subscriber disconnect sebelum kirim ACK
**Solution:** 
- Timeout mechanism akan trigger retry
- Setelah max_retries, mark as lost
- Automatic cleanup di disconnect handler

### 3. Race Condition di Metrics Update
**Problem:** Multiple threads update metrics simultaneously
**Solution:** Critical section dengan lock
```python
LOCK.acquire()
metrics['method']['counter'] += 1
LOCK.release()
```

### 4. Memory Leak dari Unlimited Latency Array
**Problem:** `latencies[]` array terus bertambah
**Solution:** Implement rolling window atau periodic cleanup
```python
if len(metrics['method']['latencies']) > 1000:
    metrics['method']['latencies'] = metrics['method']['latencies'][-500:]
```

### 5. ACK Store Growing Indefinitely
**Problem:** `ack_store` dictionary tidak pernah dibersihkan
**Solution:** Cleanup setelah delivery selesai atau timeout
```python
# Di akhir pubsub_deliver_to_target:
LOCK.acquire()
ack_store.pop((msg_id, target), None)
LOCK.release()
```

## Kesimpulan dan Pembelajaran

Dari percobaan ini, mahasiswa diharapkan dapat:

### 1. Konsep Teoritis
- **Memahami perbedaan fundamental** antara komunikasi langsung vs publish-subscribe
- **Mengerti trade-off** antara performa (speed) dan reliabilitas dalam sistem terdistribusi
- **Menganalisis kompleksitas algoritma** untuk delivery mechanisms
- **Memahami probabilistic behavior** dalam network simulation

### 2. Implementasi Praktis
- **Mengimplementasikan multi-threading** untuk menangani konkurensi
- **Menerapkan thread synchronization** menggunakan locks untuk data safety
- **Membuat event-driven architecture** dengan Socket.IO
- **Mengimplementasikan retry mechanism** dengan exponential backoff

### 3. Analisis dan Evaluasi
- **Menganalisis metrik sistem** untuk mengevaluasi kualitas komunikasi
- **Membandingkan performa** dua metode delivery dengan data empiris
- **Mengidentifikasi bottlenecks** dalam sistem terdistribusi
- **Mengoptimasi parameter** berdasarkan requirement spesifik

### 4. Decision Making
- **Membuat keputusan arsitektural** berdasarkan requirement aplikasi:
  - **Gunakan Direct** jika: prioritas speed, toleran terhadap loss, simple implementation
  - **Gunakan PubSub** jika: prioritas reliability, need decoupling, scalability penting
- **Menyeimbangkan trade-offs** antara berbagai non-functional requirements

### 5. Real-World Applications
- **Chat applications**: Butuh reliability (PubSub)
- **Live streaming**: Prioritas low latency (Direct)
- **Financial transactions**: Critical reliability (PubSub dengan high retries)
- **Gaming**: Real-time response (Direct dengan best-effort)
- **IoT sensor data**: Mix - critical data pakai PubSub, telemetry pakai Direct
