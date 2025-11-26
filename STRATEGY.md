# STRATEGY.md – Audiopub Project Philosophy & Constraints

## Project Vision

**Audiopub** converts ebooks (EPUB files) into high-fidelity audiobooks (M4B format) using on-device text-to-speech (TTS) engines. The application runs entirely locally—no cloud APIs, no per-character fees, no user tracking—making it ideal for privacy-conscious readers and those with offline needs.

### Core Value Proposition

- **Privacy First:** All TTS processing happens on-device. No text is ever sent to external servers.
- **Freedom from Fees:** No per-character charges, no subscription models. Process unlimited books locally.
- **Offline Capability:** Works completely offline after model download. No internet required during use.
- **Quality & Control:** Support for multiple TTS engines with configurable voice styles and GPU acceleration.

### Target Users

- Privacy-conscious readers who distrust cloud TTS services
- Users in regions with limited/expensive internet access
- Developers building local audiobook workflows
- Accessibility advocates who want control over their content

---

## Non-Negotiable Constraints

These constraints define the project's boundaries. **Violating any of these requires explicit discussion and decision-making, not unilateral changes.**

### 1. Local-First Architecture
- **Rule:** All TTS processing happens on-device.
- **Implication:** Never propose cloud TTS integration as a primary solution.
- **Exception:** Optional cloud engines are acceptable *if* they are:
  - Explicitly disabled by default
  - Marked as experimental/optional
  - Documented with privacy trade-offs
  - Implemented as a separate, non-interfering module

### 2. ONNX Runtime Dependency
- **Rule:** All neural models must run through ONNX Runtime.
- **Rationale:** ONNX provides cross-platform compatibility, smaller runtime footprint, and hardware flexibility (CPU, GPU, NPU).
- **Implication:** Do not propose PyTorch, TensorFlow, or other large runtime dependencies as replacements.
- **Extension:** GPU support (CUDA, OpenCL) is encouraged within ONNX constraints.

### 3. GPU Optional (Not Required)
- **Rule:** The application must work on CPU alone. GPU is an optimization, never a requirement.
- **Implication:** Every code path must have a CPU fallback.
- **Example:**
  ```python
  # ✅ GOOD: Fallback to CPU if GPU unavailable
  try:
      sess = ort.InferenceSession(model, providers=['CUDAExecutionProvider'])
  except Exception:
      logger.warning("GPU not available, using CPU")
      sess = ort.InferenceSession(model, providers=['CPUExecutionProvider'])

  # ❌ BAD: Assumes GPU is available
  sess = ort.InferenceSession(model, providers=['CUDAExecutionProvider'])
  ```

### 4. Pluggable TTS Engines
- **Rule:** All TTS engines must inherit from `tts_base.py::TTSBase`.
- **Rationale:** This enables swapping engines without changing orchestration logic (factory pattern).
- **Implication:** The `TTSBase` interface is sacred—method signatures cannot change without major version bump.
- **Extension:** New engines are welcome if they respect this contract.

### 5. M4B as Primary Output Format
- **Rule:** The default and recommended output format is M4B (MPEG-4 with chapter markers).
- **Rationale:** M4B preserves chapter metadata, is widely supported, and is the standard for audiobooks.
- **Implication:** Do not change the muxing format without explicit discussion.
- **Extension:** Fallback to WAV is acceptable for debugging/intermediate stages.

### 6. No Telemetry or Analytics
- **Rule:** No user tracking, telemetry, crash reporting, or analytics collection.
- **Rationale:** Core commitment to privacy.
- **Implication:** All I/O is local or explicitly documented.
- **Auditing:** Any new network call must be added to a visible PRIVACY_LOG or similar.

---

## Historical Decisions & Rationale

Understanding *why* decisions were made helps agents propose appropriate changes.

### Why ONNX over PyTorch or TensorFlow?
- **PyTorch:** ~500MB runtime, heavy GPU dependencies, overkill for inference-only use case.
- **TensorFlow:** Similar size, Java dependency via TFLite, complex installation.
- **ONNX:** ~50MB, cross-platform, optimized for inference, first-class edge support.
- **Decision made:** Phase 1 (Foundation)
- **Revisit if:** A new model format becomes dominant and ONNX integration becomes a bottleneck.

### Why NiceGUI?
- **Django/Flask:** Require Node.js/npm; too much overhead for desktop app.
- **Qt/Tkinter:** Python bindings are fragile; poor cross-platform support.
- **NiceGUI:** Pure Python, built-in elements, no JavaScript knowledge needed.
- **Decision made:** Phase 2 (UI & UX)
- **Revisit if:** NiceGUI becomes unmaintained or fails to support required UI patterns.

### Why M4B Format?
- **MP3:** No chapter support; deprecated for audiobooks.
- **OGG:** Poor chapter metadata support; less universal player compatibility.
- **FLAC:** Excellent quality but file size prohibitive for long books.
- **M4B:** Standard audiobook format, chapter markers preserved in metadata, reasonable file size.
- **Decision made:** Phase 1 (Foundation)
- **Revisit if:** A more universal format emerges with better metadata support.

### Why Sentence-Level Chunking?
- **Word-level:** Too many short chunks; latency issues; poor synthesis quality.
- **Paragraph-level:** Too few chunks; memory pressure; long synthesis times.
- **Sentence-level:** Balanced latency, quality, and memory; matches natural pacing.
- **Decision made:** Phase 1 (Foundation)
- **Revisit if:** GPU memory constraints change or streaming playback becomes a goal.

### Why Supertone as Primary Engine?
- **Supertone:** Diffusion-based TTS; high quality; ONNX-friendly; voice style support.
- **NeuTTS Air:** Fast, supports voice cloning; added as alternative in Phase 3.
- **Decision made:** Phase 1 (Foundation)
- **Revisit if:** Quality benchmarks show a better alternative or licensing changes.

### Why GPU Acceleration is Optional?
- **CPU-first design:** Ensures offline, low-power devices work.
- **GPU-optional:** Allows users with GPUs to speed up synthesis 3-5x.
- **Fallback:** If GPU fails, no crash—just slower synthesis.
- **Decision made:** Phase 3 (Engine Flexibility)
- **Revisit if:** GPU becomes standard on all devices, or mobile support becomes a priority.

---

## Acceptable Scope Extensions

The project can expand in these directions **without requiring strategy discussion:**

- **New TTS Engines:** If they subclass `TTSBase` and don't require cloud APIs.
- **GPU Acceleration:** New optimization techniques, CUDA kernels, inference pipeline improvements.
- **Voice Styles:** New JSON voice configuration files.
- **UI Improvements:** Layout, controls, user experience (without adding heavy dependencies).
- **Performance Optimizations:** Caching, vectorization, faster parsing (without breaking output).
- **Testing & Tooling:** Unit tests, benchmarking, debugging tools, verification scripts.
- **Documentation:** Guides, API docs, examples.

---

## Explicitly Out of Scope

These should **not** be proposed without major discussion:

- **Cloud TTS Integration** (as primary solution): Violates local-first principle.
- **Telemetry or Analytics:** Violates privacy commitment.
- **DRM or Copy Protection:** Antithetical to open, local-first design.
- **Streaming Playback:** App focus is generation, not playback. Use external players.
- **Web Service Deployment:** App is desktop-focused. (API extraction might be future work.)
- **Mobile Ports:** Requires total architecture rewrite; outside current scope.
- **Commercial Licensing:** Project is MIT-licensed; no commercial add-ons in core.

---

## Extension Approval Process

When proposing an extension **outside** the "acceptable scope" but not in "out of scope":

1. **Document the proposal** in an issue or PR description.
2. **Explain the change:**
   - Why does Audiopub need this?
   - Does it violate any non-negotiable constraints?
   - What's the privacy/dependency impact?
3. **Get approval** from the project maintainer (you) before implementing.
4. **Update this document** if the proposal is approved, so future agents know the decision.

---

## Privacy Principles

All changes must respect these principles:

1. **Data Minimization:** Only process data necessary for audiobook generation.
2. **No Tracking:** No device fingerprinting, analytics, or usage tracking.
3. **Transparent I/O:** All network calls (if any) must be opt-in and documented.
4. **User Control:** Settings must default to most private option.
5. **Open Source:** Code is auditable; no hidden behaviors.

---

## Version & Maintenance

- **Current Version:** 1.0.0
- **Python:** 3.9+
- **License:** MIT
- **Maintenance:** Active (as of Nov 2024)
- **Decision-Maker:** Project maintainer (personal project, reviews as needed)

---

## Questions This Document Answers for Agents

- **Q: Can I add a cloud TTS engine?**
  A: Only as an optional, explicitly disabled module. Local-first is non-negotiable.

- **Q: Can I replace ONNX with PyTorch?**
  A: No. ONNX is locked for cross-platform, lightweight inference.

- **Q: Can I remove CPU support to simplify GPU code?**
  A: No. CPU fallback is non-negotiable.

- **Q: Can I add telemetry to improve the app?**
  A: No. Privacy is a core value, not negotiable.

- **Q: Can I add a new voice style?**
  A: Yes! Add a JSON file to `audiopub/assets/voice_styles/`. No approval needed.

- **Q: Can I change the M4B format?**
  A: Only for good reason, discussed explicitly. Output format is user-facing.

- **Q: Can I add TypeScript/JavaScript?**
  A: No. App is Python-first to keep deployment simple.

---

## Document History

- **Version 1.0** – Nov 2024 – Initial strategy document
- **Next Review:** Q1 2025 or after major decision changes
