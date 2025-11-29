import os
import json
import threading
import time
import pika
from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit, join_room, leave_room
import eventlet
eventlet.monkey_patch()

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# RabbitMQ config
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")
RABBITMQ_USER = os.getenv("RABBITMQ_USER", "guest")
RABBITMQ_PASS = os.getenv("RABBITMQ_PASS", "guest")
RABBITMQ_VHOST = os.getenv("RABBITMQ_VHOST", "/")

FANOUT_EXCHANGE = "chat.messages"

# Track online users: {sid: nickname}
online_users = {}
users_lock = threading.Lock()

# RabbitMQ connection
_connection = None
_channel = None
_channel_lock = threading.Lock()
_consumer_started = False

def get_rabbit_connection():
    """Get or create RabbitMQ connection"""
    global _connection, _channel
    try:
        if _connection and _connection.is_open and _channel and _channel.is_open:
            return _connection, _channel
    except:
        pass
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            creds = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)
            params = pika.ConnectionParameters(
                host=RABBITMQ_HOST,
                virtual_host=RABBITMQ_VHOST,
                credentials=creds,
                heartbeat=600,
                blocked_connection_timeout=300,
                connection_attempts=3,
                retry_delay=2,
                socket_timeout=10
            )
            _connection = pika.BlockingConnection(params)
            _channel = _connection.channel()
            _channel.exchange_declare(exchange=FANOUT_EXCHANGE, exchange_type='fanout', durable=True)
            print(f"✅ RabbitMQ connected on attempt {attempt + 1}")
            return _connection, _channel
        except Exception as e:
            print(f"❌ RabbitMQ connection attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(2)
    
    raise Exception("Failed to connect to RabbitMQ after retries")

def publish_message(msg_data):
    """Publish message to RabbitMQ fanout exchange"""
    try:
        with _channel_lock:
            conn, ch = get_rabbit_connection()
            ch.basic_publish(
                exchange=FANOUT_EXCHANGE,
                routing_key='',
                body=json.dumps(msg_data).encode(),
                properties=pika.BasicProperties(delivery_mode=2)
            )
            print(f"✅ Message published: {msg_data['from']}: {msg_data['text'][:30]}...")
    except Exception as e:
        print(f"❌ Publish error: {e}")
        # Fallback: broadcast directly via Socket.IO
        print("⚠️ Falling back to direct Socket.IO broadcast")
        socketio.emit('message', msg_data, namespace='/')

def start_consumer():
    """Start RabbitMQ consumer in background thread"""
    global _consumer_started
    if _consumer_started:
        return
    _consumer_started = True
    
    def consume():
        creds = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)
        params = pika.ConnectionParameters(
            host=RABBITMQ_HOST,
            virtual_host=RABBITMQ_VHOST,
            credentials=creds,
            heartbeat=600
        )
        conn = pika.BlockingConnection(params)
        ch = conn.channel()
        ch.exchange_declare(exchange=FANOUT_EXCHANGE, exchange_type='fanout', durable=True)
        
        # Create exclusive queue for this instance
        result = ch.queue_declare(queue='', exclusive=True)
        queue_name = result.method.queue
        ch.queue_bind(exchange=FANOUT_EXCHANGE, queue=queue_name)
        
        def callback(chh, method, properties, body):
            try:
                msg = json.loads(body.decode())
                # Emit to all connected clients via Socket.IO
                socketio.emit('message', msg)
                chh.basic_ack(delivery_tag=method.delivery_tag)
            except Exception as e:
                print(f"Consumer callback error: {e}")
                chh.basic_nack(delivery_tag=method.delivery_tag)
        
        ch.basic_qos(prefetch_count=10)
        ch.basic_consume(queue=queue_name, on_message_callback=callback)
        
        try:
            print("RabbitMQ consumer started")
            ch.start_consuming()
        except Exception as e:
            print(f"Consumer error: {e}")
            try:
                ch.close()
                conn.close()
            except:
                pass
    
    threading.Thread(target=consume, daemon=True).start()

def broadcast_users_list():
    """Broadcast current online users to all clients"""
    with users_lock:
        users = list(online_users.values())
    socketio.emit('users_list', {'users': users}, namespace='/')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/health')
def health():
    return jsonify({"status": "ok"})

@socketio.on('connect')
def handle_connect():
    print(f"Client connected: {request.sid}")
    start_consumer()

@socketio.on('disconnect')
def handle_disconnect():
    sid = request.sid
    with users_lock:
        if sid in online_users:
            nickname = online_users.pop(sid)
            print(f"User disconnected: {nickname}")
            # Notify others
            emit('user_left', {'nickname': nickname}, broadcast=True)
            broadcast_users_list()

@socketio.on('join')
def handle_join(data):
    nickname = data.get('nickname', '').strip()
    if not nickname:
        return
    
    sid = request.sid
    with users_lock:
        # Check if nickname already taken
        if nickname in online_users.values():
            emit('join_error', {'error': 'Nickname already taken'})
            return
        online_users[sid] = nickname
    
    print(f"User joined: {nickname}")
    
    # Notify all clients
    emit('user_joined', {'nickname': nickname}, broadcast=True)
    broadcast_users_list()
    
    # Confirm to sender
    emit('join_success', {'nickname': nickname})

@socketio.on('send_message')
def handle_send_message(data):
    print(f"📥 Received send_message event: {data}")
    
    sid = request.sid
    with users_lock:
        nickname = online_users.get(sid)
    
    if not nickname:
        print(f"⚠️ Message from unknown user (sid: {sid})")
        return
    
    text = data.get('text', '').strip()
    if not text:
        print(f"⚠️ Empty message from {nickname}")
        return
    
    msg = {
        'from': nickname,
        'text': text,
        'timestamp': time.time()
    }
    
    print(f"📨 Message from {nickname}: {text[:50]}...")
    
    # Broadcast directly via Socket.IO
    print(f"📢 Broadcasting message to all clients...")
    print(f"📋 Message data: {msg}")
    socketio.emit('message', msg, namespace='/')
    print(f"✅ Message broadcast complete")

@socketio.on('typing')
def handle_typing(data):
    sid = request.sid
    with users_lock:
        nickname = online_users.get(sid)
    
    if not nickname:
        return
    
    is_typing = data.get('typing', False)
    # Broadcast to all except sender
    emit('user_typing', {'nickname': nickname, 'typing': is_typing}, broadcast=True, include_self=False)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=False)