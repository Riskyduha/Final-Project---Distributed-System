import os
import json
import time
import uuid
import statistics
import threading

import eventlet
eventlet.monkey_patch()

import pika
from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room, leave_room

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, async_mode='eventlet')

# In-memory structures for simulation
clients = {}  # sid -> {'node': 'A'|'B', 'last_seen': timestamp}
metrics = {
    'Direct': {'sent': 0, 'delivered': 0, 'lost': 0, 'latencies': []},
    'PubSub': {'sent': 0, 'delivered': 0, 'lost': 0, 'latencies': []}
}

# Minimal config placeholders (kept for UI compatibility)
config = {
    'loss_rate': 0,
    'latency_min': 0,
    'latency_max': 0,
    'max_retries': 0,
    'ack_timeout': 600
}

lock = threading.Lock()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/health')
def health():
    return {'status': 'ok'}, 200

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
    # Start RabbitMQ consumers for this node (if not already running)
    start_consumer_for_node(node)
    emit('registered', {'node': node})

@socketio.on('disconnect')
def handle_disconnect():
    sid = request.sid
    with lock:
        info = clients.pop(sid, None)
        # Consumers are long-lived; we don't stop them per disconnect.

@socketio.on('update_config')
def handle_update_config(data):
    with lock:
        # Accept but ignore most simulation params; keep ack_timeout for UI
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
    body = {
        'msg_id': msg_id,
        'from': sender,
        'to': target,
        'content': content,
        'method': method,
        'ts': timestamp
    }
    if method == 'Direct':
        publish_direct(target, body)
    else:
        publish_pubsub(body)
    with lock:
        metrics[method]['sent'] += 1
    emit('sent_ack', {'msg_id': msg_id, 'method': method}, room=request.sid)

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


# =========================
# RabbitMQ Integration
# =========================

RABBITMQ_HOST = os.environ.get('RABBITMQ_HOST', 'localhost')
RABBITMQ_PORT = int(os.environ.get('RABBITMQ_PORT', '5672'))
RABBITMQ_USER = os.environ.get('RABBITMQ_USER', os.environ.get('RABBITMQ_DEFAULT_USER', 'guest'))
RABBITMQ_PASS = os.environ.get('RABBITMQ_PASS', os.environ.get('RABBITMQ_DEFAULT_PASS', 'guest'))
RABBITMQ_VHOST = os.environ.get('RABBITMQ_VHOST', '/')

DIRECT_EXCHANGE = 'chat.direct'
PUBSUB_EXCHANGE = 'chat.pubsub'

publisher_lock = threading.Lock()
publisher_conn = None
publisher_channel = None


def rabbit_params():
    creds = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)
    return pika.ConnectionParameters(
        host=RABBITMQ_HOST,
        port=RABBITMQ_PORT,
        virtual_host=RABBITMQ_VHOST,
        credentials=creds,
        heartbeat=30,
        blocked_connection_timeout=30,
    )


def ensure_publisher():
    global publisher_conn, publisher_channel
    if publisher_conn and publisher_channel and publisher_conn.is_open and publisher_channel.is_open:
        return
    try:
        publisher_conn = pika.BlockingConnection(rabbit_params())
        publisher_channel = publisher_conn.channel()
        publisher_channel.exchange_declare(exchange=DIRECT_EXCHANGE, exchange_type='direct', durable=False)
        publisher_channel.exchange_declare(exchange=PUBSUB_EXCHANGE, exchange_type='fanout', durable=False)
    except Exception as e:
        print(f"[RabbitMQ] Publisher setup error: {e}")
        publisher_conn = None
        publisher_channel = None


def publish_direct(target, body: dict):
    with publisher_lock:
        ensure_publisher()
        if not publisher_channel:
            # retry once after short delay
            time.sleep(0.5)
            ensure_publisher()
            if not publisher_channel:
                print("[RabbitMQ] publish_direct skipped: channel unavailable")
                return
        payload = json.dumps(body)
        try:
            publisher_channel.basic_publish(
                exchange=DIRECT_EXCHANGE,
                routing_key=target,
                body=payload,
                properties=pika.BasicProperties(content_type='application/json')
            )
        except Exception as e:
            print(f"[RabbitMQ] publish_direct error: {e}")
            publisher_channel = None


def publish_pubsub(body: dict):
    with publisher_lock:
        ensure_publisher()
        if not publisher_channel:
            time.sleep(0.5)
            ensure_publisher()
            if not publisher_channel:
                print("[RabbitMQ] publish_pubsub skipped: channel unavailable")
                return
        payload = json.dumps(body)
        try:
            publisher_channel.basic_publish(
                exchange=PUBSUB_EXCHANGE,
                routing_key='',
                body=payload,
                properties=pika.BasicProperties(content_type='application/json')
            )
        except Exception as e:
            print(f"[RabbitMQ] publish_pubsub error: {e}")
            publisher_channel = None


def queue_name_direct(node: str) -> str:
    return f"queue.direct.{node}"


def queue_name_pubsub(node: str) -> str:
    return f"queue.pubsub.{node}"


consumer_threads = {}


def start_consumer_for_node(node: str):
    if node in consumer_threads and consumer_threads[node].is_alive():
        return
    t = threading.Thread(target=consumer_worker, args=(node,), daemon=True)
    t.start()
    consumer_threads[node] = t


def consumer_worker(node: str):
    while True:
        try:
            conn = pika.BlockingConnection(rabbit_params())
            ch = conn.channel()
            ch.exchange_declare(exchange=DIRECT_EXCHANGE, exchange_type='direct', durable=False)
            ch.exchange_declare(exchange=PUBSUB_EXCHANGE, exchange_type='fanout', durable=False)

            qd = ch.queue_declare(queue=queue_name_direct(node), durable=False)
            ch.queue_bind(queue=qd.method.queue, exchange=DIRECT_EXCHANGE, routing_key=node)

            qp = ch.queue_declare(queue=queue_name_pubsub(node), durable=False)
            ch.queue_bind(queue=qp.method.queue, exchange=PUBSUB_EXCHANGE)

            ch.basic_qos(prefetch_count=50)

            def on_direct(ch_, method, props, body):
                try:
                    data = json.loads(body.decode('utf-8'))
                except Exception:
                    data = {}
                # Ensure 'to' matches this node
                data['to'] = node
                data['method'] = 'Direct'
                socketio.emit('message', data)
                # update metrics
                try:
                    sent_ts = float(data.get('ts', time.time()))
                    with lock:
                        metrics['Direct']['delivered'] += 1
                        metrics['Direct']['latencies'].append(max(0.0, time.time() - sent_ts))
                except Exception:
                    pass

            def on_pubsub(ch_, method, props, body):
                try:
                    data = json.loads(body.decode('utf-8'))
                except Exception:
                    data = {}
                data['to'] = node
                data['method'] = 'PubSub'
                data['attempt'] = data.get('attempt', 1)
                socketio.emit('pubsub_message', data)
                try:
                    sent_ts = float(data.get('ts', time.time()))
                    with lock:
                        metrics['PubSub']['delivered'] += 1
                        metrics['PubSub']['latencies'].append(max(0.0, time.time() - sent_ts))
                except Exception:
                    pass

            ch.basic_consume(queue=queue_name_direct(node), on_message_callback=on_direct, auto_ack=True)
            ch.basic_consume(queue=queue_name_pubsub(node), on_message_callback=on_pubsub, auto_ack=True)

            print(f"[RabbitMQ] Consumer started for node {node}")
            ch.start_consuming()
        except Exception as e:
            print(f"[RabbitMQ] Consumer error for node {node}: {e}. Reconnecting in 2s...")
            time.sleep(2)
            continue


if __name__ == '__main__':
    print('Starting server on http://localhost:5000')
    socketio.run(app, host='0.0.0.0', port=5000)
