# ROADMAP.md – Phase Planning & Feature Tracking

This document tracks completed work, in-progress tasks, and planned features. It helps AI agents understand what's been done and what's blocked.

---

## Status Legend

- 🟢 **Done** – Shipped, tested, documented, merged to main
- 🟡 **In Progress** – Active development, may be incomplete
- 🔵 **Planned** – Approved for development, awaiting resources
- ⚫ **Blocked** – Cannot proceed without external dependency or decision
- ❌ **Rejected** – Decided against; reasoning documented

---

## Phase 1: Foundation (🟢 Done)

**Goal:** Core EPUB-to-M4B conversion pipeline

**Completed Items:**
- [x] EPUB parsing with chapter detection (ebooklib + BeautifulSoup)
- [x] Supertone ONNX model integration (text_encoder, duration_predictor, tts, vocoder)
- [x] Sentence-level text chunking (NLTK)
- [x] WAV synthesis and concatenation (pydub, soundfile)
- [x] Chapter metadata embedding (ID3v2 tags)
- [x] M4B muxing via ffmpeg
- [x] Basic command-line interface

**Timeline:** Completed by Sept 2024

**Author(s):** Initial development team

**Key Files:**
- audiopub/core/epub.py
- audiopub/core/tts.py
- audiopub/core/audio.py
- audiopub/core/worker.py

---

## Phase 2: UI & UX (🟢 Done)

**Goal:** Web-based interface for ease of use

**Completed Items:**
- [x] NiceGUI web server (localhost:8000)
- [x] Dark mode with glassmorphism design
- [x] Native file picker (Windows, macOS, Linux)
- [x] Real-time synthesis progress bar
- [x] Live synthesis log display (terminal-style)
- [x] Voice style selector (5 default voices)
- [x] Inline audio preview player (play synthesis chunks)
- [x] Settings panel (GPU toggle, chunk size, etc.)
- [x] Download link after completion

**Timeline:** Completed by Oct 2024

**Author(s):** UI development team

**Key Files:**
- audiopub/main.py
- audiopub/file_picker.py

---

## Phase 3: Engine Flexibility (🟢 Done)

**Goal:** Support multiple TTS engines and hardware acceleration

**Completed Items:**
- [x] Abstract TTS interface (TTSBase in tts_base.py)
- [x] Factory pattern for engine instantiation (tts_factory.py)
- [x] NeuTTS Air integration with voice cloning
- [x] GPU acceleration support (CUDA via ONNX Runtime)
- [x] Graceful fallback to CPU if GPU unavailable
- [x] Voice style system (5 pre-configured voices)
- [x] Deep female voice style (F1_deep_female)
- [x] Configurable inference steps (TTS model speedup)

**Timeline:** Completed by Nov 2024

**Author(s):** Engine integration team

**Key Files:**
- audiopub/core/tts_base.py
- audiopub/core/tts.py
- audiopub/core/tts_neutts.py
- audiopub/core/tts_factory.py
- audiopub/assets/voice_styles/
- audiopub/config.py

**Commits:**
- `c330687` – Add NeuTTS Air as alternative TTS engine
- `6ccbf02` – Add GPU acceleration and configurable inference steps
- `910455a` – Add deep female voice style

---

## Phase 4: Performance & Optimization (🟡 In Progress)

**Goal:** Reduce synthesis time, optimize memory usage

**Completed Items:**
- [x] GPU benchmarking tool (benchmark_gpu.py)
- [x] ONNX inference optimization (configurable inference steps for speedup)
- [x] ONNX session caching (reuse compiled sessions)

**In-Progress Items:**
- [ ] **Batch inference for chapter-level parallelism**
  - Status: 🟡 Investigation phase
  - Proposal: Synthesize multiple chunks in parallel (thread pool or asyncio)
  - Challenge: Thread-safety of ONNX sessions needs review
  - Blocker: Requires architecture review for async/await patterns
  - Owner: TBD
  - Est. Effort: 2-3 weeks
  - Decision Needed: Should batch size be configurable or auto-tuned?

- [ ] **Model quantization (INT8 for smaller footprint)**
  - Status: 🔵 Not started
  - Proposal: Convert ONNX models to INT8 (8-bit integer)
  - Benefit: ~4x smaller model files, faster inference on CPU
  - Risk: Potential quality loss (needs benchmarking)
  - Owner: TBD
  - Est. Effort: 2-3 weeks
  - Decision Needed: Auto-quantize on first run, or user-selected?

- [ ] **Audio file format optimization**
  - Status: 🔵 Not started
  - Proposal: Use lower sample rates (16 kHz instead of 22.05 kHz) or bitrates
  - Benefit: Smaller output files
  - Risk: Potential quality loss
  - Owner: TBD

**Timeline:** Estimated completion Q4 2024 – Q1 2025

**Key Files:**
- benchmark_gpu.py
- audiopub/core/tts.py (caching)
- audiopub/config.py (inference steps)

---

## Phase 5: Robustness & Testing (🔵 Planned)

**Goal:** Comprehensive test coverage and error recovery

**Planned Items:**
- [ ] Unit tests for EPUB parser
  - Test diverse EPUB formats (multiple publishers, DRM-free)
  - Test malformed EPUB edge cases
  - Verify chapter detection accuracy

- [ ] Integration tests for full pipeline
  - EPUB → M4B with multiple engines (Supertone, NeuTTS Air)
  - Different chapter counts (1, 5, 50 chapters)
  - Various text lengths and languages

- [ ] GPU memory stress testing
  - Test with very large books
  - Test with multiple concurrent synthesis tasks
  - Verify graceful fallback to CPU on OOM

- [ ] Audio quality validation
  - Verify sample rate accuracy (22.05 kHz)
  - Check signal-to-noise ratio (SNR)
  - Ensure no clipping or distortion

- [ ] Error recovery testing
  - Resume from interruption (if EPUB very large, user can stop/resume)
  - Network failure recovery (if future cloud engines added)
  - Corrupted temporary file recovery

**Timeline:** Planned start Q1 2025

**Owner:** TBD

**Test Framework Recommendation:** pytest with fixtures for sample EPUBs

---

## Phase 6: Extended TTS Engines (🔵 Planned)

**Goal:** Support additional TTS providers as opt-in alternatives

**Planned Items:**
- [ ] **Google Cloud Text-to-Speech (Optional, Off by Default)**
  - Status: 🔵 Not started
  - Proposal: Add cloud-based TTS as alternative engine
  - **IMPORTANT:** Must respect local-first principle
    - Default disabled in config
    - Requires explicit user opt-in
    - Requires API key (not baked in)
    - Privacy disclaimer in UI
  - Benefit: High-quality voices, natural prosody
  - Risk: Cost, privacy exposure, internet dependency
  - Decision Needed: Include in main repo or separate plugin?

- [ ] **Microsoft Edge TTS (Windows-only, Offline)**
  - Status: 🔵 Not started
  - Proposal: Use Windows native TTS engine (no internet required)
  - Benefit: Fast, lightweight, no additional downloads
  - Platform: Windows only
  - Owner: TBD

- [ ] **ElevenLabs API (Optional, Off by Default)**
  - Status: 🔵 Not started
  - Proposal: Add cloud TTS as optional engine
  - Same privacy/opt-in constraints as Google Cloud
  - Decision Needed: Include in main repo or separate plugin?

**Timeline:** Planned Q1-Q2 2025

**Architecture Impact:**
- All engines must subclass TTSBase
- Factory pattern handles instantiation
- Config must have opt-in flags
- Privacy warning in UI if cloud engine selected

---

## Phase 7: User Experience (🔵 Planned)

**Goal:** Improve onboarding and usability

**Planned Items:**
- [ ] Config wizard for first-time setup
  - Detect GPU availability
  - Suggest settings based on system specs
  - Download ONNX models if missing

- [ ] Model download/cache manager UI
  - Show installed models
  - Allow cache clearing
  - Show model file sizes

- [ ] Audiobook player preview (native playback)
  - Play generated M4B directly in app
  - Jump to chapters
  - Show metadata (duration, bitrate, etc.)

- [ ] Batch conversion queue
  - Queue multiple EPUBs
  - Background processing
  - Pause/resume queue

**Timeline:** Planned Q2 2025

---

## Known Blockers & Decisions Needed

| Issue | Status | Details | Owner |
|-------|--------|---------|-------|
| **Batch inference parallelization** | 🟡 Investigating | Requires async/await refactor. How to share ONNX sessions across threads safely? | Engineering lead |
| **Model quantization** | 🔵 Planned | Should quantization be automatic on first run, or user-configurable? | ML/Architecture lead |
| **Cloud TTS engines** | 🔵 Planning | Should optional cloud engines be in main repo or separate plugins? | Product/Architecture |
| **Chapter silence duration** | 🟡 Considering | Current 5s gap. Users suggest 2s or configurable. Needs user testing. | Product |

---

## Rejected Ideas & Rationale

| Feature | Status | Why Rejected | Author | Date |
|---------|--------|-------------|--------|------|
| Streaming playback during synthesis | ❌ Rejected | Increases complexity significantly. App focus is generation, not playback. Users have many good audiobook players. | Product team | Nov 2024 |
| Web service deployment (HTTP API) | ❌ Rejected | Out of scope for privacy-first desktop tool. Could be revisited for future server-based product. | Architecture team | Oct 2024 |
| Mobile app (iOS/Android) | ❌ Rejected | Would require complete rewrite; not planned for desktop-focused product. | Leadership | Sept 2024 |
| Add telemetry for improvement | ❌ Rejected | Violates privacy-first principle. Users should not be tracked. | Privacy team | Sept 2024 |
| Support FLAC output | ❌ Rejected (for now) | File sizes are huge for audiobooks (2-3GB). M4B is standard and more efficient. Could revisit if user demand. | Product | Oct 2024 |
| Direct audiobook player integration | ❌ Rejected | Too many existing players (Apple Books, Audible, etc.). Better to output M4B and let users choose. | Product | Nov 2024 |

---

## Recent Commits (Context for Agents)

```
910455a - Title: Add deep female voice style and surface it in the UI
9745b96 - Merge pull request #4: GPU acceleration and configurable inference steps
6ccbf02 - Add GPU acceleration and configurable inference steps
5f01649 - Merge pull request #3: NeuTTS Air integration
c330687 - Add NeuTTS Air as alternative TTS engine with voice cloning
aead221 - New screenshot
24c1b02 - Add inline playback preview and per-voice temp isolation
0f52fe1 - Changes sample files
ddc5c8f - Fix chapter silence padding and metadata timing
aafda3d - Added proper 5s gap between chapters and aligned chapter markers
```

---

## How Agents Should Update This Document

When you complete work or discover new information:

1. **Move items between phases** only if you have explicit confirmation
2. **Update "In-Progress" items** with new findings
3. **Add new "Blocked" entries** if you discover blockers
4. **Do NOT remove items** – mark as rejected instead with reasoning
5. **Keep commit hashes** for traceability

**Example update:**
```markdown
- [x] Feature name
  - Status: ✅ Completed
  - Commit: abc1234
  - Notes: Works on CPU and GPU, tested with 5 sample EPUBs
```

---

## Maintenance Schedule

- **Last updated:** Nov 25, 2024
- **Next review:** Dec 9, 2024 (2 weeks)
- **Maintainer:** You (personal project, reviews as needed)

---

## Next Major Milestone

**Target:** Phase 4 completion (Performance optimization done)
**Focus:** Batch inference and model quantization
**Estimated:** Q1 2025

---

## Document History

- **Version 1.0** – Nov 2024 – Initial roadmap with 7 phases
