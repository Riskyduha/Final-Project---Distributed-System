Event-Driven Chat Simulation (2 Nodes)

Overview
- Small Flask + Flask-SocketIO app that simulates two nodes (A and B) exchanging messages.
- Two delivery methods: `Direct` (best-effort, simulated loss/latency) and `PubSub` (publish-subscribe with ACK+resend behavior).
- Server uses Python threads to simulate concurrent delivery and to collect metrics.
- Real-time charts (latency and throughput) for visual comparison of both methods.
- Configurable simulation parameters (loss rate, latency range, retries, timeout) adjustable via UI.

Run locally (Windows PowerShell)

1. Create a virtual environment (recommended):

```powershell
python -m venv .venv; .\.venv\Scripts\Activate.ps1
```

2. Install dependencies:

```powershell
pip install -r requirements.txt
```

3. Run the server:

```powershell
python app.py
```

4. Open the UI in a browser at `http://localhost:5000`.
- You can open two browser windows/tabs and register one as `A` and the other as `B` to simulate separate clients.
- Use the method selector to switch between `Direct` and `PubSub`, send messages from either node, and watch the metrics panel to compare behaviour.
- Adjust simulation parameters in real-time:
  - **Loss Rate (%)**: Percentage of messages that will be lost (0-100)
  - **Latency Min/Max (ms)**: Range of simulated network latency
  - **Max Retries**: Number of retry attempts for PubSub delivery
  - **ACK Timeout (ms)**: Timeout for waiting for acknowledgments in PubSub
- View real-time charts showing average latency and throughput for both methods.

Files
- `app.py`: backend server and simulation logic
- `templates/index.html`: simple frontend
- `static/js/app.js`: client-side Socket.IO logic
- `requirements.txt`: Python dependencies

Features
- **Event-Driven Architecture**: Uses Flask-SocketIO for real-time bi-directional communication
- **Multi-threading**: Python threads handle concurrent message delivery and metrics broadcasting
- **Two Delivery Methods**:
  - **Direct**: Simple point-to-point delivery with simulated packet loss
  - **PubSub**: Publish-subscribe with acknowledgments and automatic retry logic
- **Real-time Monitoring**: Live charts showing latency and throughput metrics
- **Dynamic Configuration**: Adjust simulation parameters on-the-fly without restarting
- **Visual Comparison**: Side-by-side comparison of both delivery methods

Notes
- The implementation intentionally uses threads (via `threading.Thread` and Flask-SocketIO with `async_mode='threading'`) to satisfy the multi-threading requirement.
- This is a simulation: latencies and losses are randomized based on configured parameters.
- No external dependencies like XAMPP required - runs entirely with Python and Flask.
