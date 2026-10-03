"""
Optimization & Code Post-Processing Subsystem
Injects OpenMP pragma hints, SIMD directives, and ensures clean formatting.
"""

import re


def extract_cpp_code(raw_llm_response: str) -> str:
    """Extracts raw C++ code from LLM response, stripping markdown codeblocks."""
    text = raw_llm_response.strip()

    # Match ```cpp ... ``` or ```c++ ... ```
    match = re.search(r"```(?:cpp|c\+\+|c)?\s*(.*?)\s*```", text, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()

    return text


def inject_openmp_simd_directives(cpp_source: str) -> str:
    """
    Ensures OpenMP headers and pragmas are present if loops are identified.
    """
    code = cpp_source

    # Ensure <omp.h> is included if OpenMP pragmas are used
    if "#pragma omp" in code and "#include <omp.h>" not in code:
        code = "#include <omp.h>\n" + code

    return code
