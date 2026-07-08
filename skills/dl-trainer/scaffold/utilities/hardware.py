"""hardware.py — device, precision, and distributed helpers (so you don't think
about hardware). train.py imports these; you rarely open this file.

  - device: CUDA > MPS > CPU.
  - precision: bf16 on bf16-capable CUDA, else fp16+GradScaler, else fp32.
  - DDP: enabled only under torchrun/srun; plain runs are single-device.

Run it directly to probe what you are on and what the loop will pick:
    python utilities/hardware.py
"""
from __future__ import annotations

import os

import torch
import torch.distributed as dist


###############################################################################
############################# Device & precision ##############################
###############################################################################

def ddp_info() -> dict:
    """Read the distributed env set by torchrun/srun. world_size==1 => single proc."""
    ws = int(os.environ.get("WORLD_SIZE", "1"))
    return {"distributed": ws > 1, "rank": int(os.environ.get("RANK", "0")),
            "local_rank": int(os.environ.get("LOCAL_RANK", "0")), "world_size": ws}


def pick_device(requested: str = "auto", local_rank: int = 0) -> torch.device:
    """Best available device, or an explicit override (e.g. 'cpu', 'mps', 'cuda:1')."""
    if requested and requested != "auto":
        return torch.device(requested)
    if torch.cuda.is_available():
        return torch.device(f"cuda:{local_rank}")
    if getattr(torch.backends, "mps", None) is not None and torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")


def resolve_precision(device: torch.device, amp_enabled: bool, requested: str = "auto"):
    """Return (amp_enabled, amp_dtype, use_scaler) valid for this device.
    'auto' picks bf16 on bf16-capable CUDA, else fp16+scaler on CUDA, else fp32."""
    if not amp_enabled:
        return False, torch.float32, False

    # CUDA: bf16 when supported (no scaler), else fp16 + GradScaler.
    if device.type == "cuda":
        if requested == "auto":
            dt = torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16
        else:
            dt = getattr(torch, requested)
            if dt is torch.bfloat16 and not torch.cuda.is_bf16_supported():
                print("[device] bf16 unsupported on this GPU — using fp16 + GradScaler")
                dt = torch.float16
        return True, dt, dt is torch.float16

    # MPS / CPU: autocast support is partial and GradScaler is CUDA-only — use fp32.
    print(f"[device] {device.type}: running fp32 (AMP not enabled; limited autocast support)")
    return False, torch.float32, False


###############################################################################
############################## Distributed (DDP) ##############################
###############################################################################

def setup_distributed(info: dict, device: torch.device) -> None:
    """Init the process group under torchrun/srun (nccl on CUDA, gloo otherwise)."""
    if not info["distributed"]:
        return
    dist.init_process_group(backend="nccl" if device.type == "cuda" else "gloo")
    if device.type == "cuda":
        torch.cuda.set_device(info["local_rank"])


def is_main(info: dict) -> bool:
    return info["rank"] == 0


def barrier(info: dict) -> None:
    if info["distributed"] and dist.is_initialized():
        dist.barrier()


def cleanup(info: dict) -> None:
    if info["distributed"] and dist.is_initialized():
        dist.destroy_process_group()


###############################################################################
#################################### Probe ####################################
###############################################################################

def probe(exp_dir=None):
    """Print the machine (and, if given an experiment dir, the device/precision the
    loop will pick from its config). Run first to confirm your GPU/precision."""

    # What torch sees: versions + which accelerators are available.
    print(f"torch            {torch.__version__}")
    print(f"cuda build       {torch.version.cuda}")
    cuda = torch.cuda.is_available()
    mps = getattr(torch.backends, "mps", None) is not None and torch.backends.mps.is_available()
    print(f"cuda available   {cuda}")
    print(f"mps available    {mps}")

    # Per-device detail: name, memory, compute capability (flag arch/torch mismatch).
    if cuda:
        print(f"gpu count        {torch.cuda.device_count()}  "
              "(multi-GPU: launch with torchrun / scripts/run.sh NPROC=N for DDP)")
        arch_list = torch.cuda.get_arch_list() if hasattr(torch.cuda, "get_arch_list") else []
        for i in range(torch.cuda.device_count()):
            p = torch.cuda.get_device_properties(i)
            sm = f"sm_{p.major}{p.minor}"
            warn = "" if (not arch_list or sm in arch_list) else "  <-- NOT in this torch build (upgrade torch/CUDA)"
            print(f"  [{i}] {p.name}  {p.total_memory/1e9:.1f} GB  {sm}{warn}")
        print(f"bf16 supported   {torch.cuda.is_bf16_supported()}")
    elif mps:
        print("device           Apple MPS (fp32; AMP autocast support is limited)")
    else:
        print("device           cpu  (no accelerator; training will be slow)")

    # If given an experiment, show what device/precision its config resolves to.
    if exp_dir:
        try:
            import yaml
            cfg = yaml.safe_load(open(f"{exp_dir}/config.yaml"))
            d = pick_device(cfg["run"].get("device", "auto"))
            amp, dtype, scaler = resolve_precision(d, cfg["train"]["amp"], cfg["train"].get("amp_dtype", "auto"))
            print(f"\nfor {exp_dir}:")
            print(f"resolved device {d}")
            print(f"resolved amp     {amp}  dtype={str(dtype).replace('torch.','')}  grad_scaler={scaler}")
        except FileNotFoundError:
            print(f"\n(no config.yaml in {exp_dir})")


if __name__ == "__main__":
    import sys
    probe(sys.argv[1] if len(sys.argv) > 1 else None)
