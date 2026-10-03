/** Sample programs for the editor (mirrors ../examples). Deterministic output so benchmarks can compare. */

export interface ExampleProgram {
  id: string;
  title: string;
  description: string;
  source: string;
}

export const EXAMPLES: ExampleProgram[] = [
  {
    id: 'matrix_mul',
    title: 'Matrix multiplication',
    description: 'Naive O(n³) multiply of two 200×200 matrices',
    source: `def matmul(a, b, n):
    c = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for k in range(n):
            aik = a[i][k]
            for j in range(n):
                c[i][j] += aik * b[k][j]
    return c


def main():
    n = 200
    a = [[(i * n + j) % 7 * 0.5 for j in range(n)] for i in range(n)]
    b = [[(i + 2 * j) % 5 * 0.25 for j in range(n)] for i in range(n)]
    c = matmul(a, b, n)
    checksum = 0.0
    for row in c:
        for value in row:
            checksum += value
    print(f"checksum={checksum:.4f}")


if __name__ == "__main__":
    main()
`,
  },
  {
    id: 'numerical_sim',
    title: 'Heat diffusion simulation',
    description: '1D explicit finite-difference heat equation, 20k steps',
    source: `def simulate(cells, steps, alpha):
    u = [0.0] * cells
    u[cells // 2] = 100.0
    for _ in range(steps):
        nxt = u[:]
        for i in range(1, cells - 1):
            nxt[i] = u[i] + alpha * (u[i - 1] - 2.0 * u[i] + u[i + 1])
        u = nxt
    return u


def main():
    u = simulate(cells=400, steps=20000, alpha=0.25)
    total = sum(u)
    peak = max(u)
    print(f"total={total:.6f} peak={peak:.6f}")


if __name__ == "__main__":
    main()
`,
  },
];
