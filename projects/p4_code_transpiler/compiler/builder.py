"""
C++ Builder Subsystem
Invokes g++ compiler with specified flags, capturing diagnostics, warnings, and errors.
"""

import subprocess
import uuid
from pathlib import Path
from typing import Tuple, Optional
from config.settings import settings


def compile_cpp(
    cpp_source: str,
    source_id: Optional[str] = None,
    opt_level: str = "O3",
    enable_openmp: bool = True,
    timeout_seconds: int = 30,
) -> Tuple[bool, Optional[Path], str]:
    """
    Compiles C++20 source code using g++.

    Args:
        cpp_source: Complete C++ source code text.
        source_id: Optional unique identifier for filenames.
        opt_level: Optimization flag (O0, O1, O2, O3).
        enable_openmp: Whether to pass -fopenmp flag.
        timeout_seconds: Compilation timeout.

    Returns:
        Tuple of (success: bool, binary_path: Optional[Path], compiler_errors: str)
    """
    if not source_id:
        source_id = f"src_{uuid.uuid4().hex[:8]}"

    cpp_path = settings.temp_cpp_dir / f"{source_id}.cpp"
    binary_path = settings.binaries_dir / f"{source_id}.exe"

    # Write source file
    cpp_path.write_text(cpp_source, encoding="utf-8")

    # Clean previous binary if exists
    if binary_path.exists():
        try:
            binary_path.unlink()
        except OSError:
            pass

    # Build g++ command
    cmd = [
        settings.cxx_compiler,
        "-std=c++20",
        f"-{opt_level.upper() if not opt_level.startswith('O') else opt_level}",
    ]

    if enable_openmp and settings.enable_openmp:
        cmd.append("-fopenmp")

    cmd.extend([
        str(cpp_path),
        "-o",
        str(binary_path),
    ])

    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            encoding="utf-8",
            errors="replace",
        )

        stderr = proc.stderr or ""
        stdout = proc.stdout or ""
        combined_output = f"{stdout}\n{stderr}".strip()

        if proc.returncode == 0 and binary_path.exists():
            return True, binary_path, combined_output
        else:
            return False, None, combined_output or f"Compiler failed with exit code {proc.returncode}"

    except subprocess.TimeoutExpired:
        return False, None, f"Compilation timed out after {timeout_seconds}s"
    except Exception as e:
        return False, None, f"Compilation error: {str(e)}"
