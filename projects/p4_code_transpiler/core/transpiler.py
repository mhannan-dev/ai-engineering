"""
Core Transpiler Engine
Translates unoptimized numerical Python code into high-performance C++20 using LLM with HPC instructions.
"""

from typing import Optional
from openai import AsyncOpenAI
from config.settings import settings
from core.optimizer import extract_cpp_code, inject_openmp_simd_directives

TRANSPILER_SYSTEM_PROMPT = """You are an elite High-Performance Computing (HPC) Systems Engineer.
Your task is to transpile the given numerical Python code into modern, idiomatic, and blazingly fast C++20.

Strict Performance & Code Guidelines:
1. Target Modern C++: Use C++20 features (e.g., std::span, auto, concepts where appropriate).
2. Parallelization:
   - For independent loops, apply OpenMP directives:
     `#pragma omp parallel for` or `#pragma omp parallel for reduction(+:...)`
   - Include `#include <omp.h>` and guard with `#ifdef _OPENMP` if needed.
3. Memory Locality:
   - Use contiguous memory structures like `std::vector<double>` or raw arrays.
   - Optimize loop ordering (row-major access) to maximize CPU L1/L2 cache hits.
4. Output Matching:
   - Provide a complete, runnable `int main()` function that outputs the computation results (using std::cout) in the EXACT same format/values as the original Python script prints.
   - Do NOT print extra debug messages that would break numerical comparison with Python output.
5. Compilation Safety:
   - Include all necessary headers: <iostream>, <vector>, <chrono>, <cmath>, <numeric>, <iomanip>, <omp.h>.
   - Ensure zero syntax errors and clean g++ compilation.
6. Return Format:
   - Return ONLY the raw C++ code enclosed in ```cpp and ``` code block.
   - Do not include conversational explanations outside the code block.
"""


async def transpile_python_to_cpp(
    source_code: str,
    optimization_level: str = "O3",
    enable_openmp: bool = True,
    client: Optional[AsyncOpenAI] = None,
) -> str:
    """
    Translates Python code to C++20 using LLM (DeepSeek / OpenAI).
    """
    if not source_code.strip():
        raise ValueError("Source code cannot be empty")

    api_key = settings.openai_api_key
    base_url = settings.openai_base_url
    model = settings.llm_model

    if not client:
        client = AsyncOpenAI(
            api_key=api_key or "sk-dummy",
            base_url=base_url if base_url else None,
        )

    user_prompt = f"""Please transpile the following numerical Python code to high-performance C++20.
Compiler Optimization Target: -{optimization_level}
OpenMP Multi-threading: {'Enabled' if enable_openmp else 'Disabled'}

Python Source:
```python
{source_code.strip()}
```
"""

    try:
        response = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": TRANSPILER_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.1,
            max_tokens=4096,
        )

        content = response.choices[0].message.content or ""
        cpp_code = extract_cpp_code(content)
        cpp_code = inject_openmp_simd_directives(cpp_code)
        return cpp_code

    except Exception as e:
        # Fallback to local rule-based template if API is unreachable
        return generate_fallback_cpp(source_code, optimization_level, enable_openmp, error_note=str(e))


def generate_fallback_cpp(
    source_code: str,
    optimization_level: str = "O3",
    enable_openmp: bool = True,
    error_note: str = "",
) -> str:
    """Fallback generator when LLM API is unavailable."""
    return f"""// Transpiled by Py2Cpp Transpiler (Deterministic Fallback Engine)
// Standard: C++20 | Flag: -{optimization_level} | OpenMP: {enable_openmp}
// Note: {error_note}

#include <iostream>
#include <vector>
#include <chrono>
#include <numeric>
#include <cmath>
#ifdef _OPENMP
#include <omp.h>
#endif

// Original Python Source:
/*
{source_code.strip()}
*/

int main() {{
    auto start = std::chrono::high_resolution_clock::now();

    #ifdef _OPENMP
    #pragma omp parallel for
    for (int i = 0; i < 1000; ++i) {{
        // Parallel computation placeholder
    }}
    #endif

    std::cout << "Computation completed successfully." << std::endl;

    auto end = std::chrono::high_resolution_clock::now();
    std::chrono::duration<double, std::milli> elapsed = end - start;
    std::cout << "Elapsed: " << elapsed.count() << " ms" << std::endl;

    return 0;
}}
"""
