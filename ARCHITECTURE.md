# ARCHITECTURE.md – Audiopub System Design & Module Boundaries

## System Overview

Audiopub follows a **linear pipeline architecture** that transforms an EPUB file into a playable M4B audiobook.

```
┌─────────────┐
│ EPUB Input  │
└──────┬──────┘
       │
       ▼
┌──────────────────────────────────┐
│ EPUB Parser (epub.py)            │
│ • Unzip EPUB container           │
│ • Parse OPF manifest             │
│ • Extract text from XHTML        │
│ • Identify chapter boundaries    │
└──────┬───────────────────────────┘
       │ chapters: [text, metadata]
       ▼
┌──────────────────────────────────┐
│ Text Chunking (audio.py)         │
│ • Split by sentences (NLTK)      │
│ • Group by paragraphs            │
│ • Estimate synthesis time        │
└──────┬───────────────────────────┘
       │ chunks: [text, chapter_id]
       ▼
┌──────────────────────────────────┐
│ TTS Synthesis                    │
│ (tts.py or tts_neutts.py)       │
│ • Load ONNX models               │
│ • Text → tokens (encoder)        │
│ • Tokens → duration (predictor)  │
│ • Tokens + duration → mel-spec   │
│ • Mel-spec → PCM (vocoder)       │
└──────┬───────────────────────────┘
       │ wav_data: [bytes per chunk]
       ▼
┌──────────────────────────────────┐
│ Audio Assembly (audio.py)        │
│ • Concatenate WAVs               │
│ • Add 5s silence between chaps   │
│ • Embed chapter metadata (ID3v2) │
└──────┬───────────────────────────┘
       │ wav_file: raw PCM
       ▼
┌──────────────────────────────────┐
│ M4B Muxing (audio.py via ffmpeg) │
│ • Encode WAV → AAC               │
│ • Write chapter marks            │
│ • Embed artwork & metadata       │
└──────┬───────────────────────────┘
       │
       ▼
┌──────────────────────────────┐
│ M4B Output                   │
│ audiopub/output/{book}.m4b   │
└──────────────────────────────┘
```

---

## Core Modules: Responsibilities & Constraints

### 1. Main Entry Point (audiopub/main.py)

**Responsibility:**
- Launch NiceGUI web server on localhost:8000
- Handle user file upload and settings
- Manage UI state (progress bars, logs, download links)
- Spawn worker thread for synthesis (non-blocking UI)
- Serve generated audiobooks for download

**Editable:** ✅ Yes

**Can Edit:**
- Add new UI elements
- Change layout/styling
- Add new user-facing settings
- Improve progress reporting
- Add new API endpoints (serve more file formats)

**Cannot Edit Without Discussion:**
- Worker thread synchronization logic
- File path validation/sanitization

**Key Invariants:**
- UI must never block on synthesis (use `app.call_after_dark()` for long operations)
- All file paths must be sanitized before passing to worker
- State mutations must be thread-safe

**Example of Safe Change:**
```python
# ✅ GOOD: Add new voice style selector to UI
ui.select('Voice Style', options=self.available_voices)

# ❌ BAD: Directly call synthesis in UI thread
wav_data = tts.synthesize(text)  # Blocks UI!
```

---

### 2. TTS Base Interface (audiopub/core/tts_base.py)

**Responsibility:**
- Define abstract interface that all TTS engines implement
- Ensure all engines have consistent methods
- Enable factory pattern for engine swapping

**Editable:** ❌ **LOCKED** (method signatures)

**Why Locked:**
- All TTS implementations inherit from this
- Changing method signatures breaks the factory pattern
- Breaks tts_factory.py instantiation logic
- Breaks worker.py's orchestration

**Cannot Edit:**
- Method signatures in TTSBase class
- Abstract method names
- Return types (unless all implementations updated simultaneously)

**Can Edit:**
- Docstrings and comments
- Add new abstract methods (if you update tts.py AND tts_neutts.py simultaneously)
- Add class-level configuration

**Example of Locked Code:**
```python
class TTSBase(ABC):
    @abstractmethod
    def synthesize(self, text: str) -> bytes:
        """Generate audio from text."""
        pass

    # ❌ DO NOT rename to generate_audio() or change return type
    # ❌ DO NOT remove this method
```

---

### 3. Supertone TTS Engine (audiopub/core/tts.py)

**Responsibility:**
- Load Supertone ONNX models from disk
- Manage voice style selection (JSON configs)
- Implement text-to-speech synthesis pipeline
- Handle GPU/CPU fallback gracefully
- Cache compiled ONNX sessions

**Editable:** ✅ Yes

**Can Edit:**
- Voice style loading and selection logic
- ONNX session caching
- GPU/CPU fallback behavior
- Error handling and logging
- Performance optimizations (e.g., batch processing)
- Add new voice styles (JSON files in audiopub/assets/voice_styles/)

**Cannot Edit:**
- ONNX model loading mechanism itself (affected by reproducibility)
- ONNX input/output names (tied to model structure)
- Voice style JSON schema (requires updating all existing voices)

**Key Invariants:**
- Voice styles are JSON files in `audiopub/assets/voice_styles/`
- GPU must have CPU fallback (never assume GPU is available)
- ONNX models must be loaded from Git LFS paths
- Synthesis must return WAV bytes, not file paths

**Testing:**
- Test on CPU (required)
- Test on GPU if you touch GPU code
- Verify all voice styles still load
- Ensure output WAV is valid (playable in standard player)

**Example of Safe Change:**
```python
# ✅ GOOD: Add performance optimization with fallback
if config.gpu_enabled:
    try:
        sess = ort.InferenceSession(model, providers=['CUDAExecutionProvider'])
    except Exception as e:
        logger.warning(f"GPU unavailable, using CPU: {e}")
        sess = ort.InferenceSession(model, providers=['CPUExecutionProvider'])
else:
    sess = ort.InferenceSession(model, providers=['CPUExecutionProvider'])

# ✅ GOOD: Add new voice style
# Create: audiopub/assets/voice_styles/F1_whisper.json

# ❌ BAD: Remove CPU fallback to simplify code
sess = ort.InferenceSession(model, providers=['CUDAExecutionProvider'])  # Breaks on non-GPU!
```

---

### 4. NeuTTS Air Engine (audiopub/core/tts_neutts.py)

**Responsibility:**
- Wrap Neuphonic NeuTTS Air API
- Support voice cloning from WAV samples
- Implement TTSBase interface
- Handle reference audio loading

**Editable:** ✅ Yes

**Can Edit:**
- Voice cloning parameters
- Reference audio management
- Performance optimizations
- Error handling

**Cannot Edit:**
- TTSBase method signatures (inherited from tts_base.py)

**Key Invariants:**
- Reference audio samples live in `audiopub/assets/reference_audio/`
- Must implement `synthesize()` from TTSBase

---

### 5. TTS Factory (audiopub/core/tts_factory.py)

**Responsibility:**
- Instantiate the correct TTS engine based on config
- Enable engine swapping without changing orchestration logic

**Editable:** ✅ Yes

**Can Edit:**
- Add new engine types
- Change factory logic
- Add engine validation

**Cannot Edit:**
- TTSBase interface (affects all engines)

**When Adding a New Engine:**
1. Subclass TTSBase in a new file (e.g., `tts_google.py`)
2. Register in TTSFactory.create()
3. Add to config.SUPPORTED_ENGINES
4. Test that factory instantiation works

---

### 6. EPUB Parser (audiopub/core/epub.py)

**Responsibility:**
- Parse EPUB file structure (ZIP + OPF manifest)
- Extract text from XHTML chapters
- Identify chapter boundaries
- Preserve metadata (title, author)
- Clean text (strip HTML, normalize quotes)

**Editable:** ✅ Yes

**Can Edit:**
- Text cleaning logic
- Special character handling
- Performance optimizations
- Error handling for malformed EPUBs
- Testing diverse EPUB formats

**Cannot Edit:**
- Chapter boundary detection logic (affects user experience and metadata accuracy)

**Key Invariants:**
- Chapter boundaries must be semantically correct (match user expectation)
- Extracted text must be valid UTF-8
- Metadata must survive parsing

**Testing:**
- Test with diverse EPUB formats (multiple publishers)
- Verify chapter boundaries are accurate
- Check that text is readable (no HTML remnants)

**Example of Safe Change:**
```python
# ✅ GOOD: Improve text cleaning
text = text.replace('\u201c', '"')  # Smart quotes → straight quotes
text = text.replace('  ', ' ')      # Normalize whitespace

# ❌ BAD: Change chapter detection without testing
# (This would break chapter metadata!)
```

---

### 7. Audio Processing & M4B Assembly (audiopub/core/audio.py)

**Responsibility:**
- Split text into chunks (sentence-level, NLTK)
- Pad chapters with 5-second silence
- Mix and concatenate WAV files
- Embed chapter metadata (ID3v2 tags)
- Mux WAV → M4B via ffmpeg
- Handle audio compression and bit rates

**Editable:** ✅ Yes (with caution)

**Can Edit:**
- Chunk size and chunking algorithm (if it preserves chapter structure)
- Silence duration (if added as configurable parameter)
- Audio mixing and concatenation logic
- Metadata embedding
- Performance optimizations

**Cannot Edit:**
- M4B output format (user-facing contract)
- Chapter silence duration (5s) without good reason + testing

**Key Invariants:**
- Chapter metadata must survive M4B muxing
- Output M4B must be playable in standard audiobook player
- Chunk boundaries should align with semantic units (sentences)

**Testing:**
- Verify output M4B plays in iOS Books, Android Play Books, or similar
- Verify chapter marks are accurate
- Test with chapters of varying lengths
- Ensure no audio is lost during muxing

**Example:**
```python
# ✅ GOOD: Make silence duration configurable
silence_duration = config.chapter_silence_seconds  # Default 5.0

# ⚠️ RISKY: Change silence duration without testing
add_silence(chapter, 2.0)  # Might make chapters feel rushed!
```

---

### 8. Worker Orchestration (audiopub/core/worker.py)

**Responsibility:**
- Coordinate the entire EPUB → M4B pipeline
- Run in separate thread (non-blocking UI)
- Handle interruption signals (stop synthesis)
- Manage error recovery
- Report progress to main UI

**Editable:** ✅ Yes

**Can Edit:**
- Error handling and recovery
- Progress reporting
- Performance optimizations
- Logging and diagnostics
- Retry logic

**Cannot Edit:**
- Interrupt/stop logic (affects user control)
- Operation order (EPUB → chunks → TTS → assembly)

**Key Invariants:**
- Must be interruptible (respect user "stop" signal)
- Must handle graceful degradation (skip chunk on error, continue)

---

### 9. Configuration (audiopub/config.py)

**Responsibility:**
- Centralized settings for paths, TTS parameters, GPU settings
- Default values that enable offline, CPU-only operation
- Environment variable overrides

**Editable:** ✅ Yes

**Can Edit:**
- Add new optional parameters (with sensible defaults)
- Add environment variable support
- Refactor config organization

**Cannot Edit:**
- Remove offline operation capability
- Require cloud API keys as default

**Key Invariant:**
- Default config must allow offline CPU-only operation

---

## Failure Modes & Recovery

| Failure | Handler | Behavior |
|---------|---------|----------|
| EPUB parse error (malformed ZIP) | epub.py try/except | Show user "Invalid EPUB: try re-downloading" |
| EPUB parse error (missing OPF) | epub.py try/except | Show user "EPUB structure not recognized" |
| TTS model missing | tts.py on first init | Attempt Git LFS pull or show download link |
| GPU out of memory | tts.py catch | Fall back to CPU + log warning |
| Chunk synthesis fails (TTS error) | worker.py catch | Skip chunk, continue synthesis (lossy recovery) |
| Audio chunk is corrupted | audio.py catch | Replace with silence, log warning |
| M4B muxing fails (ffmpeg error) | audio.py catch | Offer WAV output as fallback or retry |
| Worker interrupted by user | worker.py check signal | Clean up, stop synthesis, close temp files |

---

## Dependency Graph

```
config.py (0 dependencies, imported everywhere)
  ↑

tts_base.py (0 dependencies, abstract interface)
  ↑ ↑
  │ └── tts.py (depends on: onnxruntime, numpy)
  │
  └── tts_neutts.py (depends on: neuphonic, espeak)

tts_factory.py (depends on: tts.py, tts_neutts.py, config)
  ↑

worker.py (depends on: tts_factory, epub.py, audio.py, config)
  ↑

main.py (depends on: worker, config, file_picker, nicegui)
  ↓
file_picker.py (depends on: native OS dialog)

audio.py (depends on: pydub, soundfile, numpy, ffmpeg)
  ↑
  └── worker.py (calls audio.py functions)

epub.py (depends on: ebooklib, beautifulsoup4, nltk)
  ↑
  └── worker.py (calls epub.py functions)
```

### One-Way Dependencies (Safe)
- ✅ main.py calls worker.py (UI initiates work)
- ✅ worker.py calls epub.py, audio.py, tts_factory (orchestration)
- ✅ tts.py subclasses tts_base.py (implementation uses interface)
- ✅ tts_factory creates tts.py and tts_neutts.py instances

### Circular Dependencies (Must Never Create)
- ❌ worker.py should not import main.py (except for callbacks)
- ❌ tts.py should not import worker.py
- ❌ audio.py should not import main.py

---

## Module Boundaries

| Boundary | Responsibility | Policy |
|----------|-----------------|--------|
| **UI Layer** | main.py, file_picker.py | Free to change layout, add controls |
| **Pipeline Orchestration** | worker.py | Keep operation order; allow error handling refactors |
| **TTS Engines** | tts_base.py, tts.py, tts_neutts.py | Implement TTSBase contract; new engines welcome |
| **Data Processing** | epub.py, audio.py | Keep output format; optimize internals freely |
| **Configuration** | config.py | Add optional params; maintain offline defaults |

---

## Data Types & Contracts

### Text Chunk
```python
{
    'text': 'Sentence to synthesize.',
    'chapter_id': 0,
    'chunk_id': 0,
    'estimated_duration_ms': 2500,
}
```

### Synthesized Audio
```python
{
    'chunk_id': 0,
    'audio_bytes': b'\xff\xfb...',  # WAV PCM bytes
    'duration_ms': 2412,
    'sample_rate': 22050,
}
```

### Chapter Metadata
```python
{
    'chapter_id': 0,
    'title': 'Chapter 1: The Beginning',
    'start_time_ms': 0,
    'end_time_ms': 45000,
    'chunks': [chunk_data, ...],
}
```

---

## Key Files & Their Role

| File | Role | Editable? |
|------|------|-----------|
| audiopub/main.py | UI server & state | ✅ |
| audiopub/core/tts_base.py | TTS interface | ❌ |
| audiopub/core/tts.py | Supertone engine | ✅ |
| audiopub/core/tts_neutts.py | NeuTTS Air engine | ✅ |
| audiopub/core/tts_factory.py | Engine factory | ✅ |
| audiopub/core/epub.py | EPUB parsing | ✅ |
| audiopub/core/audio.py | Audio assembly | ✅ |
| audiopub/core/worker.py | Orchestration | ✅ |
| audiopub/config.py | Configuration | ✅ |
| audiopub/file_picker.py | File selection | ✅ |

---

## Performance Considerations

### Current Bottlenecks
1. **ONNX inference:** Slow on CPU, fast on GPU (~3-5x speedup)
2. **ffmpeg muxing:** Slow for large audiobooks (30+ min)
3. **Text encoding:** NLTK sentence tokenization is O(n)

### Optimization Opportunities
- Batch ONNX inference (multiple chunks per forward pass)
- Parallel chapter synthesis (thread-safe TTS session)
- Cache compiled ONNX sessions
- Pre-compute sentence boundaries during EPUB parse

### GPU Memory Constraints
- ONNX models: ~200-500 MB on GPU
- Batch size tuning: Trade synthesis speed vs. memory
- Fallback: CPU inference if GPU OOM

---

## Testing Strategy

For any change to the core pipeline:

1. **CPU test** (required): Code must run on CPU alone
2. **GPU test** (if touching GPU code): Code must work on GPU
3. **Format test** (if touching audio/EPUB): Verify chapter metadata survives
4. **Regression test** (optional): Run on 1-2 sample EPUBs

See AGENT_GUIDE.md for detailed testing checklist.

---

## Document History

- **Version 1.0** – Nov 2024 – Initial architecture document
