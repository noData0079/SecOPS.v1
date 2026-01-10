# WSL / Linux ML Stack Setup

Due to compatibility issues with `vLLM` and specific `torch` CUDA versions on Windows Native, we recommend running the Heavy ML components in WSL2 (Ubuntu).

## Validated Stack
*   **OS**: Ubuntu 24.04 LTS (WSL2)
*   **Python**: 3.10 or 3.11 (via Deadsnakes PPA)
*   **Libraries**:
    *   `build-essential` (required for compiling vLLM extensions)
    *   `python3.10-dev` / `python3.11-dev`

## One-Click Setup
Run the consolidated setup script to replicate the validated environment:
```bash
./tools/setup-wsl-ml.sh
```

## Python Version Note
Windows Python 3.13 was found to have limited pre-built wheels for older Torch/vLLM versions. Using Python 3.11 in WSL is the stable path.
