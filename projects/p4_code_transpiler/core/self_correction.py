"""
Compiler Feedback Self-Correction Loop
Iteratively repairs C++ compilation errors using compiler stderr feedback and LLM repair prompts.
"""

from pathlib import Path
from typing import Tuple, List, Dict, Any, Optional
from openai import AsyncOpenAI
from config.settings import settings
from compiler.builder import compile_cpp
from core.optimizer import extract_cpp_code, inject_openmp_simd_directives
from core.transpiler import transpile_python_to_cpp

SELF_CORRECTION_SYSTEM_PROMPT = """You are an expert C++ Compiler Diagnostics and Auto-Debugging Specialist.
A C++20 source file generated from Python failed to compile with g++.

Your task:
1. Carefully inspect the compiler error diagnostics (stderr) provided.
2. Identify the exact line numbers and syntax/type/linking errors.
3. Fix the C++20 code completely while preserving the original computation and output logic.
4. Ensure all required headers (<iostream>, <vector>, <cmath>, <omp.h>, etc.) are present.
5. Return ONLY the corrected C++ code inside a ```cpp and ``` code block.
"""


async def transpile_with_feedback_loop(
    source_code: str,
    optimization_level: str = "O3",
    self_correction: bool = True,
    max_attempts: int = 3,
    enable_openmp: bool = True,
    source_id: Optional[str] = None,
    client: Optional[AsyncOpenAI] = None,
) -> Tuple[str, bool, List[Dict[str, Any]], Optional[Path]]:
    """
    Executes the full transpile -> build -> self-correct loop.

    Returns:
        Tuple of (
            final_cpp_code: str,
            is_compiled: bool,
            attempts: List[Dict[str, Any]],
            binary_path: Optional[Path]
        )
    """
    if not client:
        client = AsyncOpenAI(
            api_key=settings.openai_api_key or "sk-dummy",
            base_url=settings.openai_base_url if settings.openai_base_url else None,
        )

    # 1. Initial Transpilation
    current_cpp = await transpile_python_to_cpp(
        source_code=source_code,
        optimization_level=optimization_level,
        enable_openmp=enable_openmp,
        client=client,
    )

    attempts_log: List[Dict[str, Any]] = []

    # 2. First Compilation Attempt
    success, binary_path, compiler_errors = compile_cpp(
        cpp_source=current_cpp,
        source_id=source_id,
        opt_level=optimization_level,
        enable_openmp=enable_openmp,
    )

    if success:
        attempts_log.append({
            "attempt": 1,
            "compiler_errors": "",
            "fixed": True,
        })
        return current_cpp, True, attempts_log, binary_path

    # Log initial failure
    attempts_log.append({
        "attempt": 1,
        "compiler_errors": compiler_errors,
        "fixed": False,
    })

    if not self_correction:
        return current_cpp, False, attempts_log, None

    # 3. Iterative Feedback Loop
    current_errors = compiler_errors
    for attempt_num in range(2, max_attempts + 1):
        repair_prompt = f"""The following C++20 code failed to compile with g++.

--- COMPILER ERRORS (STDERR) ---
{current_errors}

--- FAILING C++ CODE ---
```cpp
{current_cpp}
```

--- ORIGINAL PYTHON CODE ---
```python
{source_code}
```

Please fix all compiler errors and return the complete, corrected C++20 source code.
"""
        try:
            response = await client.chat.completions.create(
                model=settings.llm_model,
                messages=[
                    {"role": "system", "content": SELF_CORRECTION_SYSTEM_PROMPT},
                    {"role": "user", "content": repair_prompt},
                ],
                temperature=0.05,
                max_tokens=4096,
            )

            repaired_code = extract_cpp_code(response.choices[0].message.content or "")
            repaired_code = inject_openmp_simd_directives(repaired_code)
            current_cpp = repaired_code

            # Re-attempt compilation
            success, binary_path, new_errors = compile_cpp(
                cpp_source=current_cpp,
                source_id=source_id,
                opt_level=optimization_level,
                enable_openmp=enable_openmp,
            )

            if success:
                attempts_log.append({
                    "attempt": attempt_num,
                    "compiler_errors": "",
                    "fixed": True,
                })
                return current_cpp, True, attempts_log, binary_path
            else:
                current_errors = new_errors
                attempts_log.append({
                    "attempt": attempt_num,
                    "compiler_errors": current_errors,
                    "fixed": False,
                })

        except Exception as e:
            attempts_log.append({
                "attempt": attempt_num,
                "compiler_errors": f"Auto-debugging API call failed: {str(e)}",
                "fixed": False,
            })
            break

    return current_cpp, False, attempts_log, None
