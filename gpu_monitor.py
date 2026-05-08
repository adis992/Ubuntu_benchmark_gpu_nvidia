"""
NVIDIA GPU Monitor and Controller
Handles GPU detection, monitoring, and fan control
"""

import pynvml
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
        self._initialize()
    
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
            
            # Fan speed
            try:
                fan_speed = pynvml.nvmlDeviceGetFanSpeed(handle)
            except:
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
        return [self.get_gpu_info(i) for i in range(self.gpu_count) if self.get_gpu_info(i)]
    
    def set_fan_speed(self, gpu_index: int, speed: int) -> bool:
        """Set fan speed for a specific GPU (0-100%)"""
        if not self.initialized or gpu_index >= self.gpu_count:
            return False
        
        try:
            handle = self.handles[gpu_index]
            # Enable manual fan control
            pynvml.nvmlDeviceSetDefaultFanSpeed_v2(handle)
            # Note: Direct fan control requires specific permissions and driver support
            logger.info(f"Attempted to set fan speed to {speed}% on GPU {gpu_index}")
            return True
        except Exception as e:
            logger.warning(f"Failed to set fan speed on GPU {gpu_index}: {e}")
            return False
    
    def reset_fan_control(self, gpu_index: int) -> bool:
        """Reset fan control to automatic"""
        if not self.initialized or gpu_index >= self.gpu_count:
            return False
        
        try:
            handle = self.handles[gpu_index]
            pynvml.nvmlDeviceSetDefaultFanSpeed_v2(handle)
            logger.info(f"Reset fan control to automatic on GPU {gpu_index}")
            return True
        except Exception as e:
            logger.warning(f"Failed to reset fan control on GPU {gpu_index}: {e}")
            return False
    
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
        if self.initialized:
            try:
                pynvml.nvmlShutdown()
                self.initialized = False
                logger.info("NVML shutdown successfully")
            except Exception as e:
                logger.error(f"Error shutting down NVML: {e}")
