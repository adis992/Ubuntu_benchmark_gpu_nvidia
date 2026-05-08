"""
Main Flask Server for GPU Benchmark Tool
Provides REST API and WebSocket for real-time monitoring
"""

from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import threading
import time
import json
import logging
import os
from datetime import datetime

from gpu_monitor import GPUMonitor
from benchmark import BenchmarkWorkload

# Setup logging
log_dir = 'logs'
log_file = os.path.join(log_dir, 'server.log')

# Create logs directory with proper permissions
try:
    os.makedirs(log_dir, exist_ok=True)
    # Ensure we can write to the log file
    with open(log_file, 'a') as f:
        pass
except (PermissionError, OSError) as e:
    # If we can't write to logs/, use a temp directory
    import tempfile
    log_dir = tempfile.gettempdir()
    log_file = os.path.join(log_dir, 'nvidia-gpu-benchmark.log')
    print(f"Warning: Cannot write to logs/, using {log_file}")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load configuration
with open('config.json', 'r') as f:
    config = json.load(f)

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'nvidia-benchmark-secret-key-change-in-production'
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Initialize GPU monitor and benchmark
gpu_monitor = GPUMonitor()
benchmark_workload = BenchmarkWorkload(gpu_monitor, config)

# Global state
monitoring_active = False
monitoring_thread = None


def monitoring_loop():
    """Background thread for continuous GPU monitoring"""
    global monitoring_active
    logger.info("Monitoring loop started")
    
    while monitoring_active:
        try:
            # Get all GPU info
            gpus_info = gpu_monitor.get_all_gpus_info()
            
            # Get active benchmarks
            active_benchmarks = benchmark_workload.get_active_benchmarks()
            
            # Emit to all connected clients
            socketio.emit('gpu_update', {
                'gpus': gpus_info,
                'benchmarks': active_benchmarks,
                'timestamp': datetime.now().isoformat()
            })
            
            time.sleep(config['monitoring']['poll_interval'])
        except Exception as e:
            logger.error(f"Error in monitoring loop: {e}")
            time.sleep(1)
    
    logger.info("Monitoring loop stopped")


@app.route('/')
def index():
    """Serve main dashboard"""
    return render_template('index.html')


@app.route('/api/status')
def api_status():
    """Get system status"""
    return jsonify({
        'status': 'running',
        'monitoring_active': monitoring_active,
        'gpu_count': gpu_monitor.gpu_count,
        'timestamp': datetime.now().isoformat()
    })


@app.route('/api/gpus')
def api_gpus():
    """Get all GPU information"""
    gpus = gpu_monitor.get_all_gpus_info()
    return jsonify({'gpus': gpus})


@app.route('/api/gpu/<int:gpu_id>')
def api_gpu_detail(gpu_id):
    """Get detailed information about a specific GPU"""
    gpu_info = gpu_monitor.get_gpu_info(gpu_id)
    if gpu_info:
        return jsonify(gpu_info)
    return jsonify({'error': 'GPU not found'}), 404


@app.route('/api/benchmark/start', methods=['POST'])
def api_benchmark_start():
    """Start benchmark on specified GPUs"""
    data = request.json
    
    gpu_indices = data.get('gpu_indices', [])
    duration = data.get('duration', config['benchmark']['default_duration'])
    stress_level = data.get('stress_level', 100)
    
    # Validate duration
    max_duration = config['benchmark']['max_duration']
    if duration > max_duration:
        return jsonify({'error': f'Duration exceeds maximum of {max_duration} seconds'}), 400
    
    result = benchmark_workload.start_benchmark(gpu_indices, duration, stress_level)
    
    if result['success']:
        return jsonify(result)
    return jsonify(result), 400


@app.route('/api/benchmark/stop/<benchmark_id>', methods=['POST'])
def api_benchmark_stop(benchmark_id):
    """Stop a running benchmark"""
    result = benchmark_workload.stop_benchmark(benchmark_id)
    
    if result['success']:
        return jsonify(result)
    return jsonify(result), 404


@app.route('/api/benchmarks/active')
def api_benchmarks_active():
    """Get all active benchmarks"""
    return jsonify(benchmark_workload.get_active_benchmarks())


@app.route('/api/benchmarks/results')
def api_benchmarks_results():
    """Get benchmark results"""
    return jsonify(benchmark_workload.get_benchmark_results())


@app.route('/api/fan/set', methods=['POST'])
def api_fan_set():
    """Set fan speed for a GPU"""
    data = request.json
    gpu_id = data.get('gpu_id')
    speed = data.get('speed', 50)
    
    if gpu_id is None:
        return jsonify({'error': 'gpu_id is required'}), 400
    
    # Validate speed
    speed = max(0, min(100, speed))
    
    success = gpu_monitor.set_fan_speed(gpu_id, speed)
    
    if success:
        return jsonify({'success': True, 'gpu_id': gpu_id, 'speed': speed})
    return jsonify({'error': 'Failed to set fan speed'}), 500


@app.route('/api/fan/reset', methods=['POST'])
def api_fan_reset():
    """Reset fan control to automatic for a GPU"""
    data = request.json
    gpu_id = data.get('gpu_id')
    
    if gpu_id is None:
        return jsonify({'error': 'gpu_id is required'}), 400
    
    success = gpu_monitor.reset_fan_control(gpu_id)
    
    if success:
        return jsonify({'success': True, 'gpu_id': gpu_id})
    return jsonify({'error': 'Failed to reset fan control'}), 500


@app.route('/api/config')
def api_config():
    """Get current configuration"""
    return jsonify(config)


@app.route('/api/config/update', methods=['POST'])
def api_config_update():
    """Update configuration"""
    global config
    data = request.json
    
    # Update config (be careful with what we allow to be updated)
    allowed_keys = ['benchmark', 'monitoring', 'safety']
    
    for key in allowed_keys:
        if key in data:
            config[key].update(data[key])
    
    # Save to file
    try:
        with open('config.json', 'w') as f:
            json.dump(config, f, indent=2)
        return jsonify({'success': True, 'config': config})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# WebSocket events
@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    logger.info(f"Client connected: {request.sid}")
    emit('connection_response', {'status': 'connected'})


@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    logger.info(f"Client disconnected: {request.sid}")


@socketio.on('start_monitoring')
def handle_start_monitoring():
    """Start real-time monitoring"""
    global monitoring_active, monitoring_thread
    
    if not monitoring_active:
        monitoring_active = True
        monitoring_thread = threading.Thread(target=monitoring_loop, daemon=True)
        monitoring_thread.start()
        logger.info("Real-time monitoring started")
        emit('monitoring_status', {'active': True})
    else:
        emit('monitoring_status', {'active': True, 'message': 'Already running'})


@socketio.on('stop_monitoring')
def handle_stop_monitoring():
    """Stop real-time monitoring"""
    global monitoring_active
    
    monitoring_active = False
    logger.info("Real-time monitoring stopped")
    emit('monitoring_status', {'active': False})


def shutdown_handler():
    """Cleanup on shutdown"""
    global monitoring_active
    monitoring_active = False
    gpu_monitor.shutdown()
    logger.info("Server shutting down...")


if __name__ == '__main__':
    import atexit
    atexit.register(shutdown_handler)
    
    # Auto-start monitoring
    monitoring_active = True
    monitoring_thread = threading.Thread(target=monitoring_loop, daemon=True)
    monitoring_thread.start()
    
    host = config['server']['host']
    port = config['server']['port']
    
    logger.info(f"Starting GPU Benchmark Server on {host}:{port}")
    logger.info(f"Dashboard URL: http://localhost:{port}")
    
    socketio.run(app, host=host, port=port, debug=False)
