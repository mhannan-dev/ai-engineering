"""
Monte Carlo Simulation Benchmark
Estimates Pi using random sampling and validates convergence.
"""

import math
import random
import time

def estimate_pi(num_samples: int = 5_000_000):
    start = time.perf_counter()

    inside_circle = 0
    # Deterministic linear congruential generator for reproducibility
    seed = 42
    for _ in range(num_samples):
        seed = (seed * 1103515245 + 12345) & 0x7FFFFFFF
        x = seed / 0x7FFFFFFF
        seed = (seed * 1103515245 + 12345) & 0x7FFFFFFF
        y = seed / 0x7FFFFFFF

        if x * x + y * y <= 1.0:
            inside_circle += 1

    pi_estimate = 4.0 * inside_circle / num_samples
    elapsed = (time.perf_counter() - start) * 1000.0

    print(f"Samples: {num_samples}")
    print(f"Pi Estimate: {pi_estimate:.6f}")
    print(f"Error: {abs(pi_estimate - math.pi):.6f}")
    print(f"Elapsed Time: {elapsed:.2f} ms")

if __name__ == "__main__":
    estimate_pi(5_000_000)
