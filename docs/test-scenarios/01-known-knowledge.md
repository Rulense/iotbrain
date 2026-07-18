# Scenario 1 — Known-knowledge path (no internet)

**Verifies:** a seeded entry is found by grep and applied with version filtering.

**Setup:** Claude Code session with the jetson-brain plugin installed; network
access to forums BLOCKED or unused (watch the transcript); any Orin device or a
mocked device-facts response (JetPack 6.1, Orin Nano).

**Steps:**
1. Prompt: "import torch on my Orin Nano fails with
   `ImportError: libcudnn.so.9: cannot open shared object file`"
2. Observe the agent.

**Pass criteria:**
- Agent collects device facts BEFORE proposing fixes.
- Agent greps the brain and reads
  `brain/ml-stack/pytorch-wheel-libcudnn-import-error.md`.
- Agent applies the entry's fix and runs its Verify step.
- No web search occurs.

**Fail signals:** web research before brain lookup; fix proposed without device
facts; entry found but Verify step skipped.
