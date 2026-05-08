"""
Enhanced GPU Stress Test Script
Uses various techniques to stress test NVIDIA GPUs
"""

import argparse
import sys
import time
import signal
from datetime import datetime

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False
    print("Warning: NumPy not available")

try:
    import cupy as cp
    HAS_CUPY = True
except ImportError:
    HAS_CUPY = False
    print("Warning: CuPy not available, using fallback methods")


class GPUStressTester:
    def __init__(self, gpu_id, stress_level=100):
        self.gpu_id = gpu_id
        self.stress_level = max(1, min(100, stress_level))
        self.running = True
        self.operations = 0
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
    def signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Shutting down gracefully...")
        self.running = False
        
    def run_cupy_stress(self):
        """Run CuPy-based GPU stress test"""
        print(f"Using CuPy for GPU {self.gpu_id}")
        
        # Set the target GPU
        with cp.cuda.Device(self.gpu_id):
            # Calculate matrix size based on stress level
            base_size = 4096
            size = int(base_size * (self.stress_level / 100))
            
            print(f"Matrix size: {size}x{size}")
            print(f"Stress level: {self.stress_level}%")
            print(f"Memory per matrix: ~{(size * size * 4 / 1024 / 1024):.1f} MB")
            print("\nStarting stress test... Press Ctrl+C to stop\n")
            
            start_time = time.time()
            
            # PRE-ALLOCATE matrices once to avoid repeated OOM crashes
            try:
                a = cp.random.random((size, size), dtype=cp.float32)
                b = cp.random.random((size, size), dtype=cp.float32)
                c = cp.zeros((size, size), dtype=cp.float32)
            except cp.cuda.memory.OutOfMemoryError:
                size = max(512, size // 2)
                print(f"OOM: reduced matrix size to {size}x{size}")
                a = cp.random.random((size, size), dtype=cp.float32)
                b = cp.random.random((size, size), dtype=cp.float32)
                c = cp.zeros((size, size), dtype=cp.float32)

            while self.running:
                try:
                    # In-place matrix multiply (no new allocations)
                    cp.matmul(a, b, out=c)
                    
                    # Element-wise operations (in-place)
                    cp.sqrt(c, out=c)
                    
                    # Reduction
                    result = float(cp.sum(c))
                    
                    # Synchronize to ensure operations complete
                    cp.cuda.Stream.null.synchronize()
                    
                    self.operations += 1
                    
                    # Progress update every 10 operations
                    if self.operations % 10 == 0:
                        elapsed = time.time() - start_time
                        ops_per_sec = self.operations / elapsed
                        print(f"[{datetime.now().strftime('%H:%M:%S')}] "
                              f"Operations: {self.operations} | "
                              f"Rate: {ops_per_sec:.2f} ops/sec | "
                              f"Elapsed: {elapsed:.1f}s")
                    
                    # Small delay based on stress level
                    time.sleep((100 - self.stress_level) / 10000)
                    
                except Exception as e:
                    print(f"Error during stress test: {e}")
                    break
            
            # Cleanup
            cp.get_default_memory_pool().free_all_blocks()
            
    def run_fallback_stress(self):
        """Fallback stress test using nvidia-smi"""
        print(f"Using fallback method for GPU {self.gpu_id}")
        print("Note: This method provides minimal stress. Install CuPy for better results.")
        print("\nStarting stress test... Press Ctrl+C to stop\n")
        
        import subprocess
        import os
        
        start_time = time.time()
        
        # Set CUDA_VISIBLE_DEVICES
        env = os.environ.copy()
        env['CUDA_VISIBLE_DEVICES'] = str(self.gpu_id)
        
        while self.running:
            try:
                # Query GPU repeatedly
                subprocess.run(
                    ['nvidia-smi', '-i', str(self.gpu_id), '-q'],
                    capture_output=True,
                    timeout=1
                )
                
                self.operations += 1
                
                if self.operations % 100 == 0:
                    elapsed = time.time() - start_time
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] "
                          f"Queries: {self.operations} | "
                          f"Elapsed: {elapsed:.1f}s")
                
                time.sleep(0.01)
                
            except Exception as e:
                print(f"Error: {e}")
                break
    
    def run(self):
        """Run the stress test"""
        print(f"\n{'='*60}")
        print(f"GPU Stress Test")
        print(f"{'='*60}")
        print(f"GPU ID: {self.gpu_id}")
        print(f"Stress Level: {self.stress_level}%")
        print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}\n")
        
        if HAS_CUPY:
            self.run_cupy_stress()
        else:
            self.run_fallback_stress()
        
        print(f"\n{'='*60}")
        print(f"Stress Test Completed")
        print(f"Total Operations: {self.operations}")
        print(f"End Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}\n")


def main():
    parser = argparse.ArgumentParser(
        description='NVIDIA GPU Stress Test Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s -g 0 -s 100          # Stress GPU 0 at 100%%
  %(prog)s -g 1 -s 50           # Stress GPU 1 at 50%%
  %(prog)s --gpu 0 --stress 75  # Stress GPU 0 at 75%%
        """
    )
    
    parser.add_argument(
        '-g', '--gpu',
        type=int,
        required=True,
        help='GPU index to stress test (0, 1, 2, ...)'
    )
    
    parser.add_argument(
        '-s', '--stress',
        type=int,
        default=100,
        help='Stress level percentage (1-100, default: 100)'
    )
    
    args = parser.parse_args()
    
    # Validate GPU index
    try:
        import subprocess
        result = subprocess.run(
            ['nvidia-smi', '--query-gpu=index', '--format=csv,noheader'],
            capture_output=True,
            text=True,
            check=True
        )
        available_gpus = [int(idx.strip()) for idx in result.stdout.strip().split('\n') if idx.strip()]
        
        if args.gpu not in available_gpus:
            print(f"Error: GPU {args.gpu} not found")
            print(f"Available GPUs: {available_gpus}")
            sys.exit(1)
            
    except Exception as e:
        print(f"Error checking GPUs: {e}")
        sys.exit(1)
    
    # Run stress test
    tester = GPUStressTester(args.gpu, args.stress)
    tester.run()


if __name__ == '__main__':
    main()
