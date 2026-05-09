"""
NVIDIA GPU Monitor and Controller
Handles GPU detection, monitoring, and fan control
"""

import pynvml
import subprocess
import threading
import time
import logging
from typing import List, Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class GPUMonitor:
    def __init__(self):
        self.initialized = False
        self.handles = []
        self.gpu_count = 0
        self._auto_fan_gpus = set()
        self._auto_fan_lock = threading.Lock()
        self._fan_curve_running = True
        self._initialize()
        # Start auto fan curve background thread
        self._fan_curve_thread = threading.Thread(target=self._fan_curve_worker, daemon=True)
        self._fan_curve_thread.start()
    
    def _initialize(self):
        """Initialize NVML library"""
        try:
            pynvml.nvmlInit()
            self.gpu_count = pynvml.nvmlDeviceGetCount()
            self.handles = [pynvml.nvmlDeviceGetHandleByIndex(i) for i in range(self.gpu_count)]
            self.initialized = True
            logger.info(f"NVML initialized successfully. Found {self.gpu_count} GPU(s)")
        except Exception as e:
            logger.error(f"Failed to initialize NVML: {e}")
            self.initialized = False
    
    def get_gpu_info(self, gpu_index: int) -> Optional[Dict]:
        """Get detailed information about a specific GPU"""
        if not self.initialized or gpu_index >= self.gpu_count:
            return None
        
        try:
            handle = self.handles[gpu_index]
            
            # Basic info
            name = pynvml.nvmlDeviceGetName(handle)
            if isinstance(name, bytes):
                name = name.decode('utf-8')
            
            # Memory info
            mem_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
            
            # Temperature
            temp = pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)
            
            # Utilization
            utilization = pynvml.nvmlDeviceGetUtilizationRates(handle)
            
            # Power
            try:
                power_usage = pynvml.nvmlDeviceGetPowerUsage(handle) / 1000.0  # Convert to watts
                power_limit = pynvml.nvmlDeviceGetPowerManagementLimit(handle) / 1000.0
            except:
                power_usage = 0
                power_limit = 0
            
            # Fan speed — try per-fan API first, fall back to legacy
            try:
                fan_speed = pynvml.nvmlDeviceGetFanSpeed_v2(handle, 0)
            except Exception:
                try:
                    fan_speed = pynvml.nvmlDeviceGetFanSpeed(handle)
                except Exception:
                    fan_speed = 0
            
            # Clock speeds
            try:
                graphics_clock = pynvml.nvmlDeviceGetClockInfo(handle, pynvml.NVML_CLOCK_GRAPHICS)
                memory_clock = pynvml.nvmlDeviceGetClockInfo(handle, pynvml.NVML_CLOCK_MEM)
            except:
                graphics_clock = 0
                memory_clock = 0
            
            return {
                "index": gpu_index,
                "name": name,
                "temperature": temp,
                "utilization": {
                    "gpu": utilization.gpu,
                    "memory": utilization.memory
                },
                "memory": {
                    "used": mem_info.used,
                    "total": mem_info.total,
                    "free": mem_info.free,
                    "used_mb": mem_info.used / (1024 ** 2),
                    "total_mb": mem_info.total / (1024 ** 2),
                    "percent": (mem_info.used / mem_info.total) * 100
                },
                "power": {
                    "usage": power_usage,
                    "limit": power_limit,
                    "percent": (power_usage / power_limit * 100) if power_limit > 0 else 0
                },
                "fan_speed": fan_speed,
                "clocks": {
                    "graphics": graphics_clock,
                    "memory": memory_clock
                },
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting GPU {gpu_index} info: {e}")
            return None
    
    def get_all_gpus_info(self) -> List[Dict]:
        """Get information about all GPUs"""
        result = []
        for i in range(self.gpu_count):
            info = self.get_gpu_info(i)
            if info:
                result.append(info)
        return result
    
    def check_gpu_error_state(self, gpu_index: int) -> Dict:
        """Query nvidia-smi to detect ERR!/GPU-requires-reset states.
        Returns {'error': False} if OK, {'error': True, 'reason': ...} if in bad state."""
        try:
            r = subprocess.run(
                ['nvidia-smi', '-i', str(gpu_index),
                 '--query-gpu=power.limit,fan.speed,ecc.errors.uncorrected.volatile.total',
                 '--format=csv,noheader'],
                capture_output=True, text=True, timeout=5
            )
            if r.returncode != 0:
                return {'error': True, 'reason': f'nvidia-smi error: {r.stderr.strip()}'}
            val = r.stdout.strip()
            if 'GPU requires reset' in val:
                return {'error': True, 'reason': 'GPU requires reset — reboot required'}
            # If all fields are N/A it's in a bad state (not just missing features)
            parts = [p.strip() for p in val.split(',')]
            if all(p in ('', '[N/A]', 'N/A') for p in parts):
                return {'error': True, 'reason': 'All power/fan sensors unavailable — GPU may be in fault state'}
            return {'error': False}
        except Exception as e:
            return {'error': True, 'reason': str(e)}

    def get_power_limit(self, gpu_index: int) -> Optional[int]:
        """Return current power limit in watts, or None on failure."""
        try:
            r = subprocess.run(
                ['nvidia-smi', '-i', str(gpu_index),
                 '--query-gpu=power.limit', '--format=csv,noheader,nounits'],
                capture_output=True, text=True, timeout=5
            )
            if r.returncode == 0:
                return int(float(r.stdout.strip()))
        except Exception as e:
            logger.warning(f"get_power_limit GPU {gpu_index}: {e}")
        return None

    def get_power_limits_range(self, gpu_index: int) -> Dict:
        """Return min/current/max power limits in watts."""
        try:
            r = subprocess.run(
                ['nvidia-smi', '-i', str(gpu_index),
                 '--query-gpu=power.min_limit,power.limit,power.max_limit',
                 '--format=csv,noheader,nounits'],
                capture_output=True, text=True, timeout=5
            )
            if r.returncode == 0:
                raw = r.stdout.strip()
                if 'GPU requires reset' in raw or '[N/A]' in raw:
                    return {'min': 0, 'current': 0, 'max': 0, 'error': 'GPU in fault state'}
                parts = [p.strip() for p in raw.split(',')]
                if len(parts) == 3:
                    try:
                        return {
                            'min': int(float(parts[0])),
                            'current': int(float(parts[1])),
                            'max': int(float(parts[2])),
                        }
                    except ValueError:
                        pass
        except Exception as e:
            logger.warning(f"get_power_limits_range GPU {gpu_index}: {e}")
        return {'min': 0, 'current': 0, 'max': 0}

    def set_power_limit(self, gpu_index: int, watts: int) -> Dict:
        """Set power limit (requires root). Returns dict with success/error."""
        # Check GPU health first — don't send commands to a GPU in fault state
        state = self.check_gpu_error_state(gpu_index)
        if state['error']:
            return {'success': False, 'error': f'GPU {gpu_index} in fault state: {state["reason"]}'}
        try:
            r = subprocess.run(
                ['nvidia-smi', '-i', str(gpu_index), '--power-limit', str(watts)],
                capture_output=True, text=True, timeout=10
            )
            if r.returncode == 0:
                logger.info(f"GPU {gpu_index}: power limit set to {watts}W")
                return {'success': True, 'gpu_index': gpu_index, 'watts': watts}
            err = r.stderr.strip() or r.stdout.strip()
            logger.warning(f"GPU {gpu_index}: nvidia-smi power-limit failed: {err}")
            return {'success': False, 'error': err}
        except Exception as e:
            logger.warning(f"set_power_limit GPU {gpu_index}: {e}")
            return {'success': False, 'error': str(e)}

    def reset_power_limit(self, gpu_index: int) -> Dict:
        """Reset power limit to card maximum."""
        limits = self.get_power_limits_range(gpu_index)
        max_w = limits.get('max', 0)
        if max_w > 0:
            return self.set_power_limit(gpu_index, max_w)
        return {'success': False, 'error': 'Could not determine max power limit'}

    def _get_num_fans(self, gpu_index: int) -> int:
        """Return the number of fans on the GPU."""
        try:
            return pynvml.nvmlDeviceGetNumFans(self.handles[gpu_index])
        except Exception:
            return 1

    def set_fan_speed(self, gpu_index: int, speed: int) -> bool:
        """Set all fans on a GPU to a fixed speed (0-100%). Requires root."""
        if not self.initialized or gpu_index >= self.gpu_count:
            return False
        try:
            handle = self.handles[gpu_index]
            speed = max(0, min(100, int(speed)))
            num_fans = self._get_num_fans(gpu_index)
            for fan_idx in range(num_fans):
                pynvml.nvmlDeviceSetFanSpeed_v2(handle, fan_idx, speed)
            logger.debug(f"GPU {gpu_index}: set {num_fans} fan(s) to {speed}%")
            return True
        except Exception as e:
            logger.warning(f"Failed to set fan speed on GPU {gpu_index}: {e}")
            return False

    def reset_fan_control(self, gpu_index: int) -> bool:
        """Reset all fans on a GPU to automatic (driver-controlled) speed."""
        if not self.initialized or gpu_index >= self.gpu_count:
            return False
        try:
            handle = self.handles[gpu_index]
            num_fans = self._get_num_fans(gpu_index)
            for fan_idx in range(num_fans):
                pynvml.nvmlDeviceSetDefaultFanSpeed_v2(handle, fan_idx)
            # Also disable auto fan curve for this GPU
            with self._auto_fan_lock:
                self._auto_fan_gpus.discard(gpu_index)
            logger.info(f"GPU {gpu_index}: reset {num_fans} fan(s) to driver auto")
            return True
        except Exception as e:
            logger.warning(f"Failed to reset fan control on GPU {gpu_index}: {e}")
            return False

    # ---- Auto fan curve ----
    def _fan_curve_speed(self, temp: int) -> int:
        """Calculate fan speed % for a given temperature.
        Below 50°C → 30%; 50°C → 55%; linear +1%/°C; capped at 100% (reached at 95°C)."""
        if temp >= 50:
            return min(100, 55 + (int(temp) - 50))
        return 30

    def _fan_curve_worker(self):
        """Background thread: every 3 s applies the fan curve for enabled GPUs."""
        while self._fan_curve_running:
            with self._auto_fan_lock:
                gpus = list(self._auto_fan_gpus)
            for gpu_idx in gpus:
                try:
                    info = self.get_gpu_info(gpu_idx)
                    if info and info.get('temperature') is not None:
                        speed = self._fan_curve_speed(info['temperature'])
                        self.set_fan_speed(gpu_idx, speed)
                except Exception as e:
                    logger.debug(f"Fan curve GPU {gpu_idx}: {e}")
            time.sleep(3)

    def enable_auto_fan_curve(self, gpu_index: int) -> bool:
        """Enable the temperature-based auto fan curve for a GPU."""
        if not self.initialized or gpu_index >= self.gpu_count:
            return False
        with self._auto_fan_lock:
            self._auto_fan_gpus.add(gpu_index)
        logger.info(f"GPU {gpu_index}: auto fan curve enabled")
        return True

    def disable_auto_fan_curve(self, gpu_index: int) -> bool:
        """Disable auto fan curve and reset fans to driver auto."""
        with self._auto_fan_lock:
            self._auto_fan_gpus.discard(gpu_index)
        return self.reset_fan_control(gpu_index)

    def get_auto_fan_status(self) -> Dict:
        """Return dict gpu_index -> bool (auto fan curve enabled)."""
        with self._auto_fan_lock:
            return {i: (i in self._auto_fan_gpus) for i in range(self.gpu_count)}
    
    def check_thermal_safety(self, gpu_index: int, max_temp: int = 100) -> Dict:
        """Check if GPU temperature is within safe limits"""
        info = self.get_gpu_info(gpu_index)
        if not info:
            return {"safe": False, "reason": "Could not read GPU info"}
        
        temp = info["temperature"]
        if temp >= max_temp:
            return {
                "safe": False,
                "reason": f"Temperature {temp}°C exceeds limit {max_temp}°C",
                "temperature": temp
            }
        
        return {"safe": True, "temperature": temp}
    
    def shutdown(self):
        """Shutdown NVML"""
        self._fan_curve_running = False
        if self.initialized:
            try:
                pynvml.nvmlShutdown()
                self.initialized = False
                logger.info("NVML shutdown successfully")
            except Exception as e:
                logger.error(f"Error shutting down NVML: {e}")
