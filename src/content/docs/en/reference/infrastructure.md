---
title: Infrastructure Guide
description: DGX H100, MIG, and Kubernetes operations guide — Jeju Halla University AI Lab environment
---

## AI Lab Infrastructure

### DGX H100 Specifications

| Item | Spec |
|------|------|
| GPU | NVIDIA H100 SXM5 × 8 |
| GPU Memory | 80GB HBM3 × 8 (640GB total) |
| CPU | Intel Xeon Platinum 8480C × 2 (112 cores) |
| System Memory | 2TB DDR5 |
| Storage | 7.68TB NVMe SSD |
| Network | 8 × InfiniBand 400Gb/s |

### MIG Slice Allocation

Each student is assigned one `1g.10gb` MIG slice:

| Slice Type | GPU Memory | Max Instances | Suitable For |
|-----------|-----------|---------------|-------------|
| `1g.10gb` | 10GB | 7 | vLLM Lite models, labs |
| `2g.20gb` | 20GB | 3 | Medium-scale models |
| `3g.40gb` | 40GB | 2 | Large-scale deployment |
| `7g.80gb` | 80GB | 1 | Full GPU |

### Server Access

The DGX server is protected by Cloudflare Zero Trust. Before connecting via SSH, you must install and log in to the **Cloudflare WARP** client.

#### 1. Install Cloudflare WARP

Download and install the client for your operating system from the [Cloudflare WARP download page](https://developers.cloudflare.com/cloudflare-one/team-and-resources/devices/cloudflare-one-client/download/).

#### 2. Log in to Cloudflare Zero Trust

1. Launch Cloudflare WARP.
2. Click the gear (Settings) icon. (Windows: bottom-left / macOS: top-right menu bar)
3. Navigate to **Preferences → Account** and click **Login to Cloudflare Zero Trust**.
4. Enter the team name and log in with your university email.

> The team name, server address, and other sensitive details will be provided separately during class.

#### 3. SSH Connection

With the WARP connection active, open a terminal and connect with the following command.

```bash
ssh {USER}@{SERVER_IP} -p {PORT}
```

| Item | Description |
|------|-------------|
| `{USER}` | Server account ID |
| `{SERVER_IP}` | DGX server address |
| `{PORT}` | SSH port |

> Account information and server address will be provided individually during class.

#### 4. Check and Use GPU

```bash
# Check assigned MIG slices
nvidia-smi mig -lgip

# Monitor GPU utilization
nvidia-smi dmon -s u -d 5  # every 5 seconds

# Run Python on your assigned MIG slice
CUDA_VISIBLE_DEVICES=MIG-GPU-[UUID] python your_script.py
```

### Running Kubernetes Workloads

```yaml
# job.yaml — batch job submission
apiVersion: batch/v1
kind: Job
metadata:
  name: [student-id]-experiment
  namespace: ai-systems
spec:
  template:
    spec:
      containers:
      - name: experiment
        image: pytorch/pytorch:2.5-cuda12-cudnn9-devel
        command: ["python", "train.py"]
        resources:
          limits:
            nvidia.com/mig-1g.10gb: "1"
            memory: "16Gi"
            cpu: "8"
        volumeMounts:
        - name: workspace
          mountPath: /workspace
      volumes:
      - name: workspace
        persistentVolumeClaim:
          claimName: [student-id]-pvc
      restartPolicy: Never
```

```bash
# Submit job
kubectl apply -f job.yaml -n ai-systems

# View logs
kubectl logs -f job/[student-id]-experiment -n ai-systems

# Delete job
kubectl delete job [student-id]-experiment -n ai-systems
```

### Storage

| Path | Capacity | Purpose |
|------|----------|---------|
| `/home/[student-id]` | 100GB | Home directory |
| `/workspace/[student-id]` | 500GB | Lab projects |
| `/data/shared` | 10TB | Shared datasets (read-only) |
| `/models/cache` | 5TB | Shared model cache (read-only) |

### Useful Commands

```bash
# Check disk usage
du -sh /workspace/[student-id]/*

# Check running processes
ps aux | grep python

# Check GPU processes
nvidia-smi

# List Slurm jobs (queued jobs)
squeue -u [student-id]
```

### Important Notes

1. **Conserve compute resources**: Terminate processes when you finish a lab session
2. **Large files**: Request to share files over 1GB in `/data/shared`
3. **Model downloads**: Models already in `/models/cache` do not need to be re-downloaded
4. **Overnight batch jobs**: Submit long experiments as Kubernetes Jobs during off-hours (22:00–06:00)

### Contact

For technical issues, contact the AI Lab administrator (lab@chu.ac.kr) or open a [GitHub Issue](https://github.com/halla-ai/ai-systems-2026/issues).
