from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
import pika
import threading
import time
import json
import uuid

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret_control_panel'
socketio = SocketIO(app, cors_allowed_origins="*")

RABBITMQ_HOST = 'localhost'

# RabbitMQ Connection
connection = None
channel = None
callback_queue = None

# Storage for RPC responses
rpc_responses = {}

def get_rabbitmq_connection():
    """Establish RabbitMQ connection"""
    global connection, channel, callback_queue
    try:
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=RABBITMQ_HOST, heartbeat=600)
        )
        channel = connection.channel()
        
        # Declare callback queue for RPC responses
        result = channel.queue_declare(queue='', exclusive=True)
        callback_queue = result.method.queue
        
        print("[Control Panel] Connected to RabbitMQ")
        return callback_queue
    except Exception as e:
        print(f"[Control Panel] Error connecting to RabbitMQ: {e}")
        return None

def consume_rpc_responses():
    """Consume RPC responses"""
    # Create dedicated connection for consumer thread
    conn = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST, heartbeat=600))
    ch = conn.channel()
    result = ch.queue_declare(queue='', exclusive=True)
    response_queue = result.method.queue
    
    def on_response(ch, method, props, body):
        try:
            correlation_id = props.correlation_id
            response = json.loads(body)
            
            # Store response
            if correlation_id in rpc_responses:
                rpc_responses[correlation_id] = response
            
            # Emit to frontend
            socketio.emit('rpc_response', {
                'correlation_id': correlation_id,
                'response': response
            })
            
            ch.basic_ack(delivery_tag=method.delivery_tag)
        except Exception as e:
            print(f"[Control Panel] Error processing RPC response: {e}")
    
    ch.basic_consume(queue=response_queue, on_message_callback=on_response)
    print("[Control Panel] Listening for RPC responses...")
    
    # Store response queue for sending RPC calls
    global callback_queue
    callback_queue = response_queue
    
    ch.start_consuming()

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    emit('connected', {'status': 'connected'})

@socketio.on('rpc_call')
def handle_rpc_call(data):
    """Make RPC call to a node"""
    try:
        target_node = data.get('node')  # 'A' or 'B'
        action = data.get('action', 'get_status')
        
        # Generate correlation ID
        correlation_id = str(uuid.uuid4())
        
        # Prepare request
        request = {
            'action': action,
            'timestamp': time.time()
        }
        
        # Initialize response storage
        rpc_responses[correlation_id] = None
        
        # Send RPC request
        channel.basic_publish(
            exchange='',
            routing_key=f'rpc_queue_{target_node}',
            properties=pika.BasicProperties(
                reply_to=callback_queue,
                correlation_id=correlation_id,
                delivery_mode=2
            ),
            body=json.dumps(request)
        )
        
        emit('rpc_sent', {
            'correlation_id': correlation_id,
            'node': target_node,
            'action': action
        })
        
        # Start timeout thread
        def check_timeout():
            time.sleep(5)  # 5 second timeout
            if correlation_id in rpc_responses and rpc_responses[correlation_id] is None:
                socketio.emit('rpc_timeout', {
                    'correlation_id': correlation_id,
                    'node': target_node
                })
                del rpc_responses[correlation_id]
        
        threading.Thread(target=check_timeout, daemon=True).start()
        
    except Exception as e:
        emit('error', {'message': str(e)})

@socketio.on('query_all_nodes')
def handle_query_all_nodes():
    """Query all nodes via RPC"""
    try:
        for node in ['A', 'B']:
            correlation_id = str(uuid.uuid4())
            request = {
                'action': 'get_status',
                'timestamp': time.time()
            }
            
            rpc_responses[correlation_id] = None
            
            channel.basic_publish(
                exchange='',
                routing_key=f'rpc_queue_{node}',
                properties=pika.BasicProperties(
                    reply_to=callback_queue,
                    correlation_id=correlation_id,
                    delivery_mode=2
                ),
                body=json.dumps(request)
            )
        
        emit('query_sent', {'nodes': ['A', 'B']})
    except Exception as e:
        emit('error', {'message': str(e)})

def start_background_threads():
    """Start RabbitMQ consumer threads"""
    queue = get_rabbitmq_connection()
    if queue:
        # Give RabbitMQ time to initialize
        time.sleep(2)
        
        # Start RPC response consumer
        rpc_thread = threading.Thread(target=consume_rpc_responses, daemon=True)
        rpc_thread.start()

if __name__ == '__main__':
    print("Starting Control Panel on http://localhost:5003")
    start_background_threads()
    socketio.run(app, host='0.0.0.0', port=5003, debug=False)
