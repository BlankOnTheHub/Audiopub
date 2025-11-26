# Audiopub

![Audiopub Screenshot](screenshot.png)

**Turn your EPUBs into high-fidelity audiobooks locally.**

Audiopub is a slick, desktop-based power tool that converts ebooks into chapterized .m4b audiobooks using **on-device TTS engines**. It runs entirely on your machine—no cloud APIs, no per-character fees.

### Supported TTS Engines:
- **Supertonic** (default): Supertone's high-quality diffusion-based TTS
- **NeuTTS Air**: Instant voice cloning from 3-15 second audio samples

## Features

*   **⚡ Local & Private:** Powered by ONNX Runtime. Zero data leaves your rig.
*   **🚀 GPU Acceleration:** Optional CUDA support for 10x faster synthesis on NVIDIA GPUs.
*   **💎 Deep Dark UI:** A beautiful, responsive glass-morphism interface built with NiceGUI.
*   **🧠 Smart Context:** Splits text intelligently by sentence to maintain narrative flow.
*   **⏯️ Resumable:** Crash? Quit? No problem. Resume exactly where you left off.
*   **📦 Auto-Muxing:** Outputs ready-to-listen `.m4b` files with proper metadata and chapters.
*   **🎚️ Configurable Quality:** Adjust inference steps (2-128) for speed/quality tradeoff.

## Quick Start

1.  **Install:**
    ```bash
    git clone https://github.com/yourusername/audiopub.git
    cd audiopub
    git lfs pull  # Essential: Downloads the AI models
    pip install -r requirements.txt
    ```

2.  **Run:**
    ```bash
    python audiopub/main.py
    ```
    The WebUI launches automatically at `http://localhost:8080`

3.  **Generate:**
    *   Select your EPUB and Voice
    *   GPU acceleration is **enabled by default** with 16-step quality setting
    *   Adjust GPU toggle and inference steps as needed in the UI
    *   Hit **Generate** and enjoy high-quality audiobooks at 6-10x faster speed! ⚡

**Note:** GPU is automatically configured on startup. For manual setup or troubleshooting, see [GPU_SETUP.md](GPU_SETUP.md).

## Requirements

*   **Python 3.9+**
*   **FFmpeg** (Must be in your PATH)
*   **Git LFS** (For model weights)

## Voice Styles

### For Supertonic (default):
Drop your custom `.json` voice style configs into `audiopub/assets/`. The app will auto-detect them.

### For NeuTTS Air:
1. **Install additional dependencies:**
   ```bash
   pip install -r requirements-neutts.txt
   sudo apt-get install espeak  # or: brew install espeak on macOS
   ```

2. **Set the TTS engine:**
   ```bash
   export AUDIOPUB_TTS_ENGINE=neutts-air
   ```

3. **Add voice samples:**
   Place `.wav` audio files (3-15 seconds) with matching `.txt` transcript files in:
   - `audiopub/assets/reference_audio/`

   Example:
   ```
   reference_audio/
   ├── narrator1.wav    # 5 seconds of clean speech
   └── narrator1.txt    # Transcript of the audio
   ```

   See `audiopub/assets/reference_audio/README.md` for detailed setup instructions.

## Switching TTS Engines

Change engines by setting the environment variable:
```bash
# Use NeuTTS Air (with voice cloning)
export AUDIOPUB_TTS_ENGINE=neutts-air

# Use Supertonic (default)
export AUDIOPUB_TTS_ENGINE=supertonic
```

## GPU Acceleration

### Default Configuration

✅ **GPU acceleration is enabled by default** in the WebUI with quality-focused settings (16-step inference for balanced quality/speed).

**In the WebUI:**
1. **"GPU ACCELERATION"** toggle starts as **ON**
2. **"INFERENCE STEPS"** defaults to **16** (balanced quality)
3. Adjust steps with the slider (2-128) anytime:
   - 2-5 steps: Real-time/streaming (fastest, lower quality)
   - 16 steps: Balanced quality/speed (default)
   - 32+ steps: High quality (slower, best audio)

### Setup

**Automatic (Recommended):**
GPU support is automatically configured on startup if available.

**Manual Setup:**
If you need to manually enable GPU:
```bash
# Enable GPU for current shell session
source setup_gpu.sh

# Or add to your ~/.bashrc or ~/.zshrc
```

**Requirements:**
- NVIDIA GPU with CUDA support
- CUDA 11.8+ or 12.x
- `onnxruntime-gpu` installed (installed by default)

### Benchmarking

Test GPU performance on your hardware:

```bash
# CPU-only benchmark
python benchmark_gpu.py

# GPU benchmark (with CUDA setup)
source setup_gpu.sh
python benchmark_gpu.py --gpu --steps 2,5,16,32,64,128

# Save results for comparison
python benchmark_gpu.py --gpu --output gpu_results.json
```

**Real-World Performance Examples:**

**RTX 2070 (Tested):**
```
Steps  | GPU Speed      | CPU Speed    | Speedup
-------|----------------|--------------|--------
2      | 1915-3614 c/s  | 182-409 c/s  | 8.8-10.5x
16     | 534-1091 c/s   | 89-163 c/s   | 6.0-6.7x
32     | 285-606 c/s    | 56-98 c/s    | 5.1-6.2x
```

**Expected Performance (RTX4090):**
- GPU: ~12,000 chars/sec (2-step) → ~600 chars/sec (16-step)
- CPU: ~1,200 chars/sec (2-step) → ~400 chars/sec (16-step)

See [GPU_SETUP.md](GPU_SETUP.md), [GPU_DEFAULTS.md](GPU_DEFAULTS.md), and [GPU_BENCHMARKING.md](GPU_BENCHMARKING.md) for detailed setup, configuration, performance tuning, and troubleshooting.

---

## For AI Agents (Claude Code, GitHub Copilot, etc.)

This repository is optimized for AI-assisted development. **Before working on Audiopub:**

1. **Read** [AGENT_NOTES.md](AGENT_NOTES.md) – Quick system prompt (one page)
2. **Review** [AGENT_GUIDE.md](AGENT_GUIDE.md) – Operating procedures & testing checklist
3. **Understand** [ARCHITECTURE.md](ARCHITECTURE.md) – Module boundaries & what's locked

**Key constraints:**
- ✅ Safe changes: Add voice styles, optimize performance, fix bugs, add tests
- ❌ Unsafe changes: Remove CPU support, break TTS factory, add cloud APIs, remove channel boundaries
- 🔒 Locked files: `tts_base.py` (method signatures), some aspects of `audio.py`, `epub.py`, `worker.py`

**Additional context:**
- [STRATEGY.md](STRATEGY.md) – Project philosophy & non-negotiable constraints
- [ENTRYPOINTS.md](ENTRYPOINTS.md) – Module map & data flow diagrams
- [ROADMAP.md](ROADMAP.md) – Phase tracking & current blockers
- [repo_manifest.json](repo_manifest.json) – Machine-readable metadata

These documents live in the repo permanently and are updated as the project evolves.

---
*Built for audiophiles who code.*
