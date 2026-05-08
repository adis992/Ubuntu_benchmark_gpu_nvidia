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


class _StressWorker:
    """Runs GPU stress directly in a daemon thread. Mimics subprocess.Popen interface."""

    def __init__(self, gpu_idx, stress_level, workload_type, np_dtype, compute_size, memory_mb):
        self.gpu_idx      = gpu_idx
        self.stress_level = stress_level
        self.workload_type = workload_type
        self.np_dtype     = np_dtype
        self.compute_size = compute_size
        self.memory_mb    = memory_mb
        self._stop        = False
        self._thread      = None
        self.returncode   = None

    def start(self):
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self):
        try:
            import cupy as cp
            cp.cuda.Device(self.gpu_idx).use()
            logger.info(f"GPU {self.gpu_idx} stress thread active, "
                        f"size={self.compute_size}, type={self.workload_type}")
            if self.workload_type == 'compute':
                self._compute(cp)
            elif self.workload_type == 'memory':
                self._memory(cp)
            else:
                mem_t = threading.Thread(
                    target=self._memory, args=(cp,), daemon=True)
                mem_t.start()
                self._compute(cp)
        except Exception as e:
            logger.error(f"GPU {self.gpu_idx} stress error: {e}")
        finally:
            self.returncode = 0

    def _compute(self, cp):
        size  = self.compute_size
        dtype = getattr(cp, self.np_dtype)
        try:
            a = cp.random.random((size, size), dtype=dtype)
            b = cp.random.random((size, size), dtype=dtype)
            c = cp.zeros((size, size), dtype=dtype)
        except cp.cuda.memory.OutOfMemoryError:
            size = max(512, size // 2)
            a = cp.random.random((size, size), dtype=dtype)
            b = cp.random.random((size, size), dtype=dtype)
            c = cp.zeros((size, size), dtype=dtype)
        it = 0
        delay = max(0.0, (100 - self.stress_level) / 2000.0)
        while not self._stop:
            try:
                cp.matmul(a, b, out=c)
                cp.sqrt(c, out=c)
                cp.sin(c, out=c)
                cp.cuda.Stream.null.synchronize()
                it += 1
                if it % 100 == 0:
                    cp.random.random((size, size), out=a)
                if delay > 0:
                    time.sleep(delay)
            except cp.cuda.memory.OutOfMemoryError:
                size = max(512, size // 2)
                a = cp.random.random((size, size), dtype=dtype)
                b = cp.random.random((size, size), dtype=dtype)
                c = cp.zeros((size, size), dtype=dtype)
                time.sleep(0.5)
            except Exception:
                time.sleep(0.1)

    def _memory(self, cp):
        n = min(self.memory_mb * 1024 * 1024 // 4, 256 * 1024 * 1024)
        try:
            buf = cp.zeros(n, dtype=cp.float32)
            while not self._stop:
                try:
                    cp.random.random(n, out=buf)
                    _ = cp.sum(buf)
                    cp.cuda.Stream.null.synchronize()
                    time.sleep(0.002)
                except Exception:
                    time.sleep(0.1)
        except Exception:
            time.sleep(0.5)

    # subprocess.Popen-compatible interface
    def poll(self):
        if self._thread and not self._thread.is_alive():
            if self.returncode is None:
                self.returncode = 0
        return self.returncode

    def terminate(self):
        self._stop = True

    def kill(self):
        self._stop = True

    def wait(self, timeout=None):
        if self._thread:
            self._thread.join(timeout=timeout)


class BenchmarkWorkload:
    def __init__(self, gpu_monitor, config):
        self.gpu_monitor = gpu_monitor
        self.config = config
        self.active_benchmarks = {}
        self.benchmark_threads = {}
        self.stop_flags = {}
        self.benchmark_results = {}
        self.crash_detector = CrashDetector()
    
    def start_benchmark(self, gpu_indices: List[int], duration: int,
                        stress_level: int = 100, workload_type: str = 'mixed',
                        precision: str = 'fp32', memory_level: int = 50) -> Dict:
        """Start benchmark on specified GPUs"""
        benchmark_id = f"bench_{int(time.time())}"
        
        if not gpu_indices:
            return {"success": False, "error": "No GPUs specified"}
        
        # Check if any GPU is already being benchmarked
        for idx in gpu_indices:
            if idx in self.active_benchmarks:
                return {"success": False, "error": f"GPU {idx} is already being benchmarked"}
        
        # Validate inputs
        stress_level = max(1, min(100, stress_level))
        memory_level = max(0, min(100, memory_level))
        
        # Initialize benchmark data
        self.active_benchmarks[benchmark_id] = {
            "gpu_indices": gpu_indices,
            "duration": duration,
            "stress_level": stress_level,
            "workload_type": workload_type,
            "precision": precision,
            "memory_level": memory_level,
            "start_time": datetime.now(),
            "end_time": datetime.now() + timedelta(seconds=duration),
            "status": "running",
            "processes": []
        }
        
        self.stop_flags[benchmark_id] = False
        
        # Start benchmark thread
        thread = threading.Thread(
            target=self._run_benchmark,
            args=(benchmark_id, gpu_indices, duration, stress_level, workload_type, precision, memory_level),
            daemon=True
        )
        thread.start()
        self.benchmark_threads[benchmark_id] = thread
        
        logger.info(f"Started benchmark {benchmark_id} on GPUs {gpu_indices} for {duration}s "
                    f"at {stress_level}% stress, type={workload_type}, precision={precision}")
        
        return {
            "success": True,
            "benchmark_id": benchmark_id,
            "gpu_indices": gpu_indices,
            "duration": duration,
            "stress_level": stress_level,
            "workload_type": workload_type,
            "precision": precision
        }
    
    def _run_benchmark(self, benchmark_id: str, gpu_indices: List[int], duration: int,
                       stress_level: int, workload_type: str = 'mixed',
                       precision: str = 'fp32', memory_level: int = 50):
        """Run the actual benchmark workload"""
        start_time = time.time()
        processes = []
        
        try:
            # Start GPU stress process for each GPU
            for gpu_idx in gpu_indices:
                process = self._start_gpu_stress(gpu_idx, stress_level, workload_type, precision, memory_level)
                if process:
                    processes.append((gpu_idx, process))
                    self.active_benchmarks[benchmark_id]["processes"].append(process)
            
            # Initialize metrics history
            self.active_benchmarks[benchmark_id]["metrics_history"] = []
            self.active_benchmarks[benchmark_id]["metrics_labels"] = []

            # Monitor benchmark
            while time.time() - start_time < duration and not self.stop_flags.get(benchmark_id, False):
                time.sleep(1)
                elapsed_sec = time.time() - start_time

                # Record per-GPU metrics snapshot
                snapshot = {"ts": round(elapsed_sec, 1), "gpus": []}
                for gpu_idx in gpu_indices:
                    try:
                        info = self.gpu_monitor.get_gpu_info(gpu_idx)
                        snapshot["gpus"].append({
                            "gpu": gpu_idx,
                            "temp": info.get("temperature", 0),
                            "util": info.get("utilization", {}).get("gpu", 0),
                            "power": round(info.get("power", {}).get("usage", 0), 1),
                            "fan": info.get("fan_speed", 0),
                            "mem_pct": round(info.get("memory", {}).get("percent", 0), 1),
                            "clock": info.get("clocks", {}).get("graphics", 0),
                        })
                    except Exception:
                        pass
                if snapshot["gpus"]:
                    self.active_benchmarks[benchmark_id]["metrics_history"].append(snapshot)

                # Check thermal safety
                for gpu_idx in gpu_indices:
                    try:
                        safety = self.gpu_monitor.check_thermal_safety(
                            gpu_idx,
                            self.config.get("safety", {}).get("max_temperature", 100)
                        )
                    except Exception as e:
                        logger.error(f"Error checking thermal safety for GPU {gpu_idx}: {e}")
                        continue
                    
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
    
    def _start_gpu_stress(self, gpu_idx: int, stress_level: int,
                          workload_type: str = 'mixed', precision: str = 'fp32',
                          memory_level: int = 50):
        """Start GPU stress directly in a thread (no subprocess, no env issues)"""
        try:
            compute_size = int(1024 + (3072 * stress_level / 100))
            memory_mb   = int(100  + (900  * memory_level  / 100))
            dtype_map   = {'fp16': 'float16'}
            np_dtype    = dtype_map.get(precision, 'float32')

            worker = _StressWorker(gpu_idx, stress_level, workload_type, np_dtype,
                                   compute_size, memory_mb)
            worker.start()
            logger.info(f"Started GPU stress thread for GPU {gpu_idx} "
                        f"(size={compute_size}, mem={memory_mb}MB, type={workload_type})")
            return worker

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
