# Claude Code – Project Playbook: EWS-Project-Plan

> Repo nickname: **EWS** · Purpose: Execute the Ethical Web Scraper Project Plan with reliable session handoffs and checkpoints for defensive security research.

---

## 0) Mission & Working Agreement

When asked for changes in this repo:

1. **Plan** briefly (what/why/files to touch).
2. **Patch** with **small, reviewable diffs**; no broad rewrites unless asked.
3. **Test** using the quality gates in §4.
4. **Summarize** changes, risks, and next steps.
5. Respect the guardrails below.

**Non‑negotiables**

* Production‑ready diffs only (no placeholders or TODO litter in committed code).
* Preserve headers/license blocks; bump versions per project rules.
* No secrets in code; use `.env`/secure config.

---

## 1) Session Commands (exact phrases to use)

### ▶️ `EWS start`

**Goal:** Prime context at the start of a session.
**Claude should:**

1. Read, if present (otherwise create stubs):

   * `docs/EWS-Project-Plan.md`
   * Latest `docs/archive/checkpoints/CheckPoint-*.md`
   * `docs/projectStatus.md`
2. Post a **kickoff note** with:

   * **Last session wins** (bullets)
   * **What remains this sprint** (bullets)
   * **Today’s plan** (1–3 concrete steps)
3. Confirm Git branch/status and whether working tree is clean.

### 💾 `EWS checkpoint`

**Goal:** Capture state at any time (especially near usage limits) so the next session can resume seamlessly.
**Claude should:**

1. Create a new checkpoint file in `docs/archive/checkpoints/` using the existing naming pattern if found; otherwise default to:
   `CheckPoint-YYYY-MM-DD_HHMM.md`
2. Use this template in the file:

   * **Context summary** (why we’re here)
   * **Accomplishments** (what shipped)
   * **Technical changes** (files touched, diffs overview)
   * **Known issues / blockers**
   * **Next session priorities** (bullet list)
   * **Backlog movement** (added/removed/deferred)
   * **Git status** (branch, last commit hash, pushed: yes/no)
3. Update live docs:

   * Append any **Design Variations & Rationale** to `docs/EWS-Project-Plan.md`.
   * Update `docs/projectStatus.md` (Completed / In‑Progress / Deferred + Next items).
4. `git add -A && git commit -m "chore(checkpoint): YYYY-MM-DD_HHMM – <short summary>" && git push`
5. Reply in chat with a 1‑paragraph summary + a checklist of next steps.

> **Trigger words**: "checkpoint now", "prepare for rollover", "juice check", "save state" → run **EWS checkpoint** immediately.

### ⏹️ `EWS shutdown`

**Goal:** End a session cleanly and **always** checkpoint.
**Claude should:**

1. Run **EWS checkpoint** (mandatory).
2. Ensure all changes are pushed; echo branch, commit hash, and tag if created.
3. Post “Shutdown complete” with **3 bullets** for the next session.

---

## 2) Project Guardrails (EWS specifics)

* **Stack**: Python 3.11+, Playwright, BeautifulSoup4, Pydantic, Typer, YAML configs.
* **Purpose**: Ethical web scraping for defensive security research with partner permission.
* **Ethics**: Respect robots.txt by default, implement rate limiting, use proper user-agent identification.
* **Error Handling**: Structured exception hierarchy (EWS001-EWS005) with retry logic.
* **Output**: JSON format with absolute image URLs, configurable to CSV/XML.
* **Performance**: Max 5 concurrent requests, 30s timeout per page, <500MB memory per scrape.

---

## 3) Files & Paths (authoritative)

* **Plan**: `docs/EWS-Project-Plan.md` (source of truth + Design Variations section)
* **Status**: `docs/projectStatus.md` (sprint state + next actions)
* **Checkpoints**: `docs/archive/checkpoints/` (one markdown per checkpoint)

> If these files/folders don’t exist, Claude should create them with minimal scaffolding.

---

## 4) Code Quality Gates & Runbook

### Python

```bash
ruff --fix . && black . && mypy . && pytest -q
```

* Full typing on new/changed code; Google‑style docstrings.
* Use structured logging; no `print` in libraries.
* CLIs default to safe behavior (dry‑run when destructive).
* `pathlib` for filesystem ops; write OS‑portable code.

### Playwright Browser Tests

```bash
pytest tests/integration/ -v --browser=chromium
```

* Test browser automation, JavaScript rendering, selector validation.
* Verify robots.txt compliance and rate limiting behavior.

---

## 5) Debug/Release Hygiene

Before tagging a release:

* Remove debug prints and traces from scraper modules.
* Re‑run quality gate and integration tests; verify ethical compliance.
* Test with real website scenarios and validate JSON output schema.

---

## 6) Override Directives (Add / Edit / Delete)

Change rules via chat without manually editing this file. Claude should apply the change, show a small diff, and commit.

### Add

```
ADD RULE → <Section Anchor>
<one sentence rule to append>
```

### Edit

```
EDIT RULE → <Section Anchor>
<existing line text>
--- becomes ---
<new line text>
```

### Delete

```
DELETE RULE → <Section Anchor>
<exact line text to remove>
```

**Section Anchors**:
`0) Mission` · `1) Session Commands` · `2) Project Guardrails` · `3) Files & Paths` · `4) Code Quality Gates` · `5) Debug/Release Hygiene` · `6) Override Directives`

---

## 7) Quick Prompts

* **Start session**: `EWS start`
* **Checkpoint now**: `EWS checkpoint — summarize, commit, push`
* **End session**: `EWS shutdown`
* **Override rule**: `EDIT RULE → 4) Code Quality Gates …`

---

## 8) Notes on Continuity & Limits

* Use **EWS checkpoint** whenever you're nearing your daily usage cap or switching tasks.
* A checkpoint is **mandatory** for every **EWS shutdown**.
* Next session resumes with **EWS start** which reads the last checkpoint and aligns the plan.
