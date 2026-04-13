"""
MIG 1g.10gb 슬라이스에서 Llama-3-8B 4-bit 양자화 모델 추론 벤치마크.

요구사항:
- NVIDIA GPU (MIG 1g.10gb 슬라이스, 10GB VRAM)
- transformers, bitsandbytes, accelerate, torch

사용법:
    # 1. 패키지 설치
    pip install transformers bitsandbytes accelerate torch

    # 2. 벤치마크 실행
    python llm_benchmark.py

    # 3. 특정 모델로 실행
    python llm_benchmark.py --model "meta-llama/Meta-Llama-3-8B"

    # 4. 결과만 JSON으로 출력
    python llm_benchmark.py --json
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from dataclasses import asdict, dataclass, field

logging.basicConfig(
    stream=sys.stderr,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("llm-benchmark")


@dataclass
class BenchmarkResult:
    """벤치마크 결과."""
    model_name: str = ""
    quantization: str = "4-bit (NF4)"
    device: str = ""
    mig_profile: str = ""

    # 메모리
    vram_total_gb: float = 0.0
    vram_used_after_load_gb: float = 0.0
    vram_peak_gb: float = 0.0
    model_size_gb: float = 0.0

    # 추론 성능
    num_prompts: int = 0
    total_tokens_generated: int = 0
    total_time_sec: float = 0.0
    tokens_per_sec: float = 0.0
    avg_latency_ms: float = 0.0
    first_token_latency_ms: float = 0.0

    # 개별 결과
    prompt_results: list[dict] = field(default_factory=list)

    # 환경
    torch_version: str = ""
    cuda_version: str = ""
    driver_version: str = ""

    # 상태
    success: bool = False
    error: str = ""


def get_gpu_info() -> dict:
    """현재 GPU 정보를 수집."""
    info = {"available": False}
    try:
        import torch
        if torch.cuda.is_available():
            info["available"] = True
            info["device_name"] = torch.cuda.get_device_name(0)
            info["vram_total_gb"] = round(
                torch.cuda.get_device_properties(0).total_mem / (1024**3), 2
            )
            info["torch_version"] = torch.__version__
            info["cuda_version"] = torch.version.cuda or "N/A"

            # MIG 확인
            try:
                import pynvml
                pynvml.nvmlInit()
                handle = pynvml.nvmlDeviceGetHandleByIndex(0)
                current_mode, _ = pynvml.nvmlDeviceGetMigMode(handle)
                info["mig_enabled"] = current_mode == pynvml.NVML_DEVICE_MIG_ENABLE
                info["driver_version"] = pynvml.nvmlSystemGetDriverVersion()
                pynvml.nvmlShutdown()
            except Exception:
                info["mig_enabled"] = False
                info["driver_version"] = "N/A"
    except ImportError:
        pass
    return info


def load_model_4bit(model_name: str):
    """4-bit 양자화로 모델 로드."""
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
    import torch

    logger.info("Loading model: %s (4-bit NF4 quantization)", model_name)

    quantization_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_use_double_quant=True,  # 이중 양자화로 메모리 절약
    )

    tokenizer = AutoTokenizer.from_pretrained(model_name)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        quantization_config=quantization_config,
        device_map="auto",
        torch_dtype=torch.float16,
    )

    return model, tokenizer


def measure_inference(model, tokenizer, prompt: str, max_new_tokens: int = 128) -> dict:
    """단일 프롬프트의 추론 시간을 측정."""
    import torch

    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    input_len = inputs["input_ids"].shape[1]

    torch.cuda.synchronize()
    start = time.perf_counter()

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=False,  # greedy decoding for reproducibility
            temperature=1.0,
        )

    torch.cuda.synchronize()
    end = time.perf_counter()

    output_len = outputs.shape[1] - input_len
    elapsed = end - start
    generated_text = tokenizer.decode(outputs[0][input_len:], skip_special_tokens=True)

    return {
        "prompt": prompt[:80] + "..." if len(prompt) > 80 else prompt,
        "input_tokens": input_len,
        "output_tokens": output_len,
        "time_sec": round(elapsed, 3),
        "tokens_per_sec": round(output_len / elapsed, 2) if elapsed > 0 else 0,
        "generated_text_preview": generated_text[:200],
    }


# 벤치마크 프롬프트 (다양한 태스크)
BENCHMARK_PROMPTS = [
    # 코드 생성
    "Write a Python function that checks if a number is prime:\n```python\ndef is_prime(n):",
    # 요약
    "Summarize the concept of GPU Multi-Instance GPU (MIG) technology in 3 sentences:",
    # 추론
    "If a GPU has 80GB of memory and is split into 7 MIG instances of 10GB each, how much memory is unallocated? Show your reasoning:",
    # 번역
    "Translate the following to Korean: 'Machine learning models require significant computational resources for training and inference.'",
    # Q&A
    "What is the difference between model parallelism and data parallelism in distributed training?",
]


def run_benchmark(model_name: str, output_json: bool = False) -> BenchmarkResult:
    """전체 벤치마크 실행."""
    result = BenchmarkResult(model_name=model_name)

    # GPU 정보 수집
    gpu_info = get_gpu_info()
    if not gpu_info["available"]:
        result.error = "CUDA GPU not available. Run on a machine with NVIDIA GPU."
        logger.error(result.error)
        return result

    result.device = gpu_info.get("device_name", "Unknown")
    result.vram_total_gb = gpu_info.get("vram_total_gb", 0)
    result.mig_profile = "1g.10gb (detected)" if gpu_info.get("mig_enabled") else "N/A (MIG not enabled)"
    result.torch_version = gpu_info.get("torch_version", "")
    result.cuda_version = gpu_info.get("cuda_version", "")
    result.driver_version = gpu_info.get("driver_version", "")

    logger.info("GPU: %s (%.1f GB)", result.device, result.vram_total_gb)
    logger.info("MIG: %s", result.mig_profile)

    # 모델 로드
    try:
        import torch
        torch.cuda.reset_peak_memory_stats()

        load_start = time.perf_counter()
        model, tokenizer = load_model_4bit(model_name)
        load_time = time.perf_counter() - load_start

        result.vram_used_after_load_gb = round(
            torch.cuda.memory_allocated() / (1024**3), 2
        )
        result.model_size_gb = result.vram_used_after_load_gb
        logger.info(
            "Model loaded in %.1fs, VRAM used: %.2f GB",
            load_time, result.vram_used_after_load_gb,
        )

        # MIG 1g.10gb 메모리 체크
        if result.vram_used_after_load_gb > 9.5:
            logger.warning(
                "Model uses %.2f GB, may not fit in 1g.10gb MIG slice (10GB)",
                result.vram_used_after_load_gb,
            )

    except Exception as e:
        result.error = f"Model loading failed: {e}"
        logger.error(result.error)
        return result

    # 워밍업
    logger.info("Warming up...")
    try:
        _ = measure_inference(model, tokenizer, "Hello", max_new_tokens=10)
    except Exception as e:
        logger.warning("Warmup failed: %s", e)

    # 벤치마크 실행
    logger.info("Running benchmark with %d prompts...", len(BENCHMARK_PROMPTS))
    total_tokens = 0
    total_time = 0.0

    for i, prompt in enumerate(BENCHMARK_PROMPTS):
        logger.info("Prompt %d/%d...", i + 1, len(BENCHMARK_PROMPTS))
        try:
            res = measure_inference(model, tokenizer, prompt, max_new_tokens=128)
            result.prompt_results.append(res)
            total_tokens += res["output_tokens"]
            total_time += res["time_sec"]

            if i == 0:
                result.first_token_latency_ms = round(
                    res["time_sec"] / max(res["output_tokens"], 1) * 1000, 1
                )
        except Exception as e:
            logger.error("Prompt %d failed: %s", i + 1, e)
            result.prompt_results.append({"prompt": prompt[:80], "error": str(e)})

    # 결과 집계
    import torch
    result.num_prompts = len(BENCHMARK_PROMPTS)
    result.total_tokens_generated = total_tokens
    result.total_time_sec = round(total_time, 3)
    result.tokens_per_sec = round(total_tokens / total_time, 2) if total_time > 0 else 0
    result.avg_latency_ms = round(
        (total_time / len(BENCHMARK_PROMPTS)) * 1000, 1
    ) if BENCHMARK_PROMPTS else 0
    result.vram_peak_gb = round(torch.cuda.max_memory_allocated() / (1024**3), 2)
    result.success = True

    logger.info("Benchmark complete: %.2f tokens/sec, peak VRAM: %.2f GB",
                result.tokens_per_sec, result.vram_peak_gb)

    return result


def print_report(result: BenchmarkResult, as_json: bool = False):
    """벤치마크 결과를 출력."""
    if as_json:
        print(json.dumps(asdict(result), indent=2, ensure_ascii=False))
        return

    print("\n" + "=" * 60)
    print("  Llama-3-8B 4-bit Quantization Inference Benchmark")
    print("=" * 60)

    print(f"\n{'Model:':<30} {result.model_name}")
    print(f"{'Quantization:':<30} {result.quantization}")
    print(f"{'Device:':<30} {result.device}")
    print(f"{'MIG Profile:':<30} {result.mig_profile}")
    print(f"{'PyTorch:':<30} {result.torch_version}")
    print(f"{'CUDA:':<30} {result.cuda_version}")
    print(f"{'Driver:':<30} {result.driver_version}")

    print(f"\n--- Memory ---")
    print(f"{'VRAM Total:':<30} {result.vram_total_gb:.2f} GB")
    print(f"{'Model Size (loaded):':<30} {result.model_size_gb:.2f} GB")
    print(f"{'VRAM Peak:':<30} {result.vram_peak_gb:.2f} GB")
    print(f"{'VRAM Utilization:':<30} {result.vram_peak_gb / result.vram_total_gb * 100:.1f}%" if result.vram_total_gb > 0 else "")

    print(f"\n--- Performance ---")
    print(f"{'Prompts:':<30} {result.num_prompts}")
    print(f"{'Total Tokens Generated:':<30} {result.total_tokens_generated}")
    print(f"{'Total Time:':<30} {result.total_time_sec:.3f} sec")
    print(f"{'Throughput:':<30} {result.tokens_per_sec:.2f} tokens/sec")
    print(f"{'Avg Latency per Prompt:':<30} {result.avg_latency_ms:.1f} ms")
    print(f"{'First Token Latency:':<30} {result.first_token_latency_ms:.1f} ms")

    fit_in_mig = result.vram_peak_gb <= 10.0
    print(f"\n--- MIG 1g.10gb Compatibility ---")
    print(f"{'Fits in 10GB slice:':<30} {'YES' if fit_in_mig else 'NO'}")
    print(f"{'Headroom:':<30} {10.0 - result.vram_peak_gb:.2f} GB" if fit_in_mig else f"{'Overflow:':<30} {result.vram_peak_gb - 10.0:.2f} GB")

    if result.prompt_results:
        print(f"\n--- Per-Prompt Results ---")
        for i, pr in enumerate(result.prompt_results):
            if "error" in pr:
                print(f"  [{i+1}] ERROR: {pr['error']}")
            else:
                print(f"  [{i+1}] {pr['output_tokens']} tokens in {pr['time_sec']:.2f}s "
                      f"({pr['tokens_per_sec']:.1f} tok/s)")

    if result.error:
        print(f"\n[ERROR] {result.error}")

    print("\n" + "=" * 60)


def main():
    parser = argparse.ArgumentParser(description="Llama-3-8B 4-bit 추론 벤치마크")
    parser.add_argument(
        "--model",
        default="meta-llama/Meta-Llama-3-8B",
        help="HuggingFace 모델 ID (기본: meta-llama/Meta-Llama-3-8B)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="결과를 JSON으로 출력",
    )
    args = parser.parse_args()

    result = run_benchmark(args.model, output_json=args.json)
    print_report(result, as_json=args.json)

    if not result.success:
        sys.exit(1)


if __name__ == "__main__":
    main()

