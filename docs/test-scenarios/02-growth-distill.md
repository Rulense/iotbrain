# Scenario 2 — Growth path (research → verify → distill)

**Verifies:** an unseeded problem flows through research and produces a
schema-valid local-overlay entry.

**Setup:** plugin installed; pick a real Jetson issue NOT in the brain (check
INDEX.md first); a device (or honest simulation) where the fix can be verified.

**Steps:**
1. Present the unseeded problem.
2. Let the agent research, fix, and verify it.
3. Observe whether brain-distill is invoked.

**Pass criteria:**
- Agent greps the brain first and correctly reports a miss.
- After the fix is VERIFIED (not merely found), brain-distill runs.
- Entry appears under `~/.jetson-brain/local/<domain>/` with verbatim keys and
  correct device/JetPack frontmatter.
- `python3 scripts/lint_brain.py ~/.jetson-brain/local` exits 0 (INDEX check
  errors are acceptable for the overlay; frontmatter errors are not).

**Fail signals:** distillation before verification; paraphrased keys; entry
written straight into the plugin's brain/ directory.
