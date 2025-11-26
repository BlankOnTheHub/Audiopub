# AGENT_GUIDE.md – Rules & Operating Procedures for AI Agents

This document tells you exactly how to work on the Audiopub codebase safely. Read it before making any changes.

---

## Before Making ANY Change: A Checklist

1. **Read the relevant section of ARCHITECTURE.md**
   - Understand which module you're editing
   - Check if it's marked "Editable: ✅" or "Editable: ❌"

2. **Verify the file is not locked**
   - If "Cannot Edit" is listed, ask the human before proceeding
   - Some files like tts_base.py are locked for architectural reasons

3. **Check for invariants that must be preserved**
   - See ARCHITECTURE.md for each module's "Key Invariants"
   - Examples: Chapter boundaries must be accurate, CPU fallback must work, M4B format must be valid

4. **Write a reasoning comment in your code**
   - Explain why the change is safe
   - Document what invariants you preserved
   - See examples below

5. **Run the test checklist**
   - Before committing, verify your change passes all requirements
   - See "Testing Checklist" section below

---

## Coding Conventions

### Naming Conventions

**Classes:**
- TTS engine classes: `Supertone`, `NeuTTSAir` (PascalCase)
- Abstract/base classes: `TTSBase`, `AudioProcessor` (PascalCase)

**Functions & Methods:**
- Functions and methods: `synthesize_chunk()`, `parse_epub()` (snake_case)
- Private methods: `_load_model()`, `_validate_input()` (leading underscore)
- Properties: `sample_rate`, `is_ready` (snake_case)

**Variables & Constants:**
- Configuration keys: `tts_engine`, `gpu_enabled`, `chunk_size` (snake_case)
- Constants: `DEFAULT_SAMPLE_RATE`, `MAX_BATCH_SIZE` (UPPER_SNAKE_CASE)
- Private module state: `_model_cache`, `_session` (leading underscore)

**File Organization:**
- Core modules in `audiopub/core/`
- UI components in `audiopub/`
- Assets in `audiopub/assets/`
- Voice styles as JSON: `audiopub/assets/voice_styles/*.json`

### Error Handling

```python
# ✅ GOOD: Specific exception, logged, user-facing message
import logging
logger = logging.getLogger(__name__)

try:
    model = onnx.load(model_path)
except FileNotFoundError as e:
    logger.error(f"Model not found at {model_path}")
    raise ModelNotFoundError(
        "Supertone model missing. Ensure Git LFS is installed."
    ) from e

# ✅ GOOD: Graceful fallback with warning
try:
    sess = ort.InferenceSession(model, providers=['CUDAExecutionProvider'])
except Exception as e:
    logger.warning(f"GPU unavailable, using CPU: {e}")
    sess = ort.InferenceSession(model, providers=['CPUExecutionProvider'])

# ❌ BAD: Silent failure
try:
    model = onnx.load(model_path)
except:
    pass  # Silently ignored, will cause cryptic error later

# ❌ BAD: Generic Exception without context
try:
    parse_epub(path)
except Exception:
    print("Error")  # No info for debugging
```

### Logging

```python
import logging
logger = logging.getLogger(__name__)

# Use appropriate log levels:
logger.debug("Model loaded in 1.234s")        # Verbose detail, disabled in prod
logger.info("Starting EPUB parse of 50 chapters")  # Informational
logger.warning("GPU unavailable, using CPU")  # Non-fatal issue, but noteworthy
logger.error("Synthesis failed for chunk 5")  # Recoverable error (continue with next)
logger.critical("Worker thread crashed")      # Unrecoverable error

# ✅ GOOD: Structured, helpful logging
logger.info(f"Synthesizing chapter {chapter_id}: {len(text)} chars, est. {est_ms}ms")

# ❌ BAD: Too verbose or vague
logger.info("Processing")
logger.debug("loop iteration 1")
logger.debug("loop iteration 2")
```

### GPU/CPU Handling

**Pattern: GPU Optional, CPU Always Works**

```python
# ✅ CORRECT pattern for GPU support
class Supertone(TTSBase):
    def __init__(self, model_path, config):
        self.config = config
        # Load model with GPU fallback
        providers = []
        if config.gpu_enabled:
            providers.append('CUDAExecutionProvider')
        providers.append('CPUExecutionProvider')

        try:
            self.sess = ort.InferenceSession(model_path, providers=providers)
            logger.info(f"ONNX session created with providers: {self.sess.get_providers()}")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise

    def synthesize(self, text):
        """Synthesize audio. Works on CPU or GPU."""
        # Implementation here
        pass

# ❌ WRONG: Assumes GPU, no fallback
class BadTTS(TTSBase):
    def __init__(self, model_path, config):
        # Crashes if GPU not available!
        self.sess = ort.InferenceSession(
            model_path,
            providers=['CUDAExecutionProvider']
        )
```

### Reasoning Comments in Code

When you make a non-obvious change, explain it:

```python
# REASONING: Voice style JSON schema expanded to include "timbre" parameter.
# All existing voice files must include this key with a default value to maintain
# backward compatibility. Files updated: F1.json, F2.json, M1.json, M2.json, F1_deep_female.json.
# Risk: None if all voice files are updated; critical if partial.
def load_voice_style(style_name):
    style = json.load(f"voice_styles/{style_name}.json")
    # Ensure timbre key exists (for backward compat)
    style.setdefault('timbre', 'neutral')
    return style
```

---

## What Agents Can Always Do

These changes are **always safe** and don't require pre-approval:

✅ **Add new voice styles**
- Create a new JSON file in `audiopub/assets/voice_styles/`
- Follow the schema of existing voice files (F1.json, F2.json, etc.)
- Test that it loads without errors

✅ **Performance optimizations**
- Caching, vectorization, reducing redundant computations
- Must not change output or behavior
- CPU path must always work

✅ **Add unit tests**
- Test individual functions (parse_epub, synthesize, chunk_text)
- Test error cases and edge cases
- Use pytest or unittest as you see fit

✅ **Refactor private methods**
- `_load_model()`, `_validate_input()`, etc.
- Can rename if no other modules call them
- Must not change public API

✅ **Fix bugs**
- Incorrect logic, off-by-one errors, memory leaks
- Document what was broken and how you fixed it

✅ **Improve logging and diagnostics**
- Add debug logs to help troubleshooting
- Make error messages more helpful
- Performance profiling output

✅ **Add optional config parameters**
- Only if they have sensible defaults
- Must not require cloud APIs or special setup
- Document in comments

---

## What Agents Must NEVER Do

These will **break the system** and are forbidden:

❌ **Remove or rename public methods in tts_base.py**
- This breaks the factory pattern and all TTS engines
- If you need a change, discuss with the maintainer first

❌ **Remove CPU inference support**
- Every code path must have a CPU fallback
- You cannot simplify GPU code by removing CPU

❌ **Change the M4B output format**
- This is the user-facing output contract
- If M4B format changes, all player compatibility breaks

❌ **Add cloud TTS as the primary solution**
- Local-first is non-negotiable (see STRATEGY.md)
- Optional cloud engines are acceptable only if disabled by default

❌ **Add telemetry or analytics**
- No user tracking, crash reporting, or usage stats
- Privacy is a core principle

❌ **Commit without reasoning**
- Every commit must explain WHY the change was needed
- See "Commit Message Format" section below

❌ **Break chapter boundary detection**
- If you change epub.py or audio.py, verify chapters are still accurate
- Users rely on chapter markers in the M4B file

❌ **Change ONNX model loading logic**
- This affects reproducibility and cross-platform compatibility
- Model loading is intentionally locked

---

## Testing Checklist Before Committing

Before you mark a task as done, verify ALL of these:

- [ ] **Code runs on CPU** (required)
  ```bash
  python audiopub/main.py
  # OR run your unit test
  # OR manually test the feature
  ```

- [ ] **Code runs on GPU** (if you touched GPU code)
  ```bash
  # Set GPU enabled, verify it still works
  ```

- [ ] **EPUB parsing still works** (if you touched epub.py or audio.py)
  - Test with 1-2 sample EPUB files
  - Verify chapters are detected correctly
  - No text is lost or corrupted

- [ ] **Output M4B is valid** (if you touched audio.py)
  - Download the M4B file
  - Play it in a standard player (Apple Books, Android Play Books, etc.)
  - Verify it plays without errors

- [ ] **Chapter metadata is preserved** (if you touched audio.py)
  - Play the M4B file
  - Jump to Chapter 2, Chapter 3, etc.
  - Verify chapter marks are accurate

- [ ] **No new cloud dependencies** (always)
  - Check requirements.txt
  - Verify no new cloud API keys are needed
  - Verify offline operation still works

- [ ] **Logging is helpful, not verbose** (always)
  - Debug logs are informative for developers
  - User-facing logs are short and actionable
  - No spam (not logging inside loops)

---

## Commit Message Format

Every commit should have:

**Subject line:** `[COMPONENT] Brief description`

**Body:** Reasoning for why the change was needed (2-4 lines)

**Example:**

```
[TTS] Add deep female voice style (F1_deep_female)

Added new voice style JSON with lower pitch and richer bass.
Requested by users who find F1 too high-pitched.
All existing voice styles remain unchanged.
Tested with 3 sample EPUBs.
```

**Another example:**

```
[AUDIO] Optimize ONNX session caching

Reuse compiled ONNX sessions across multiple chunks to reduce
overhead. Benchmarks show 15% faster synthesis on CPU, 5% on GPU.
No change to output quality or format.
```

### Commit Components

Common components:
- `[TTS]` – Changes to tts.py, tts_neutts.py, voice styles
- `[AUDIO]` – Changes to audio.py, audio assembly, M4B muxing
- `[EPUB]` – Changes to epub.py, text parsing, chapter detection
- `[WORKER]` – Changes to worker.py, orchestration
- `[UI]` – Changes to main.py, NiceGUI interface
- `[CONFIG]` – Changes to config.py
- `[DOCS]` – Changes to documentation (STRATEGY.md, etc.)
- `[TEST]` – Adding tests
- `[FIX]` – Bug fixes (also indicate which component, e.g. `[FIX] TTS model loading`)

---

## When to Ask Before Proceeding

If you're doing ANY of these, **STOP and ask the maintainer** (in a PR or comment) before proceeding:

1. **Adding a new TTS engine**
   - Example: "I want to add Google Cloud TTS"
   - Why: Needs to respect TTSBase contract; may violate local-first principle

2. **Changing ONNX model loading**
   - Example: "Replace ONNX Runtime with PyTorch"
   - Why: Affects reproducibility, portability, and dependencies

3. **Modifying chapter silence duration**
   - Example: "Change 5s gap between chapters to 2s"
   - Why: User-facing; affects audiobook pacing

4. **Changing text chunking algorithm**
   - Example: "Use paragraph-level chunks instead of sentence-level"
   - Why: Affects synthesis latency and memory usage; needs testing

5. **Adding cloud API integration**
   - Example: "Add optional OpenAI Whisper TTS"
   - Why: Must verify it's truly optional and doesn't violate local-first principle

6. **Removing or renaming public methods**
   - Example: "Rename `synthesize()` to `generate_audio()`"
   - Why: Breaks the factory pattern and all TTS engines

7. **Changing the M4B output format**
   - Example: "Use MP3 instead of M4B"
   - Why: User-facing contract; affects player compatibility

---

## Handling Blockers & Errors

### If You Encounter a "Cannot Edit" File

If a file is marked "Editable: ❌" in ARCHITECTURE.md:

1. **Read ARCHITECTURE.md** to understand why it's locked
2. **Document the blocker** in a comment or issue
3. **Ask the maintainer** (in a PR or comment) if your change is necessary
4. **Do NOT work around the constraint** by changing other files

Example:
```
# BLOCKED: tts_base.py method signatures cannot change (factory pattern constraint).
# Need to add new method `get_voice_styles()` to TTSBase.
# This requires updating both tts.py and tts_neutts.py.
# Waiting for maintainer approval to proceed.
```

### If Your Change Breaks Tests

1. **Understand which test failed** (read the error)
2. **Identify the invariant you broke**
   - Did you remove CPU support?
   - Did you change chapter boundary detection?
   - Did you break the TTSBase contract?
3. **Fix the code** to restore the invariant
4. **Re-run tests** to verify

### If You Discover a New Blocker

If you find that the roadmap has a blocker you didn't know about:

1. **Read ROADMAP.md** for context
2. **Update the blocker entry** if your work reveals new information
3. **Add a comment** explaining what you discovered
4. **Ask the maintainer** what the next step should be

---

## Code Review Checklist for Maintainer

When reviewing a PR from an agent, check:

- [ ] Commit message explains WHY (not just WHAT)
- [ ] CPU test passes (code runs on CPU alone)
- [ ] GPU test passes (if GPU code was touched)
- [ ] Chapter boundaries/metadata preserved (if audio.py touched)
- [ ] M4B output is valid (if audio.py touched)
- [ ] No new cloud dependencies
- [ ] No breaking changes to public APIs
- [ ] Logging is appropriate (not spam)
- [ ] Reasoning comments explain non-obvious changes

---

## Example: Safe Change (Adding a Voice Style)

**Task:** Add a new "whisper" voice style

**Steps:**

1. **Read architecture:** Voice styles are JSON files in `audiopub/assets/voice_styles/`
2. **Create file:** `audiopub/assets/voice_styles/F1_whisper.json`
3. **Copy existing:** Base it on F1.json schema
4. **Test:** Load it in tts.py, verify no errors
5. **Commit:** `[TTS] Add F1_whisper voice style`

**Commit message:**
```
[TTS] Add F1_whisper voice style

New voice style with breathy, intimate tone for narration.
Based on F1.json schema; all existing voices unchanged.
Tested: loads without errors, synthesizes correctly.
```

---

## Example: Blocked Change (Changing TTS Interface)

**Task:** Add `get_voice_styles()` method to TTSBase

**Steps:**

1. **Read architecture:** TTSBase is locked (tts_base.py, "Editable: ❌")
2. **Understand why:** Factory pattern depends on stable interface
3. **STOP and ask:** Create an issue or comment in the PR
   - "I need to add `get_voice_styles()` to TTSBase"
   - "This requires updating tts.py and tts_neutts.py"
   - "Is this acceptable?"
4. **Wait for approval** before proceeding

**If approved:**
- Update tts_base.py with new abstract method
- Update tts.py with implementation
- Update tts_neutts.py with implementation
- Test all TTS engines
- Commit: `[TTS] Add get_voice_styles() method to TTSBase interface`

---

## Key Files Reference

| File | Responsibility | Editable? |
|------|-----------------|-----------|
| audiopub/main.py | Web UI & server | ✅ |
| audiopub/core/tts_base.py | TTS interface | ❌ |
| audiopub/core/tts.py | Supertone engine | ✅ |
| audiopub/core/tts_neutts.py | NeuTTS Air engine | ✅ |
| audiopub/core/tts_factory.py | Engine factory | ✅ |
| audiopub/core/epub.py | EPUB parsing | ✅ |
| audiopub/core/audio.py | Audio assembly | ✅ |
| audiopub/core/worker.py | Orchestration | ✅ |
| audiopub/config.py | Configuration | ✅ |

---

## If You Get Stuck

1. **Read ARCHITECTURE.md** for the module you're editing
2. **Look at recent commits** (`git log`) to see patterns
3. **Check existing error handling** for similar cases
4. **Ask in a comment** or PR description what's unclear
5. **Escalate if needed** – don't work around constraints

---

## Document History

- **Version 1.0** – Nov 2024 – Initial agent guide
