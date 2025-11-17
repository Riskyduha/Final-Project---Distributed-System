from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room, leave_room
import threading
import time
import uuid
import statistics

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, async_mode='threading')

# In-memory structures for simulation
clients = {}  # sid -> {'node': 'A'|'B', 'last_seen': timestamp}
metrics = {
    'Direct': {'sent': 0, 'delivered': 0, 'lost': 0, 'latencies': []},
    'PubSub': {'sent': 0, 'delivered': 0, 'lost': 0, 'latencies': []}
}

PUBSUB_TOPIC = 'chat'
subscribers = set()  # node ids subscribed to topic

# Configurable simulation parameters
config = {
    'loss_rate': 10,  # percentage (0-100)
    'latency_min': 50,  # milliseconds
    'latency_max': 250,  # milliseconds
    'max_retries': 2,
    'ack_timeout': 600  # milliseconds
}

lock = threading.Lock()

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    emit('connected', {'msg': 'connected'})

@socketio.on('register')
def handle_register(data):
    node = data.get('node')
    sid = request.sid
    with lock:
        clients[sid] = {'node': node, 'last_seen': time.time()}
    join_room(f'node-{node}')
    # auto-subscribe to pubsub topic
    with lock:
        subscribers.add(node)
    emit('registered', {'node': node})

@socketio.on('disconnect')
def handle_disconnect():
    sid = request.sid
    with lock:
        info = clients.pop(sid, None)
        if info:
            node = info['node']
            subscribers.discard(node)

@socketio.on('update_config')
def handle_update_config(data):
    with lock:
        if 'loss_rate' in data:
            config['loss_rate'] = max(0, min(100, int(data['loss_rate'])))
        if 'latency_min' in data:
            config['latency_min'] = max(0, int(data['latency_min']))
        if 'latency_max' in data:
            config['latency_max'] = max(config['latency_min'], int(data['latency_max']))
        if 'max_retries' in data:
            config['max_retries'] = max(0, int(data['max_retries']))
        if 'ack_timeout' in data:
            config['ack_timeout'] = max(100, int(data['ack_timeout']))
    emit('config_updated', config, broadcast=True)

@socketio.on('send_message')
def handle_send_message(data):
    # data: {from, to, method, content}
    method = data.get('method')
    sender = data.get('from')
    target = data.get('to')
    content = data.get('content')
    msg_id = str(uuid.uuid4())
    timestamp = time.time()
    if method == 'Direct':
        threading.Thread(target=direct_delivery, args=(msg_id, sender, target, content, timestamp)).start()
    else:
        threading.Thread(target=pubsub_publish, args=(msg_id, sender, content, timestamp)).start()
    with lock:
        metrics[method]['sent'] += 1
    emit('sent_ack', {'msg_id': msg_id, 'method': method}, room=request.sid)


def direct_delivery(msg_id, sender, target, content, timestamp):
    # Simulate variable latency and possible loss
    with lock:
        lat_min = config['latency_min'] / 1000.0
        lat_max = config['latency_max'] / 1000.0
        loss_rate = config['loss_rate']
    delay = lat_min + ((lat_max - lat_min) * (uuid.uuid4().int % 100) / 100)
    time.sleep(delay)
    # Simple random-ish loss simulation
    lost = (uuid.uuid4().int % 100) < loss_rate
    now = time.time()
    if lost:
        with lock:
            metrics['Direct']['lost'] += 1
        # notify sender about failure
        socketio.emit('delivery_failed', {'msg_id': msg_id, 'method': 'Direct', 'reason': 'simulated_loss'}, room=request.sid)
        return
    # deliver to room
    payload = {'msg_id': msg_id, 'from': sender, 'to': target, 'content': content, 'method': 'Direct', 'ts': now}
    socketio.emit('message', payload)
    with lock:
        metrics['Direct']['delivered'] += 1
        metrics['Direct']['latencies'].append(now - timestamp)


def pubsub_publish(msg_id, sender, content, timestamp):
    # Publish to topic; deliver to all subscribers with ACK and resend logic
    # For simulation, we deliver to all nodes in subscribers set
    with lock:
        max_retries = config['max_retries']
        timeout = config['ack_timeout'] / 1000.0
    targets = []
    with lock:
        targets = list(subscribers)
    # For the simulation, we deliver using a separate thread per target to emulate concurrency
    threads = []
    for t in targets:
        th = threading.Thread(target=pubsub_deliver_to_target, args=(msg_id, sender, t, content, timestamp, max_retries, timeout))
        th.start()
        threads.append(th)
    # wait for background deliveries to finish (non-blocking in main flow, but we join here to keep metrics consistent)
    for th in threads:
        th.join()


def pubsub_deliver_to_target(msg_id, sender, target, content, timestamp, max_retries, timeout):
    attempt = 0
    delivered = False
    while attempt <= max_retries and not delivered:
        attempt += 1
        # simulated latency
        with lock:
            lat_min = config['latency_min'] / 1000.0
            lat_max = config['latency_max'] / 1000.0
        delay = lat_min + ((lat_max - lat_min) * (uuid.uuid4().int % 100) / 100)
        time.sleep(delay)
        # send message and wait for ack
        payload = {'msg_id': msg_id, 'from': sender, 'to': target, 'content': content, 'method': 'PubSub', 'attempt': attempt, 'ts': time.time()}
        socketio.emit('pubsub_message', payload)
        # wait for ack
        ack_event = threading.Event()
        ack_key = f'ack-{msg_id}-{target}'

        def ack_listener(data):
            if data.get('msg_id') == msg_id and data.get('node') == target:
                ack_event.set()

        socketio.on_event('pubsub_ack_listener', ack_listener)
        # We can't directly attach per-thread listeners in flask-socketio easily; to keep simulation simple
        # we will instead rely on clients to emit 'pubsub_ack' and we'll set a global ack store
        # Poll a global ack store instead.
        global_ack_key = (msg_id, target)
        start = time.time()
        while time.time() - start < timeout:
            with lock:
                # check if ack recorded
                if ack_store.get(global_ack_key):
                    delivered = True
                    break
            time.sleep(0.05)
        if delivered:
            with lock:
                metrics['PubSub']['delivered'] += 1
                metrics['PubSub']['latencies'].append(time.time() - timestamp)
            break
    if not delivered:
        with lock:
            metrics['PubSub']['lost'] += 1

# Global ack store used by pubsub delivery threads
ack_store = {}

@socketio.on('pubsub_ack')
def handle_pubsub_ack(data):
    # data: {msg_id, node}
    msg_id = data.get('msg_id')
    node = data.get('node')
    with lock:
        ack_store[(msg_id, node)] = True

# Periodic metrics broadcaster
def metrics_broadcaster():
    while True:
        time.sleep(0.5)
        snapshot = {}
        with lock:
            for k, v in metrics.items():
                lat_avg = statistics.mean(v['latencies']) if v['latencies'] else 0
                snapshot[k] = {'sent': v['sent'], 'delivered': v['delivered'], 'lost': v['lost'], 'avg_latency': round(lat_avg, 3)}
        socketio.emit('metrics_update', snapshot)

# start background metrics thread
threading.Thread(target=metrics_broadcaster, daemon=True).start()

if __name__ == '__main__':
    print('Starting server on http://localhost:5000')
    socketio.run(app, host='0.0.0.0', port=5000)
