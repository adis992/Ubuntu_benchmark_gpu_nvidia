"""
GPU Benchmark Workload Module
Handles GPU stress testing and benchmarking
"""

import subprocess
import threading
import time
import logging
import signal
import os
from typing import List, Dict, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class BenchmarkWorkload:
    def __init__(self, gpu_monitor, config):
        self.gpu_monitor = gpu_monitor
        self.config = config
        self.active_benchmarks = {}
        self.benchmark_threads = {}
        self.stop_flags = {}
        self.benchmark_results = {}
        self.crash_detector = CrashDetector()
    
    def start_benchmark(self, gpu_indices: List[int], duration: int, stress_level: int = 100) -> Dict:
        """Start benchmark on specified GPUs"""
        benchmark_id = f"bench_{int(time.time())}"
        
        if not gpu_indices:
            return {"success": False, "error": "No GPUs specified"}
        
        # Check if any GPU is already being benchmarked
        for idx in gpu_indices:
            if idx in self.active_benchmarks:
                return {"success": False, "error": f"GPU {idx} is already being benchmarked"}
        
        # Validate stress level
        stress_level = max(1, min(100, stress_level))
        
        # Initialize benchmark data
        self.active_benchmarks[benchmark_id] = {
            "gpu_indices": gpu_indices,
            "duration": duration,
            "stress_level": stress_level,
            "start_time": datetime.now(),
            "end_time": datetime.now() + timedelta(seconds=duration),
            "status": "running",
            "processes": []
        }
        
        self.stop_flags[benchmark_id] = False
        
        # Start benchmark thread
        thread = threading.Thread(
            target=self._run_benchmark,
            args=(benchmark_id, gpu_indices, duration, stress_level),
            daemon=True
        )
        thread.start()
        self.benchmark_threads[benchmark_id] = thread
        
        logger.info(f"Started benchmark {benchmark_id} on GPUs {gpu_indices} for {duration}s at {stress_level}% stress")
        
        return {
            "success": True,
            "benchmark_id": benchmark_id,
            "gpu_indices": gpu_indices,
            "duration": duration,
            "stress_level": stress_level
        }
    
    def _run_benchmark(self, benchmark_id: str, gpu_indices: List[int], duration: int, stress_level: int):
        """Run the actual benchmark workload"""
        start_time = time.time()
        processes = []
        
        try:
            # Start GPU stress process for each GPU
            for gpu_idx in gpu_indices:
                process = self._start_gpu_stress(gpu_idx, stress_level)
                if process:
                    processes.append((gpu_idx, process))
                    self.active_benchmarks[benchmark_id]["processes"].append(process)
            
            # Monitor benchmark
            while time.time() - start_time < duration and not self.stop_flags.get(benchmark_id, False):
                time.sleep(1)
                
                # Check thermal safety
                for gpu_idx in gpu_indices:
                    safety = self.gpu_monitor.check_thermal_safety(
                        gpu_idx,
                        self.config.get("safety", {}).get("max_temperature", 100)
                    )
                    
                    if not safety["safe"]:
                        logger.warning(f"Thermal safety issue on GPU {gpu_idx}: {safety['reason']}")
                        
                        # Check critical temperature
                        if safety.get("temperature", 0) >= self.config.get("safety", {}).get("critical_temperature", 105):
                            reason = f"CRITICAL TEMPERATURE: GPU {gpu_idx} reached {safety['temperature']}°C (limit: {self.config.get('safety', {}).get('critical_temperature', 105)}°C)"
                            logger.critical(reason)
                            self.crash_detector.log_critical_event(
                                reason,
                                {
                                    "benchmark_id": benchmark_id,
                                    "gpu_idx": gpu_idx,
                                    "temperature": safety['temperature'],
                                    "limit": self.config.get("safety", {}).get("critical_temperature", 105),
                                    "action": "Benchmark auto-stopped"
                                }
                            )
                            
                            # Always stop benchmark on critical temperature
                            if self.config.get("safety", {}).get("auto_stop_benchmark_on_critical", True):
                                logger.warning(f"Auto-stopping benchmark {benchmark_id} due to critical temperature on GPU {gpu_idx}")
                                self.stop_flags[benchmark_id] = True
                                if benchmark_id in self.active_benchmarks:
                                    self.active_benchmarks[benchmark_id]["status"] = "stopped_critical_temp"
                                    self.active_benchmarks[benchmark_id]["stop_reason"] = reason
                                break
                
                # Check if processes are still running
                for gpu_idx, proc in processes:
                    if proc.poll() is not None:
                        logger.warning(f"Benchmark process for GPU {gpu_idx} terminated unexpectedly")
            
            # Stop all processes
            for gpu_idx, proc in processes:
                try:
                    proc.terminate()
                    proc.wait(timeout=5)
                except:
                    proc.kill()
            
            # Update status
            if benchmark_id in self.active_benchmarks:
                # Only mark as completed if it wasn't already marked as stopped_critical_temp
                if self.active_benchmarks[benchmark_id]["status"] != "stopped_critical_temp":
                    self.active_benchmarks[benchmark_id]["status"] = "completed"
                self.active_benchmarks[benchmark_id]["actual_duration"] = time.time() - start_time
                
                # Store results
                self.benchmark_results[benchmark_id] = self.active_benchmarks[benchmark_id].copy()
                del self.active_benchmarks[benchmark_id]
            
            logger.info(f"Benchmark {benchmark_id} completed")
        
        except Exception as e:
            logger.error(f"Error in benchmark {benchmark_id}: {e}")
            self.crash_detector.log_error(f"Benchmark error: {e}", {"benchmark_id": benchmark_id})
            
            if benchmark_id in self.active_benchmarks:
                self.active_benchmarks[benchmark_id]["status"] = "error"
                self.active_benchmarks[benchmark_id]["error"] = str(e)
    
    def _start_gpu_stress(self, gpu_idx: int, stress_level: int) -> Optional[subprocess.Popen]:
        """Start GPU stress test process"""
        try:
            # Use nvidia-smi to create GPU load
            # This is a simple approach - for production, use CUDA kernels
            stress_script = f"""
import time
import numpy as np
try:
    import cupy as cp
    # CuPy stress test
    size = int(8192 * ({stress_level}/100))
    while True:
        a = cp.random.random((size, size), dtype=cp.float32)
        b = cp.random.random((size, size), dtype=cp.float32)
        c = cp.matmul(a, b)
        cp.cuda.Stream.null.synchronize()
        time.sleep(0.001)
except ImportError:
    # Fallback: use nvidia-smi to create some load
    import subprocess
    while True:
        subprocess.run(['nvidia-smi', '-i', str({gpu_idx}), '-q'], capture_output=True)
        time.sleep(0.1)
"""
            
            # Write stress script to temp file
            script_path = f"/tmp/gpu_stress_{gpu_idx}_{int(time.time())}.py"
            with open(script_path, 'w') as f:
                f.write(stress_script)
            
            # Set CUDA_VISIBLE_DEVICES to target specific GPU
            env = os.environ.copy()
            env['CUDA_VISIBLE_DEVICES'] = str(gpu_idx)
            
            # Start process
            process = subprocess.Popen(
                ['python3', script_path],
                env=env,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
            logger.info(f"Started GPU stress process for GPU {gpu_idx} (PID: {process.pid})")
            return process
        
        except Exception as e:
            logger.error(f"Failed to start GPU stress for GPU {gpu_idx}: {e}")
            return None
    
    def stop_benchmark(self, benchmark_id: str) -> Dict:
        """Stop a running benchmark"""
        if benchmark_id not in self.active_benchmarks:
            return {"success": False, "error": "Benchmark not found or already stopped"}
        
        self.stop_flags[benchmark_id] = True
        logger.info(f"Stopping benchmark {benchmark_id}")
        
        return {"success": True, "benchmark_id": benchmark_id}
    
    def get_active_benchmarks(self) -> Dict:
        """Get all active benchmarks"""
        return {k: {
            "gpu_indices": v["gpu_indices"],
            "duration": v["duration"],
            "stress_level": v["stress_level"],
            "start_time": v["start_time"].isoformat(),
            "end_time": v["end_time"].isoformat(),
            "status": v["status"],
            "elapsed": (datetime.now() - v["start_time"]).total_seconds(),
            "stop_reason": v.get("stop_reason", "")
        } for k, v in self.active_benchmarks.items()}
    
    def get_benchmark_results(self) -> Dict:
        """Get completed benchmark results"""
        return self.benchmark_results


class CrashDetector:
    """Handles crash detection and logging before system failures"""
    
    def __init__(self):
        self.log_file = "logs/crash_detection.log"
        self._ensure_log_dir()
        self._setup_signal_handlers()
    
    def _ensure_log_dir(self):
        """Ensure log directory exists"""
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
    
    def _setup_signal_handlers(self):
        """Setup signal handlers to catch crashes"""
        def signal_handler(signum, frame):
            self.log_critical_event(
                f"Received signal {signum}",
                {"signal": signum, "frame": str(frame)}
            )
        
        try:
            signal.signal(signal.SIGTERM, signal_handler)
            signal.signal(signal.SIGINT, signal_handler)
        except Exception as e:
            logger.warning(f"Could not setup signal handlers: {e}")
    
    def log_error(self, message: str, context: Dict = None):
        """Log an error event"""
        self._write_log("ERROR", message, context)
    
    def log_critical_event(self, message: str, context: Dict = None):
        """Log a critical event that might lead to crash"""
        self._write_log("CRITICAL", message, context)
        logger.critical(f"CRITICAL EVENT: {message}")
    
    def _write_log(self, level: str, message: str, context: Dict = None):
        """Write to crash detection log"""
        try:
            with open(self.log_file, 'a') as f:
                timestamp = datetime.now().isoformat()
                log_entry = f"[{timestamp}] {level}: {message}"
                if context:
                    log_entry += f" | Context: {context}"
                log_entry += "\n"
                f.write(log_entry)
                f.flush()
                os.fsync(f.fileno())  # Force write to disk
        except Exception as e:
            logger.error(f"Failed to write crash log: {e}")
