"""
Performance & Correctness Metrics Calculator
Computes speedup factor, floating-point equivalence (epsilon check), and throughput.
"""

import math
import re
from typing import Tuple


def calculate_speedup(python_ms: float, cpp_ms: float) -> float:
    """Computes speedup ratio python_ms / cpp_ms safely."""
    if cpp_ms <= 0:
        return 1.0
    return round(max(python_ms / cpp_ms, 0.01), 2)


def check_outputs_match(py_stdout: str, cpp_stdout: str, tolerance: float = 1e-4) -> bool:
    """
    Compares Python and C++ output streams for numerical and semantic equivalence.
    Supports exact string match or floating-point comparison with epsilon tolerance.
    """
    py_clean = py_stdout.strip()
    cpp_clean = cpp_stdout.strip()

    if not py_clean or not cpp_clean:
        return False

    # 1. Exact string match
    if py_clean == cpp_clean:
        return True

    # 2. Extract numbers from both outputs and compare numerically
    py_numbers = [float(x) for x in re.findall(r"[-+]?(?:\d*\.\d+|\d+)(?:[eE][-+]?\d+)?", py_clean)]
    cpp_numbers = [float(x) for x in re.findall(r"[-+]?(?:\d*\.\d+|\d+)(?:[eE][-+]?\d+)?", cpp_clean)]

    if py_numbers and len(py_numbers) == len(cpp_numbers):
        all_close = True
        for p, c in zip(py_numbers, cpp_numbers):
            if not math.isclose(p, c, rel_tol=tolerance, abs_tol=tolerance):
                all_close = False
                break
        if all_close:
            return True

    # 3. Line by line comparison
    py_lines = [line.strip() for line in py_clean.splitlines() if line.strip()]
    cpp_lines = [line.strip() for line in cpp_clean.splitlines() if line.strip()]

    # Filter out timing lines like "Elapsed time: ..." from comparison
    py_filtered = [l for l in py_lines if not any(kw in l.lower() for kw in ["elapsed", "time:", "ms", "took"])]
    cpp_filtered = [l for l in cpp_lines if not any(kw in l.lower() for kw in ["elapsed", "time:", "ms", "took"])]

    if py_filtered and py_filtered == cpp_filtered:
        return True

    return False
