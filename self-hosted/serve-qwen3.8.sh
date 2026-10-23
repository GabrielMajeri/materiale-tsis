#!/usr/bin/env bash

module add cuda/13.4.3

# Get the script's directory
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

# Expose the vLLM server on all interfaces and use port 27182
HOST=0.0.0.0
PORT=27182

# Store the cache in a local directory to avoid using the default cache location
CACHE_DIR="$SCRIPT_DIR/cache"
echo "Using cache directory: $CACHE_DIR"
mkdir -p "$CACHE_DIR"

export HF_HOME="$CACHE_DIR/huggingface"
export VLLM_CACHE_ROOT="$CACHE_DIR/vllm"

export NCCL_NVLS_ENABLE=0

uv run vllm serve --host $HOST --port $PORT Qwen/Qwen3.8-27B-FP8 \
    --tensor-parallel-size 2 --gpu-memory-utilization 0.9 \
    --enable-auto-tool-choice \
    --tool-call-parser qwen3_coder \
    --reasoning-parser qwen3 \
    --mm-encoder-tp-mode data
