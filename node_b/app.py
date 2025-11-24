from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
import pika
import threading
import time
import json
import uuid

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret_node_b'
socketio = SocketIO(app, cors_allowed_origins="*")

NODE_ID = 'B'
RABBITMQ_HOST = 'localhost'

# Metrics
metrics = {
    'Direct': {'sent': 0, 'received': 0, 'latency': []},
    'PubSub': {'sent': 0, 'received': 0, 'latency': []},
    'RPC': {'requests': 0, 'responses': 0, 'latency': []}
}

# RabbitMQ Connection
connection = None
channel = None
rpc_response_data = {}

def get_rabbitmq_connection():
    """Establish RabbitMQ connection"""
    global connection, channel
    try:
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=RABBITMQ_HOST, heartbeat=600)
        )
        channel = connection.channel()
        
        # Declare exchanges
        channel.exchange_declare(exchange='direct_exchange', exchange_type='direct', durable=True)
        channel.exchange_declare(exchange='pubsub_exchange', exchange_type='fanout', durable=True)
        
        # Declare queues for Direct
        channel.queue_declare(queue=f'node_{NODE_ID}_direct', durable=True)
        channel.queue_bind(exchange='direct_exchange', queue=f'node_{NODE_ID}_direct', routing_key=f'to_{NODE_ID}')
        
        # Declare queue for PubSub
        result = channel.queue_declare(queue='', exclusive=True)
        pubsub_queue = result.method.queue
        channel.queue_bind(exchange='pubsub_exchange', queue=pubsub_queue)
        
        # Declare RPC queue
        channel.queue_declare(queue=f'rpc_queue_{NODE_ID}', durable=True)
        
        print(f"[Node {NODE_ID}] Connected to RabbitMQ")
        return pubsub_queue
    except Exception as e:
        print(f"[Node {NODE_ID}] Error connecting to RabbitMQ: {e}")
        return None

def consume_direct_messages():
    """Consume Direct messages"""
    # Create dedicated connection for this consumer thread
    conn = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST, heartbeat=600))
    ch = conn.channel()
    
    def callback(ch, method, properties, body):
        try:
            msg = json.loads(body)
            msg['received_at'] = time.time()
            latency = msg['received_at'] - msg['timestamp']
            
            metrics['Direct']['received'] += 1
            metrics['Direct']['latency'].append(latency)
            
            socketio.emit('message_received', {
                'method': 'Direct',
                'from': msg['from'],
                'content': msg['content'],
                'latency': round(latency * 1000, 2)
            })
            
            ch.basic_ack(delivery_tag=method.delivery_tag)
        except Exception as e:
            print(f"[Node {NODE_ID}] Error processing direct message: {e}")
    
    ch.basic_consume(queue=f'node_{NODE_ID}_direct', on_message_callback=callback)
    print(f"[Node {NODE_ID}] Listening for Direct messages...")
    ch.start_consuming()

def consume_pubsub_messages(pubsub_queue):
    """Consume PubSub messages"""
    # Create dedicated connection for this consumer thread
    conn = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST, heartbeat=600))
    ch = conn.channel()
    
    # Re-bind to pubsub exchange
    result = ch.queue_declare(queue='', exclusive=True)
    queue_name = result.method.queue
    ch.queue_bind(exchange='pubsub_exchange', queue=queue_name)
    
    def callback(ch, method, properties, body):
        try:
            msg = json.loads(body)
            msg['received_at'] = time.time()
            latency = msg['received_at'] - msg['timestamp']
            
            metrics['PubSub']['received'] += 1
            metrics['PubSub']['latency'].append(latency)
            
            socketio.emit('message_received', {
                'method': 'PubSub',
                'from': msg['from'],
                'content': msg['content'],
                'latency': round(latency * 1000, 2)
            })
            
            ch.basic_ack(delivery_tag=method.delivery_tag)
        except Exception as e:
            print(f"[Node {NODE_ID}] Error processing pubsub message: {e}")
    
    ch.basic_consume(queue=queue_name, on_message_callback=callback)
    print(f"[Node {NODE_ID}] Listening for PubSub messages...")
    ch.start_consuming()

def consume_rpc_requests():
    """Consume RPC requests and respond"""
    # Create dedicated connection for this consumer thread
    conn = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST, heartbeat=600))
    ch = conn.channel()
    ch.queue_declare(queue=f'rpc_queue_{NODE_ID}', durable=True)
    
    def on_request(ch, method, props, body):
        try:
            request = json.loads(body)
            print(f"[Node {NODE_ID}] RPC Request: {request}")
            
            # Process request
            if request.get('action') == 'get_status':
                response = {
                    'node': NODE_ID,
                    'status': 'online',
                    'metrics': {
                        'direct_sent': metrics['Direct']['sent'],
                        'direct_received': metrics['Direct']['received'],
                        'pubsub_sent': metrics['PubSub']['sent'],
                        'pubsub_received': metrics['PubSub']['received'],
                        'rpc_requests': metrics['RPC']['requests']
                    },
                    'timestamp': time.time()
                }
            else:
                response = {'error': 'Unknown action'}
            
            # Send response
            ch.basic_publish(
                exchange='',
                routing_key=props.reply_to,
                properties=pika.BasicProperties(correlation_id=props.correlation_id),
                body=json.dumps(response)
            )
            ch.basic_ack(delivery_tag=method.delivery_tag)
            
            metrics['RPC']['requests'] += 1
        except Exception as e:
            print(f"[Node {NODE_ID}] Error processing RPC request: {e}")
    
    ch.basic_consume(queue=f'rpc_queue_{NODE_ID}', on_message_callback=on_request)
    print(f"[Node {NODE_ID}] RPC Server listening...")
    ch.start_consuming()

@app.route('/')
def index():
    return render_template('index.html', node_id=NODE_ID)

@socketio.on('connect')
def handle_connect():
    emit('connected', {'node': NODE_ID, 'status': 'connected'})

@socketio.on('send_direct')
def handle_send_direct(data):
    """Send Direct message to specific node"""
    try:
        target = data.get('target')
        content = data.get('content')
        
        message = {
            'from': NODE_ID,
            'to': target,
            'content': content,
            'timestamp': time.time(),
            'msg_id': str(uuid.uuid4())
        }
        
        channel.basic_publish(
            exchange='direct_exchange',
            routing_key=f'to_{target}',
            body=json.dumps(message),
            properties=pika.BasicProperties(delivery_mode=2)
        )
        
        metrics['Direct']['sent'] += 1
        emit('message_sent', {'method': 'Direct', 'target': target, 'content': content})
    except Exception as e:
        emit('error', {'message': str(e)})

@socketio.on('send_pubsub')
def handle_send_pubsub(data):
    """Publish message to all subscribers"""
    try:
        content = data.get('content')
        
        message = {
            'from': NODE_ID,
            'content': content,
            'timestamp': time.time(),
            'msg_id': str(uuid.uuid4())
        }
        
        channel.basic_publish(
            exchange='pubsub_exchange',
            routing_key='',
            body=json.dumps(message),
            properties=pika.BasicProperties(delivery_mode=2)
        )
        
        metrics['PubSub']['sent'] += 1
        emit('message_sent', {'method': 'PubSub', 'content': content})
    except Exception as e:
        emit('error', {'message': str(e)})

@socketio.on('get_metrics')
def handle_get_metrics():
    """Return current metrics"""
    try:
        emit('metrics_update', {
            'direct': {
                'sent': metrics['Direct']['sent'],
                'received': metrics['Direct']['received'],
                'avg_latency': round(sum(metrics['Direct']['latency']) / len(metrics['Direct']['latency']) * 1000, 2) if metrics['Direct']['latency'] else 0
            },
            'pubsub': {
                'sent': metrics['PubSub']['sent'],
                'received': metrics['PubSub']['received'],
                'avg_latency': round(sum(metrics['PubSub']['latency']) / len(metrics['PubSub']['latency']) * 1000, 2) if metrics['PubSub']['latency'] else 0
            },
            'rpc': {
                'requests': metrics['RPC']['requests'],
                'responses': metrics['RPC']['responses']
            }
        })
    except Exception as e:
        emit('error', {'message': str(e)})

def start_background_threads():
    """Start RabbitMQ consumer threads"""
    pubsub_queue = get_rabbitmq_connection()
    if pubsub_queue:
        # Give RabbitMQ time to initialize
        time.sleep(2)
        
        # Start Direct consumer
        direct_thread = threading.Thread(target=consume_direct_messages, daemon=True)
        direct_thread.start()
        
        # Start PubSub consumer
        pubsub_thread = threading.Thread(target=lambda: consume_pubsub_messages(pubsub_queue), daemon=True)
        pubsub_thread.start()
        
        # Start RPC server
        rpc_thread = threading.Thread(target=consume_rpc_requests, daemon=True)
        rpc_thread.start()

if __name__ == '__main__':
    print(f"Starting Node {NODE_ID} on http://localhost:5002")
    start_background_threads()
    socketio.run(app, host='0.0.0.0', port=5002, debug=False)
