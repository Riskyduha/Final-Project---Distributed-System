# Final Project - Distributed System with RabbitMQ

Sistem terdistribusi dengan 3 window terpisah (Node A, Node B, Control Panel) yang mengimplementasikan 3 metode komunikasi: **Direct Exchange**, **Pub/Sub (Fanout)**, dan **RPC (Remote Procedure Call)**.

## 📋 Fitur

### 🖥️ Node A & Node B
- **Direct Messaging**: Kirim pesan langsung ke node tertentu
- **Pub/Sub Broadcasting**: Broadcast pesan ke semua node yang subscribe
- **RPC Server**: Menerima request status dari Control Panel
- **Real-time Metrics**: Monitor jumlah pesan dikirim/diterima dan latency
- **WebSocket UI**: Interface web yang responsive

### 🎛️ Control Panel
- **RPC Client**: Query status dari Node A dan Node B via RPC
- **Real-time Monitoring**: Monitor metrics dari semua nodes
- **Auto-refresh**: Otomatis query nodes setiap 5 detik
- **Visual Dashboard**: Charts untuk visualisasi data
- **Event Logging**: Log semua aktivitas sistem

## 🏗️ Arsitektur

```
┌─────────────┐         ┌─────────────┐
│   Node A    │         │   Node B    │
│  Port: 5001 │         │  Port: 5002 │
└──────┬──────┘         └──────┬──────┘
       │                       │
       │    Direct Exchange    │
       ├───────────────────────┤
       │                       │
       │   PubSub Exchange     │
       ├───────────────────────┤
       │                       │
       └───────┬───────────────┘
               │
        ┌──────▼──────┐
        │  RabbitMQ   │
        │  Port: 5672 │
        │  Mgmt: 15672│
        └──────┬──────┘
               │
        ┌──────▼──────┐
        │   Control   │
        │    Panel    │
        │  Port: 5003 │
        └─────────────┘
```

## 🚀 Cara Menjalankan

### Opsi 1: Menggunakan Docker (Recommended)

#### Prerequisites
- Docker Desktop terinstall
- Docker Compose terinstall

#### Langkah-langkah:

1. **Clone repository**
```bash
git clone <repository-url>
cd Final-Project---Distributed-System
```

2. **Jalankan dengan Docker Compose**
```bash
docker-compose up --build
```

3. **Akses aplikasi**
   - Node A: http://localhost:5001
   - Node B: http://localhost:5002
   - Control Panel: http://localhost:5003
   - RabbitMQ Management: http://localhost:15672 (username: admin, password: admin)

4. **Stop aplikasi**
```bash
docker-compose down
```

### Opsi 2: Menjalankan Manual (Tanpa Docker)

#### Prerequisites
- Python 3.11+
- RabbitMQ Server terinstall dan running

#### Langkah-langkah:

1. **Install RabbitMQ**
   - Download dari: https://www.rabbitmq.com/download.html
   - Install dan jalankan service RabbitMQ

2. **Setup Node A**
```bash
cd node_a
pip install -r requirements.txt
python app.py
```

3. **Setup Node B** (Terminal baru)
```bash
cd node_b
pip install -r requirements.txt
python app.py
```

4. **Setup Control Panel** (Terminal baru)
```bash
cd control_panel
pip install -r requirements.txt
python app.py
```

5. **Akses aplikasi**
   - Node A: http://localhost:5001
   - Node B: http://localhost:5002
   - Control Panel: http://localhost:5003

## 📖 Cara Menggunakan

### 1. Testing Direct Message
1. Buka Node A (http://localhost:5001)
2. Pada section "Send Direct Message", pilih target Node B
3. Ketik pesan dan klik "Send Direct →"
4. Buka Node B (http://localhost:5002) untuk melihat pesan yang diterima
5. Perhatikan latency yang tercatat

### 2. Testing Pub/Sub Broadcast
1. Buka Node A atau Node B
2. Pada section "Broadcast (PubSub)", ketik pesan
3. Klik "Broadcast to All Nodes →"
4. Pesan akan diterima oleh semua nodes yang subscribe (A dan B)
5. Check message log di kedua nodes

### 3. Testing RPC (Remote Procedure Call)
1. Buka Control Panel (http://localhost:5003)
2. Klik tombol "Query All Nodes (RPC)" atau "Query" pada node tertentu
3. Control Panel akan mengirim RPC request ke nodes
4. Status dan metrics dari nodes akan ditampilkan
5. Perhatikan RPC Activity chart yang terupdate

### 4. Monitoring & Metrics
- **Node A/B**: Metrics ditampilkan di bagian bawah halaman
  - Direct Sent/Received
  - PubSub Sent/Received
  - Average Latency
- **Control Panel**: 
  - Real-time node status
  - Aggregated metrics
  - Event logs
  - Visual charts

## 🔧 Konfigurasi

### Environment Variables
Edit di `docker-compose.yml` atau set manual:
- `RABBITMQ_HOST`: Hostname RabbitMQ (default: localhost)

### RabbitMQ Management
- URL: http://localhost:15672
- Username: `admin`
- Password: `admin`

## 📊 Metode Komunikasi

### 1. Direct Exchange
- **Pattern**: Point-to-Point
- **Use Case**: Mengirim pesan ke node spesifik
- **Routing**: Menggunakan routing key `to_A` atau `to_B`
- **Reliability**: Persistent messages dengan acknowledgment

### 2. Pub/Sub (Fanout Exchange)
- **Pattern**: Broadcasting
- **Use Case**: Broadcast pesan ke semua nodes
- **Routing**: Fanout ke semua queue yang terhubung
- **Reliability**: All subscribers receive the message

### 3. RPC (Remote Procedure Call)
- **Pattern**: Request-Response
- **Use Case**: Control Panel query node status
- **Routing**: Direct queue dengan reply_to callback
- **Reliability**: Timeout handling (5 seconds)

## 🧪 Testing Scenario

### Scenario 1: Basic Communication
1. Node A kirim Direct message ke Node B
2. Node B kirim Direct message ke Node A
3. Verify latency < 100ms

### Scenario 2: Broadcasting
1. Node A broadcast PubSub message
2. Verify Node A dan Node B menerima message
3. Node B broadcast PubSub message
4. Verify Node A dan Node B menerima message

### Scenario 3: Monitoring via RPC
1. Control Panel query Node A status
2. Control Panel query Node B status
3. Verify metrics ditampilkan dengan benar
4. Verify auto-refresh setiap 5 detik

### Scenario 4: Performance Testing
1. Kirim 10 Direct messages dari A ke B
2. Kirim 10 PubSub broadcasts
3. Query RPC 10 kali
4. Analyze latency dan throughput di metrics

## 🐛 Troubleshooting

### RabbitMQ Connection Error
```
Error connecting to RabbitMQ: [Errno 111] Connection refused
```
**Solution**: 
- Pastikan RabbitMQ service running: `rabbitmq-server`
- Check port 5672 tidak digunakan aplikasi lain
- Jika pakai Docker, tunggu RabbitMQ healthcheck pass

### Port Already in Use
```
Address already in use: bind
```
**Solution**:
- Stop aplikasi yang menggunakan port (5001, 5002, 5003)
- Atau ubah port di `app.py` dan `docker-compose.yml`

### WebSocket Connection Failed
```
WebSocket connection to 'ws://localhost:5001/socket.io/' failed
```
**Solution**:
- Pastikan Flask-SocketIO terinstall
- Check browser console untuk error details
- Refresh halaman

## 📁 Struktur Project

```
Final-Project---Distributed-System/
├── node_a/
│   ├── app.py
│   ├── Dockerfile
│   ├── requirements.txt
│   └── templates/
│       └── index.html
├── node_b/
│   ├── app.py
│   ├── Dockerfile
│   ├── requirements.txt
│   └── templates/
│       └── index.html
├── control_panel/
│   ├── app.py
│   ├── Dockerfile
│   ├── requirements.txt
│   └── templates/
│       └── index.html
├── docker-compose.yml
└── README.md
```

## 🎓 Penelitian

Project ini cocok untuk penelitian tentang:
- **Perbandingan Metode Komunikasi**: Direct vs PubSub vs RPC
- **Performance Analysis**: Latency, Throughput, Reliability
- **Scalability**: Menambah lebih banyak nodes
- **Fault Tolerance**: Testing dengan node failure
- **Load Balancing**: Distribusi pesan ke multiple consumers

## 📝 License

MIT License - Free for educational use

## 👨‍💻 Author

Tugas Akhir - Sistem Terdistribusi
Semester 1 - S2

---

**Happy Testing! 🚀**
