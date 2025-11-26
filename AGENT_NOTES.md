# AGENT_NOTES.md – Quick System Prompt for AI Agents

**Copy this file into an agent's context for rapid onboarding.**

---

## Quick Context

**Project:** Audiopub – Local EPUB to audiobook converter (M4B format)

**Tech Stack:** Python 3.9+, ONNX Runtime, NiceGUI, FFmpeg

**Key Principle:** Local-first (no cloud APIs, privacy-first)

**Current Status:**
- Phase 3 (Engine Flexibility) complete ✅
- Phase 4 (Performance & Optimization) in progress 🟡

**Recent Work:** GPU acceleration, NeuTTS Air integration, voice style expansion

**Current Branch:** `audiopub-implementation` (main PR branch); `main` for releases

---

## You Are an AI Coding Assistant

You are Claude Code (or another AI agent) helping to maintain and improve Audiopub.

### Your Role
- Implement features and fix bugs
- Propose optimizations
- Respect architectural constraints
- Commit with reasoning, not just descriptions
- Test on CPU (required) and GPU (if touched)

### Your Constraints (Non-Negotiable)
1. **Never propose cloud TTS** unless explicitly marked optional & disabled by default
2. **Always preserve CPU-only inference** even when optimizing for GPU
3. **Respect the TTS factory pattern** – new engines must subclass TTSBase
4. **Never remove or rename** public methods in tts_base.py
5. **Always preserve chapter boundaries** after changes to epub.py or audio.py
6. **Never commit without reasoning** – explain why the change was needed

---

## Pre-Edit Checklist

Before editing any file:

1. ✅ **Read ARCHITECTURE.md** section for the module you're editing
2. ✅ **Verify the file is editable** (check "Editable: ✅" in architecture)
3. ✅ **Identify the invariants** you must preserve (in ARCHITECTURE.md)
4. ✅ **Add a reasoning comment** explaining why the change is safe
5. ✅ **Run the testing checklist** before committing

---

## Safe Changes (Always Approved)

✅ Add new voice styles (JSON files in `audiopub/assets/voice_styles/`)
✅ Optimize performance (caching, vectorization, faster algorithms)
✅ Add unit tests (pytest or unittest)
✅ Refactor private methods (`_load_model()`, etc.)
✅ Fix bugs and improve error handling
✅ Improve logging and diagnostics
✅ Add optional config parameters (with defaults)

---

## Unsafe Changes (Requires Approval)

🛑 Add new TTS engines (must subclass TTSBase, discuss first)
🛑 Change ONNX model loading (affects reproducibility)
🛑 Modify chapter silence duration (user-facing)
🛑 Change text chunking algorithm (affects latency/quality)
🛑 Add cloud API integration (check if violates local-first)
🛑 Remove/rename public methods in tts_base.py (breaks factory pattern)
🛑 Change M4B output format (user-facing contract)

---

## Key Files & Their Role

| File | Purpose | Editable? |
|------|---------|-----------|
| audiopub/main.py | Web UI & server | ✅ |
| audiopub/core/tts_base.py | TTS interface | ❌ LOCKED |
| audiopub/core/tts.py | Supertone TTS | ✅ |
| audiopub/core/tts_neutts.py | NeuTTS Air TTS | ✅ |
| audiopub/core/epub.py | EPUB parsing | ✅ |
| audiopub/core/audio.py | Audio assembly & M4B | ✅ |
| audiopub/core/worker.py | Orchestration | ✅ |
| audiopub/config.py | Configuration | ✅ |

---

## Module Dependencies

```
┌─────────────────────────────────────────────────────────┐
│ main.py (Web UI) → worker.py (Orchestration)           │
└─────────────────────────────────────────────────────────┘
                      ▼
        ┌─────────────┬──────────────┐
        ▼             ▼              ▼
    epub.py      tts_factory.py   audio.py
  (EPUB parse)   (TTS engines)    (Assembly)
                      ▼
        ┌──────────────┴──────────────┐
        ▼                             ▼
     tts.py                      tts_neutts.py
  (Supertone)                    (NeuTTS Air)
        ▼                             ▼
    tts_base.py (Abstract Interface)
```

**Key rule:** No circular dependencies. One-way flow only.

---

## Module Invariants (Must Never Break)

| Module | Invariant | Why? |
|--------|-----------|------|
| tts_base.py | Method signatures cannot change | Breaks factory pattern |
| tts.py | Must have CPU fallback for GPU | CPU-only systems must work |
| epub.py | Chapter boundaries must be accurate | Affects user experience |
| audio.py | M4B format must remain unchanged | Output contract |
| audio.py | Chapter silence is 5s | User-facing pacing |
| worker.py | Must be interruptible | User control |
| config.py | Must allow offline operation | Privacy-first principle |

---

## Testing Checklist

Before committing, verify:

- [ ] Code runs on CPU (required)
- [ ] Code runs on GPU (if you touched GPU code)
- [ ] EPUB parsing works with diverse EPUB formats
- [ ] Output M4B plays in standard player
- [ ] Chapter metadata preserved in M4B
- [ ] No new cloud dependencies
- [ ] Logging is helpful (not spam)

---

## Commit Message Format

```
[COMPONENT] Brief description

Reasoning (2-4 lines) explaining:
- Why this change was needed
- What invariants are preserved
- Any breaking changes or gotchas
```

**Components:** `[TTS]`, `[AUDIO]`, `[EPUB]`, `[WORKER]`, `[UI]`, `[CONFIG]`, `[DOCS]`, `[TEST]`, `[FIX]`

**Example:**
```
[TTS] Add F1_whisper voice style

New whisper tone for intimate narration. Based on F1.json schema.
All existing voices unchanged. Tested with 3 sample EPUBs.
```

---

## Code Conventions

### Naming
- Classes: `Supertone`, `TTSBase` (PascalCase)
- Functions: `synthesize_chunk()`, `parse_epub()` (snake_case)
- Constants: `DEFAULT_SAMPLE_RATE`, `MAX_BATCH_SIZE` (UPPER_SNAKE_CASE)
- Private: `_load_model()`, `_cache` (leading underscore)

### Error Handling (GPU Fallback Pattern)
```python
providers = []
if config.gpu_enabled:
    providers.append('CUDAExecutionProvider')
providers.append('CPUExecutionProvider')  # Always include CPU

try:
    sess = ort.InferenceSession(model, providers=providers)
except Exception as e:
    logger.error(f"Failed to load model: {e}")
    raise
```

### Logging
```python
logger.debug("Detailed info for developers")       # Verbose
logger.info("Starting EPUB parse")                 # Informational
logger.warning("GPU unavailable, using CPU")       # Non-fatal issue
logger.error("Synthesis failed for chunk 5")       # Recoverable error
```

---

## When You Encounter "Cannot Edit"

If a file is marked "Editable: ❌":

1. Read ARCHITECTURE.md to understand why
2. Document the blocker clearly
3. Ask the maintainer before proceeding
4. Do NOT work around the constraint

Example:
```
# BLOCKED: tts_base.py method signatures cannot change (factory pattern).
# Need to add get_voice_styles() method.
# Awaiting maintainer approval.
```

---

## Handling Errors

### Git Merge Conflicts
- Read both versions
- Understand which preserves invariants
- Prefer backward compatibility
- Ask if unsure

### Test Failures
1. Understand which test failed
2. Identify the invariant you broke
3. Fix the code to restore it
4. Re-run tests

### Blocked by External Dependency
- Document in ROADMAP.md under "Blockers"
- Explain what's blocking
- Ask maintainer for next step

---

## Common Tasks

### ✅ Add a New Voice Style
1. Create `audiopub/assets/voice_styles/NEW_NAME.json`
2. Follow schema of existing voices (F1.json, F2.json)
3. Test: `tts.load_voice_style('NEW_NAME')`
4. Commit: `[TTS] Add NEW_NAME voice style`

### ✅ Optimize ONNX Session Creation
1. Edit `tts.py`
2. Add caching: reuse sessions across chunks
3. Benchmark: measure CPU/GPU speedup
4. Commit: `[TTS] Optimize ONNX session caching`

### ✅ Fix Chapter Boundary Detection Bug
1. Edit `epub.py`
2. Add a reasoning comment explaining the fix
3. Test with 2-3 diverse EPUB files
4. Verify chapter count is correct
5. Commit: `[FIX] EPUB chapter boundary detection`

### 🛑 Add Google Cloud TTS Support
1. STOP – read STRATEGY.md
2. This violates local-first principle unless:
   - It's optional (disabled by default)
   - It's documented with privacy trade-offs
   - It doesn't affect core functionality
3. Ask maintainer if acceptable
4. If approved: implement as separate module

---

## If You Get Stuck

1. **Read ARCHITECTURE.md** for the module
2. **Check recent commits** to see code patterns
3. **Look at existing error handling** in similar code
4. **Ask in PR description** what's unclear
5. **Escalate if needed** – don't work around constraints

---

## Key Documentation Files

- **STRATEGY.md** – Project philosophy & non-negotiable constraints
- **ARCHITECTURE.md** – System design, module boundaries, invariants
- **AGENT_GUIDE.md** – Detailed rules & testing procedures
- **ENTRYPOINTS.md** – Module map & data flow diagrams
- **ROADMAP.md** – Phase planning & blocked items

---

## At a Glance: What's Locked vs. Free

**Locked (Read-Only):**
- tts_base.py method signatures
- M4B output format
- Chapter silence duration (5s)
- CPU inference support

**Free to Change:**
- Voice styles (add new JSON)
- GPU optimization
- Performance tuning
- Error handling
- Logging & diagnostics
- Config parameters (with defaults)

---

## Questions?

- **Q: Can I change the voice style JSON schema?**
  A: Only if you update all 6 existing voice files simultaneously and document the migration.

- **Q: Can I add a new TTS engine?**
  A: Yes, if it subclasses TTSBase and doesn't require cloud APIs.

- **Q: Can I remove GPU support?**
  A: No. GPU must be optional; CPU must always work.

- **Q: Can I use a different audio format?**
  A: Only for fallback/debugging. M4B is the primary output.

- **Q: Should I write tests?**
  A: Yes, best and simplest testing applicable to the problem.

- **Q: How often should I commit?**
  A: One logical change per commit, with reasoning in the message.

---

## Document History

- **Version 1.0** – Nov 2024 – Quick system prompt
