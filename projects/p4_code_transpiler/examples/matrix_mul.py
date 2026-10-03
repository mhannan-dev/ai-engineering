"""
Matrix Multiplication Benchmark (GEMM)
Multiplies two NxN matrices and computes the sum of the resulting matrix.
"""

import time

def matrix_multiply(n: int = 250):
    # Initialize matrices
    A = [[float(i + j) for j in range(n)] for i in range(n)]
    B = [[float(i * j) for j in range(n)] for i in range(n)]
    C = [[0.0 for _ in range(n)] for _ in range(n)]

    start = time.perf_counter()

    for i in range(n):
        for k in range(n):
            for j in range(n):
                C[i][j] += A[i][k] * B[k][j]

    elapsed = (time.perf_counter() - start) * 1000.0

    total_sum = sum(sum(row) for row in C)
    print(f"Matrix Dimension: {n}x{n}")
    print(f"Matrix Sum: {total_sum:.4f}")
    print(f"Elapsed Time: {elapsed:.2f} ms")

if __name__ == "__main__":
    matrix_multiply(250)
