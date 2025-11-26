# ENTRYPOINTS.md – Module Map & Data Flow

This document shows where users enter the system, how modules interact, and how data flows through the pipeline.

---

## Entry Points: How Users Invoke the System

### 1. Web UI (Primary)

**Invoked by:** `python audiopub/main.py`

**What happens:**
1. NiceGUI server starts on `localhost:8000`
2. User opens browser to `http://localhost:8000`
3. User selects EPUB file via file picker
4. User clicks "Convert" button
5. `main.py::on_convert_clicked()` spawns worker thread
6. Worker processes EPUB → M4B
7. UI shows download link when complete

**Files involved:**
- `audiopub/main.py` – UI orchestration
- `audiopub/file_picker.py` – Native file selection dialog
- `audiopub/core/worker.py` – Async synthesis pipeline

---

### 2. GPU Benchmarking (Utility)

**Invoked by:** `python benchmark_gpu.py`

**What happens:**
1. Load Supertone ONNX models
2. Synthesize a test text chunk on GPU
3. Measure time: GPU inference vs. CPU inference
4. Print speedup factor

**Files involved:**
- `benchmark_gpu.py` – Standalone script
- `audiopub/core/tts.py` – TTS engine
- `audiopub/config.py` – Settings

---

### 3. Frontend Verification (Testing)

**Invoked by:** `python verify_frontend.py`

**What happens:**
1. Basic smoke tests of UI components
2. Verify file picker works
3. Verify settings load correctly

**Files involved:**
- `verify_frontend.py` – Standalone script
- `audiopub/main.py` – UI components

---

## Module Call Graph

```
┌─────────────────────────────────────────────────────────────┐
│                   main.py (Web Server)                      │
│  • NiceGUI app initialization                               │
│  • UI state management (file select, progress, settings)    │
│  • Thread synchronization with worker                       │
└──────────────────┬──────────────────────────────────────────┘
                   │ spawns async task
                   ▼
        ┌──────────────────────┐
        │ file_picker.py       │
        │ Native file dialog   │
        └──────────────────────┘

       ┌────────────────────────────────────────┐
       │ worker.py (Worker Thread)              │
       │ • Orchestrates EPUB → M4B pipeline    │
       │ • Coordinates all steps                │
       │ • Handles interrupts (stop signal)    │
       └───────────┬─────────────────────────┬──┘
                   │                         │
          ┌────────▼────────┐    ┌──────────▼────────┐
          │ epub.py         │    │ tts_factory.py    │
          │ EPUB parsing    │    │ Engine factory    │
          │ • Unzip EPUB    │    │ • Instantiate TTS │
          │ • Parse OPF     │    │ • Select engine   │
          │ • Extract text  │    └────────┬──────────┘
          │ • Find chapters │             │
          └────────┬────────┘         ┌───┴────────┬──────────┐
                   │                  │            │          │
                   │          ┌───────▼────────┐  │          │
                   │          │ tts.py         │  │          │
                   │          │ Supertone TTS  │  │    ┌─────▼───────┐
                   │          │ • Load models  │  │    │ tts_neutts  │
                   │          │ • Synthesize   │  │    │ NeuTTS Air  │
                   │          │ • Voice styles │  │    └─────────────┘
                   │          └───────────────┘  │
                   │                             │
                   │                 ┌───────────▼──────┐
                   │                 │ tts_base.py      │
                   │                 │ Abstract class   │
                   │                 │ (inherited by    │
                   │                 │  tts.py and      │
                   │                 │  tts_neutts.py)  │
                   │                 └──────────────────┘
                   │
          ┌────────▼────────────────────┐
          │ audio.py                     │
          │ Audio Assembly & M4B Muxing  │
          │ • Text chunking (NLTK)       │
          │ • Parallel WAV generation    │
          │ • Silence padding            │
          │ • Chapter metadata embedding │
          │ • M4B muxing (ffmpeg)       │
          └────────┬─────────────────────┘
                   │
                   ▼
        ┌──────────────────────┐
        │ output/              │
        │ {book_name}.m4b      │
        └──────────────────────┘
```

**Key dependency:** All modules depend on `config.py` (shared configuration)

---

## Data Flow: User Uploads EPUB → M4B Output

### Step 1: File Upload to Worker

```
User selects EPUB in web UI
  ↓
main.py::on_convert_clicked()
  ↓
Validate file path (sanitized)
  ↓
worker.convert_epub_to_m4b(epub_path, config)
  ↓
Worker thread spawned
```

**Data:**
- Input: EPUB file path (string)
- Output: M4B file path (string)

---

### Step 2: EPUB Parsing

```
epub.py::parse_epub(epub_path)
  ↓
1. Unzip EPUB container
2. Parse OPF manifest (table of contents)
3. Extract XHTML chapter files
4. For each chapter:
   - Parse HTML with BeautifulSoup
   - Extract text nodes
   - Identify chapter boundaries (nav, h1, etc.)
  ↓
Return: Chapters with metadata
```

**Data returned:**
```python
chapters = [
    {
        'chapter_id': 0,
        'title': 'Chapter 1: The Beginning',
        'text': 'Long chapter text...',
        'word_count': 2500,
    },
    {
        'chapter_id': 1,
        'title': 'Chapter 2: The Middle',
        'text': 'More text...',
        'word_count': 3100,
    },
    ...
]
```

---

### Step 3: Text Chunking

```
audio.py::chunk_text(chapter_text)
  ↓
1. Split by sentences (NLTK sentence tokenizer)
2. Group by paragraphs for pacing
3. Estimate synthesis duration (tokens × avg_ms_per_token)
4. Estimate TTS time budget
  ↓
Return: List of text chunks
```

**Data returned:**
```python
chunks = [
    {
        'chunk_id': 0,
        'chapter_id': 0,
        'text': 'First sentence of the chapter.',
        'token_count': 12,
        'estimated_duration_ms': 2400,
    },
    {
        'chunk_id': 1,
        'chapter_id': 0,
        'text': 'Second sentence. Third sentence.',
        'token_count': 10,
        'estimated_duration_ms': 2000,
    },
    ...
]
```

---

### Step 4: TTS Engine Selection

```
tts_factory.py::TTSFactory.create(config.tts_engine)
  ↓
Based on config.tts_engine:
  - 'supertone' → tts.Supertone(config)
  - 'neutts_air' → tts_neutts.NeuTTSAir(config)
  ↓
Load ONNX models (if Supertone) or API keys (if NeuTTS Air)
  ↓
Return: TTS engine instance (subclass of TTSBase)
```

**Flow:**
1. TTS factory instantiates the selected engine
2. Engine loads models/resources
3. Engine ready for synthesis

---

### Step 5: TTS Synthesis (Per Chunk)

```
For each chunk in chunks:
  ↓
  tts.synthesize(chunk['text'])
    ↓
    [Supertone pipeline]
    1. Text → Tokens (text encoder ONNX)
    2. Tokens → Duration (duration predictor ONNX)
    3. Tokens + Duration → Mel-spec (TTS model ONNX)
    4. Mel-spec → PCM waveform (vocoder ONNX)
    ↓
    Return: WAV bytes (PCM audio)
```

**Data returned:**
```python
wav_bytes = b'\xff\xfb...'  # 44.1 kHz, 16-bit, mono
duration_ms = 2412
sample_rate = 22050
```

**GPU Fallback:**
- If GPU enabled, try CUDA execution provider
- If GPU unavailable, silently fall back to CPU
- Log warning for debugging

---

### Step 6: Audio Assembly (Per Chapter)

```
For each chapter:
  ↓
  1. Concatenate all chunk WAVs
  2. Add 5-second silence gap
  3. Embed chapter metadata (ID3v2 tags):
     - Chapter title
     - Chapter start/end time
  ↓
  Return: Chapter audio with metadata
```

**Data structure:**
```python
chapter_audio = {
    'chapter_id': 0,
    'title': 'Chapter 1: The Beginning',
    'wav_bytes': b'...',  # Concatenated WAV
    'duration_ms': 45000,
    'metadata_tags': {
        'TIT2': 'Chapter 1: The Beginning',
        'TXXX:ChapterNumber': '1',
    }
}
```

---

### Step 7: Audio Muxing to M4B

```
audio.py::create_m4b(all_chapter_audio, metadata)
  ↓
1. Concatenate all chapter WAVs with silence gaps
2. Create temp WAV file
3. Encode WAV → AAC using ffmpeg:
   ffmpeg -i temp.wav -c:a aac -b:a 128k output.m4b
4. Embed chapter marks in M4B:
   - Read chapter metadata
   - Write iTuneSMPB atoms (chapter times)
5. Embed artwork & metadata:
   - Title, author, ISBN (if available)
   - Cover image (from EPUB)
6. Clean up temp files
  ↓
Return: M4B file path
```

**Output:** `/mnt/Games/Audiopub/output/{book_name}.m4b`

---

### Step 8: Serve to User

```
M4B file created successfully
  ↓
main.py receives completion signal
  ↓
Generate download link
  ↓
UI shows "Download ready" button
  ↓
User clicks, downloads {book_name}.m4b
```

---

## Complete Data Flow Diagram

```
┌──────────────────────────────────────────────────────────────────────┐
│ STEP 1: FILE UPLOAD                                                  │
│ User selects: /path/to/book.epub                                     │
└────────────────────┬─────────────────────────────────────────────────┘
                     ▼
┌──────────────────────────────────────────────────────────────────────┐
│ STEP 2: EPUB PARSING (epub.py)                                       │
│ Output: [Chapter, Chapter, Chapter...]                               │
│   ├─ Chapter 1: {id: 0, title: "Ch1", text: "..."}                   │
│   ├─ Chapter 2: {id: 1, title: "Ch2", text: "..."}                   │
│   └─ Chapter 3: {id: 2, title: "Ch3", text: "..."}                   │
└────────────────────┬─────────────────────────────────────────────────┘
                     ▼
┌──────────────────────────────────────────────────────────────────────┐
│ STEP 3: TEXT CHUNKING (audio.py)                                     │
│ Output: [Chunk, Chunk, Chunk, ...]                                   │
│   ├─ Chunk 0: {chapter: 0, text: "Sent 1.", est_ms: 2400}            │
│   ├─ Chunk 1: {chapter: 0, text: "Sent 2. Sent 3.", est_ms: 2000}    │
│   ├─ Chunk 2: {chapter: 1, text: "New chapter...", est_ms: 2300}     │
│   └─ Chunk 3: {chapter: 1, text: "...", est_ms: 2200}                │
└────────────────────┬─────────────────────────────────────────────────┘
                     ▼
┌──────────────────────────────────────────────────────────────────────┐
│ STEP 4: TTS SYNTHESIS (tts.py or tts_neutts.py)                      │
│ For each chunk: text → WAV bytes                                      │
│ Output: [WAV, WAV, WAV, ...]                                          │
│   ├─ WAV 0: {chunk: 0, bytes: b'...', duration_ms: 2412}             │
│   ├─ WAV 1: {chunk: 1, bytes: b'...', duration_ms: 1998}             │
│   ├─ WAV 2: {chunk: 2, bytes: b'...', duration_ms: 2289}             │
│   └─ WAV 3: {chunk: 3, bytes: b'...', duration_ms: 2198}             │
└────────────────────┬─────────────────────────────────────────────────┘
                     ▼
┌──────────────────────────────────────────────────────────────────────┐
│ STEP 5: AUDIO ASSEMBLY (audio.py)                                    │
│ Concatenate WAVs per chapter + 5s silence                             │
│ Output: [ChapterAudio, ChapterAudio, ChapterAudio]                    │
│   ├─ Chapter 0: {wav: b'...', duration_ms: 45000, title: "Ch1"}      │
│   ├─ Chapter 1: {wav: b'...', duration_ms: 51000, title: "Ch2"}      │
│   └─ Chapter 2: {wav: b'...', duration_ms: 38000, title: "Ch3"}      │
└────────────────────┬─────────────────────────────────────────────────┘
                     ▼
┌──────────────────────────────────────────────────────────────────────┐
│ STEP 6: M4B MUXING (audio.py via ffmpeg)                             │
│ Encode WAV → AAC, embed chapter metadata, add artwork                 │
│ Output: output/book_title.m4b                                         │
└────────────────────┬─────────────────────────────────────────────────┘
                     ▼
┌──────────────────────────────────────────────────────────────────────┐
│ STEP 7: DOWNLOAD (main.py)                                           │
│ User clicks download link, receives M4B file                          │
└──────────────────────────────────────────────────────────────────────┘
```

---

## Dependency Invariants: What Must Never Happen

### ❌ Circular Dependencies

These would create infinite loops or unclear dependencies:
- `tts.py` must NOT import from `worker.py`
- `audio.py` must NOT import from `main.py`
- `epub.py` must NOT import from `audio.py` (unidirectional only)
- `worker.py` must NOT import from `main.py` (except for callbacks)

### ✅ One-Way Dependencies (Safe)

These create a clean flow:
- `main.py` imports `worker.py` (UI calls worker)
- `worker.py` imports `epub.py`, `audio.py`, `tts_factory.py` (orchestration calls components)
- `tts.py` imports `tts_base.py` (implementation uses interface)
- All modules import `config.py` (shared configuration)

### How to Verify

When adding an import:
```python
# ❌ BAD: Create circular dependency
# audio.py imports worker
import worker  # Now audio.py depends on worker
               # But worker already depends on audio!

# ✅ GOOD: One-way flow
# audio.py provides functions
# worker.py calls audio functions
```

---

## Module Responsibility Checklist

Before editing a module, verify:

| Module | Responsibility | ✓ Verify |
|--------|-----------------|----------|
| main.py | UI & event handling | No blocking calls; thread-safe |
| worker.py | Orchestrate pipeline | Respects interrupt signal |
| epub.py | Parse EPUB structure | Detects chapters correctly |
| audio.py | Chunk text, assemble audio | Preserves metadata in M4B |
| tts.py | Supertone synthesis | GPU has CPU fallback |
| config.py | Centralized settings | Allows offline operation |

---

## Tracing a User Action: Complete Example

**User Action:** "Convert book.epub with Supertone engine"

**Call Trace:**

1. `main.py::on_convert_clicked()`
   - User clicks "Convert" button
   - Handler validates EPUB path
   - Spawns worker thread

2. `worker.py::Worker.run()`
   - Starts async task
   - Calls `epub.parse_epub(epub_path)`

3. `epub.py::parse_epub()`
   - Unzips EPUB
   - Parses OPF manifest
   - Extracts text from XHTML
   - Returns: `[Chapter(id=0, title="...", text="..."), ...]`

4. `worker.py::Worker.run()` (continues)
   - Calls `tts_factory.TTSFactory.create(config.tts_engine)`

5. `tts_factory.py::TTSFactory.create()`
   - config.tts_engine = 'supertone'
   - Returns: `Supertone(config)` instance

6. `worker.py::Worker.run()` (continues, for each chapter)
   - Calls `audio.chunk_text(chapter.text)`

7. `audio.py::chunk_text()`
   - Tokenizes text with NLTK
   - Groups by sentences/paragraphs
   - Returns: `[Chunk(id=0, text="...", est_ms=...), ...]`

8. `worker.py::Worker.run()` (continues, for each chunk)
   - Calls `tts.synthesize(chunk.text)`

9. `tts.py::Supertone.synthesize()`
   - Loads ONNX models (first run only, cached after)
   - Encodes text → tokens (text_encoder ONNX)
   - Predicts duration (duration_predictor ONNX)
   - Generates mel-spectrogram (tts ONNX)
   - Vocodes to PCM (vocoder ONNX)
   - Returns: WAV bytes

10. `worker.py::Worker.run()` (continues)
    - Calls `audio.assemble_audio(all_chapter_audio)`

11. `audio.py::assemble_audio()`
    - Concatenates chapter WAVs
    - Adds 5s silence between chapters
    - Embeds chapter metadata (ID3v2)
    - Calls `audio.create_m4b(assembled_wav, metadata)`

12. `audio.py::create_m4b()`
    - Encodes WAV → AAC (ffmpeg)
    - Embeds chapter marks
    - Writes to `output/book_title.m4b`
    - Returns: M4B file path

13. `main.py` (receives completion signal)
    - Shows "Download ready" button
    - User clicks, downloads M4B file

**Total modules involved:** 7 (main, worker, epub, audio, tts, tts_factory, config)
**Total I/O steps:** 2 (EPUB input, M4B output)
**Total synthesis steps:** Chunks × TTS models (typically 20-50 chunks = 80-200 ONNX invocations)

---

## Performance Paths

### CPU Path (Default)
```
EPUB → Chunks → TTS (CPU) → Audio (CPU) → ffmpeg (encode) → M4B
Typical: 5-20 min for 50k-word book
```

### GPU Path (Optimized)
```
EPUB → Chunks → TTS (GPU) → Audio (CPU) → ffmpeg (encode) → M4B
Typical: 1-5 min for 50k-word book (3-5x faster)
```

### Fallback Path (GPU OOM)
```
GPU synthesis starts → GPU OOM → Fall back to CPU (mid-synthesis)
Note: This is NOT ideal but doesn't crash the app
```

---

## Error Recovery Paths

| Error | Handling | Result |
|-------|----------|--------|
| EPUB parse fails | Catch, show "Invalid EPUB" | User re-downloads |
| ONNX model missing | Try Git LFS pull on first init | User runs setup |
| Chunk synthesis fails | Skip, continue with next | Lossy (missing audio) |
| M4B muxing fails | Offer WAV fallback | User has intermediate file |
| GPU OOM mid-synthesis | Fall back to CPU | Synthesis continues (slow) |
| User clicks "Stop" | Check interrupt signal | Clean exit, temp cleanup |

---

## Document History

- **Version 1.0** – Nov 2024 – Entry points and data flow documentation
