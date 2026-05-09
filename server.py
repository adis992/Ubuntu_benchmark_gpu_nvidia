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
import sys
import platform
import subprocess
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

# Return JSON for all errors instead of HTML (prevents "unexpected character" in frontend)
@app.errorhandler(Exception)
def handle_exception(e):
    logger.error(f"Unhandled exception: {e}", exc_info=True)
    return jsonify({'error': str(e)}), 500

@app.errorhandler(404)
def handle_404(e):
    return jsonify({'error': 'Not found'}), 404

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
    workload_type = data.get('workload_type', 'mixed')
    precision = data.get('precision', 'fp32')
    memory_level = data.get('memory_level', 50)
    power_limit = data.get('power_limit', None)
    
    # Validate duration
    max_duration = config['benchmark']['max_duration']
    if duration > max_duration:
        return jsonify({'error': f'Duration exceeds maximum of {max_duration} seconds'}), 400
    
    # Validate power_limit
    if power_limit is not None:
        try:
            power_limit = int(power_limit)
            if power_limit < 50 or power_limit > 600:
                return jsonify({'error': 'power_limit must be between 50 and 600 watts'}), 400
        except (TypeError, ValueError):
            return jsonify({'error': 'power_limit must be an integer'}), 400
    
    result = benchmark_workload.start_benchmark(
        gpu_indices, duration, stress_level,
        workload_type=workload_type, precision=precision,
        memory_level=memory_level, power_limit=power_limit
    )
    
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
    """Get completed benchmark results with metrics history (JSON-safe)"""
    raw = benchmark_workload.get_benchmark_results()
    results = {}
    for bid, r in raw.items():
        safe = {}
        for k, v in r.items():
            if k == 'processes':
                continue
            if hasattr(v, 'isoformat'):
                safe[k] = v.isoformat()
            elif isinstance(v, list):
                safe[k] = v
            else:
                safe[k] = v
        results[bid] = safe
    return jsonify(results)


@app.route('/api/power/limits')
def api_power_limits():
    """Get power limit range (min/current/max) for all GPUs"""
    limits = {}
    for i in range(gpu_monitor.gpu_count):
        limits[i] = gpu_monitor.get_power_limits_range(i)
    return jsonify(limits)


@app.route('/api/power/set', methods=['POST'])
def api_power_set():
    """Set power limit for a GPU (requires root)"""
    data = request.json
    gpu_id = data.get('gpu_id')
    watts = data.get('watts')
    if gpu_id is None or watts is None:
        return jsonify({'error': 'gpu_id and watts are required'}), 400
    try:
        watts = int(watts)
        gpu_id = int(gpu_id)
    except (TypeError, ValueError):
        return jsonify({'error': 'gpu_id and watts must be integers'}), 400
    if watts < 50 or watts > 600:
        return jsonify({'error': 'watts must be between 50 and 600'}), 400
    result = gpu_monitor.set_power_limit(gpu_id, watts)
    if result['success']:
        return jsonify(result)
    return jsonify(result), 500


@app.route('/api/power/reset', methods=['POST'])
def api_power_reset():
    """Reset power limit to card maximum"""
    data = request.json
    gpu_id = data.get('gpu_id')
    if gpu_id is None:
        return jsonify({'error': 'gpu_id is required'}), 400
    result = gpu_monitor.reset_power_limit(int(gpu_id))
    if result['success']:
        return jsonify(result)
    return jsonify(result), 500


@app.route('/api/fan/auto', methods=['GET'])
def api_fan_auto_get():
    """Get auto fan curve status for all GPUs"""
    return jsonify(gpu_monitor.get_auto_fan_status())


@app.route('/api/fan/auto', methods=['POST'])
def api_fan_auto_set():
    """Enable or disable the auto fan curve for a GPU"""
    data = request.json
    gpu_id = data.get('gpu_id')
    enabled = data.get('enabled', True)
    if gpu_id is None:
        return jsonify({'error': 'gpu_id is required'}), 400
    gpu_id = int(gpu_id)
    if enabled:
        ok = gpu_monitor.enable_auto_fan_curve(gpu_id)
    else:
        ok = gpu_monitor.disable_auto_fan_curve(gpu_id)
    return jsonify({'success': ok, 'gpu_id': gpu_id, 'auto_fan': enabled})


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
    allowed_keys = ['benchmark', 'monitoring', 'safety']
    for key in allowed_keys:
        if key in data:
            config[key].update(data[key])
    try:
        with open('config.json', 'w') as f:
            json.dump(config, f, indent=2)
        return jsonify({'success': True, 'config': config})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


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


@app.route('/api/system/info')
def api_system_info():
    """Get system information: driver, CUDA, Python, CuPy"""
    info = {
        'os': platform.platform(),
        'hostname': platform.node(),
        'python': sys.version.split()[0],
        'driver_version': 'N/A',
        'cuda_version': 'N/A',
        'cupy_version': 'N/A',
        'cupy_installed': False,
        'nvml_version': 'N/A',
        'gpu_count': gpu_monitor.gpu_count,
    }
    try:
        result = subprocess.run(
            ['nvidia-smi', '--query-gpu=driver_version', '--format=csv,noheader'],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            info['driver_version'] = result.stdout.strip().split('\n')[0]
    except Exception:
        pass
    try:
        result = subprocess.run(
            ['nvidia-smi', '--query-gpu=name,memory.total,compute_cap',
             '--format=csv,noheader,nounits'],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            gpus = []
            for line in result.stdout.strip().split('\n'):
                parts = [p.strip() for p in line.split(',')]
                if len(parts) >= 3:
                    gpus.append({'name': parts[0], 'vram_mb': parts[1], 'compute_cap': parts[2]})
            info['gpu_list'] = gpus
    except Exception:
        pass
    try:
        result = subprocess.run(
            ['nvidia-smi'], capture_output=True, text=True, timeout=5
        )
        import re
        match = re.search(r'CUDA Version:\s*([0-9.]+)', result.stdout)
        if match:
            info['cuda_version'] = match.group(1)
    except Exception:
        pass
    try:
        import cupy
        info['cupy_version'] = cupy.__version__
        info['cupy_installed'] = True
    except ImportError:
        info['cupy_installed'] = False
    try:
        from pynvml import nvmlSystemGetDriverVersion
        info['nvml_version'] = nvmlSystemGetDriverVersion().decode()
    except Exception:
        pass
    return jsonify(info)


@app.route('/api/system/health')
def api_system_health():
    """Run GPU health check"""
    results = []
    for i in range(gpu_monitor.gpu_count):
        gpu_result = {'gpu_index': i, 'checks': [], 'status': 'ok'}
        try:
            # First check for hardware fault / ERR! state via nvidia-smi
            err_state = gpu_monitor.check_gpu_error_state(i)
            if err_state['error']:
                gpu_result['status'] = 'error'
                gpu_result['error'] = err_state['reason']
                gpu_result['checks'].append({'name': 'GPU fault state (nvidia-smi)', 'ok': False})
                # Try to get name and temp even in bad state
                try:
                    info = gpu_monitor.get_gpu_info(i)
                    if info:
                        gpu_result['name'] = info.get('name', f'GPU {i}')
                        gpu_result['checks'].append({'name': f'Temperature: {info["temperature"]}°C', 'ok': True})
                        gpu_result['checks'].append({'name': f'Memory: {info["memory"]["used_mb"]:.0f} / {info["memory"]["total_mb"]:.0f} MB', 'ok': True})
                except Exception:
                    pass
                results.append(gpu_result)
                continue

            info = gpu_monitor.get_gpu_info(i)
            if info:
                # Check ECC uncorrected errors via nvidia-smi
                ecc_errors = 0
                try:
                    r = subprocess.run(
                        ['nvidia-smi', '-i', str(i),
                         '--query-gpu=ecc.errors.uncorrected.volatile.total',
                         '--format=csv,noheader,nounits'],
                        capture_output=True, text=True, timeout=5
                    )
                    if r.returncode == 0:
                        val = r.stdout.strip()
                        if val not in ('', 'N/A', '[N/A]'):
                            ecc_errors = int(val)
                except Exception:
                    pass

                limits = gpu_monitor.get_power_limits_range(i)

                checks = [
                    ('Temperature readable', info['temperature'] is not None),
                    ('Utilization readable', info['utilization']['gpu'] is not None),
                    ('Memory readable', info['memory']['used_mb'] is not None),
                    ('Power readable', info['power']['usage'] is not None),
                    ('Clock readable', info['clocks']['graphics'] is not None),
                    ('Temperature sane', 0 < info['temperature'] < 120),
                    ('Memory sane', info['memory']['used_mb'] >= 0),
                    ('No uncorrected ECC errors', ecc_errors == 0),
                    ('Power limit readable', limits.get('max', 0) > 0),
                ]
                for name, ok in checks:
                    gpu_result['checks'].append({'name': name, 'ok': ok})
                    if not ok:
                        gpu_result['status'] = 'warning'

                # Add informational lines
                gpu_result['checks'].append({
                    'name': f'Power: {info["power"]["usage"]:.1f} W / {limits.get("current", 0)} W (max {limits.get("max", 0)} W)',
                    'ok': True
                })
                if ecc_errors > 0:
                    gpu_result['checks'].append({'name': f'⚠️ ECC uncorrected errors: {ecc_errors}', 'ok': False})
                    gpu_result['status'] = 'warning'

                gpu_result['name'] = info.get('name', f'GPU {i}')
            else:
                gpu_result['status'] = 'error'
                gpu_result['error'] = 'Could not read GPU info'
        except Exception as e:
            gpu_result['status'] = 'error'
            gpu_result['error'] = str(e)
        results.append(gpu_result)
    cupy_ok = False
    try:
        import cupy
        cupy_ok = True
    except ImportError:
        pass
    return jsonify({'gpus': results, 'cupy_installed': cupy_ok, 'timestamp': datetime.now().isoformat()})


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
    
    socketio.run(app, host=host, port=port, debug=False, allow_unsafe_werkzeug=True)
