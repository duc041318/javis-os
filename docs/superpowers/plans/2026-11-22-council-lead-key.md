# Meeting room lead key Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let an outside MCP client (Claude) lead the meeting room with a lead key, on the existing `/ext/javis-council/mcp` endpoint.

**Architecture:** The store gains one `lead` record (hashed key). The body of `_brain_chay` moves into a shared `run_lead_op(store, args)` used by both the in-Javis tool and the MCP lead tools. A context variable names the actor so log lines say who led.

**Tech Stack:** Python 3, Starlette (via Javis plugin host), stdlib only.

**Spec:** `docs/superpowers/specs/2026-11-22-council-lead-key-design.md`

## Global Constraints
- New identifiers (functions, variables, constants, params) are English; never add names to `tests/python/english_identifiers_baseline.json`.
- New prompt and tool-description text is English. No em dash anywhere.
- Lead key prefix `jl_`, `secrets.token_urlsafe(32)`, only sha256 stored, compared with `hmac.compare_digest`.
- Reserved member names: `javis`, `lead`.
- The outside lead never gets `add_member`, `remove_member`, `setup`, `lead_key`, `lead_revoke`.
- One `changelog.d/<slug>.md` fragment (`bump: minor`); do not touch VERSION or CHANGELOG*.

## Review Focus
- A member key (`jc_`) calling a lead tool name: must get "Unknown tool", not run it.
- A revoked or reissued lead key: the old key must return 401.
- The lead calling `council_read` on a task: member text still fenced as DATA.
- `lead_key` issued before any member exists: still works, status shows lead not connected yet.
- The actor context must reset after each MCP call, so a later in-Javis call logs as "Javis".

---

### Task 1: Lead key, shared op runner, MCP routing

**Files:**
- Modify: `system/plugins/javis-council/plugin.py`
- Test: `tests/python/test_javis_council.py` (append a section before the final summary)
- Create: `changelog.d/council-lead-key.md`

**Interfaces:**
- Produces: `LEAD = "lead"`; `Store.issue_lead_key() -> str`; `Store.revoke_lead_key() -> bool`; `Store.lead_matches(key: str) -> bool`; `run_lead_op(store: Store, args: dict) -> str`; `LEAD_TOOLS: list[dict]` (names `council_status, council_assign, council_answer, council_meet, council_next_round, council_conclude, council_read, council_log, council_cancel`); `_ACTOR: contextvars.ContextVar[str]` default `_BRAIN`.

- [ ] **Step 1: Write the failing tests** (in the test file, new section "5. outside lead")

```python
out = brain(op="lead_key")
k_l = next(w for w in out.split() if w.startswith("jl_"))
check("lead key shown once, store keeps only the hash", k_l not in (lp.ctx.data_dir / "council.json").read_text(encoding="utf-8"))
check("lead key comes with Claude connect instructions", "claude mcp add" in out)
names = {t["name"] for t in rpc("tools/list", key=k_l).json()["result"]["tools"]}
check("lead sees lead tools", {"council_assign", "council_meet", "council_conclude", "council_status"} <= names)
check("lead cannot manage members", not any("member" in n for n in names))
check("lead brief in initialize", "lead" in rpc("initialize", key=k_l).json()["result"]["instructions"].lower())
txt, err = call(k_l, "council_assign", to="hermes", title="Check Downloads", detail="List 10 newest files.")
check("lead assigns work", not err and "T" in txt)
check("log names the outside lead", "Đầu não ngoài" in brain(op="log"))
brain(op="status")
check("in-Javis brain still logs as Javis afterwards", brain(op="log").splitlines()[-1].count("Javis") >= 0)
r = rpc("tools/call", {"name": "council_assign", "arguments": {"to": "hermes", "title": "x"}}, k_h).json()
check("member key cannot call lead tools", "error" in r)
check("name 'lead' is reserved", brain(op="add_member", name="lead").startswith("ERROR"))
check("status shows the outside lead", "Đầu não ngoài" in brain(op="status"))
brain(op="lead_revoke")
check("revoked lead key -> 401", rpc("tools/list", key=k_l).status_code == 401)
```

Note: Muse was removed earlier in the file, so assign to `hermes`. The "logs as Javis afterwards" check must instead assert the last log line after a `brain(op="assign", ...)` call starts with the `Javis` label; write it that way.

- [ ] **Step 2: Run to verify they fail**

Run: `python tests/python/test_javis_council.py`
Expected: FAIL at "lead key shown once" (`op` unknown).

- [ ] **Step 3: Implement in `plugin.py`**
- Constants `LEAD = "lead"`, `LEAD_LABEL = "Đầu não ngoài"`; `_ten()` returns `LEAD_LABEL` for `LEAD`; member-name check rejects `_BRAIN` and `LEAD`.
- `_ACTOR` context var; `Store._ghi_log` replaces `who == _BRAIN` with `_ACTOR.get()`. `_log_txt` member filter also keeps `LEAD` rows.
- `Store._load` adds `d.setdefault("lead", {})`. `issue_lead_key`, `revoke_lead_key`, `lead_matches` (updates `last_seen` at most once a minute, like `xac_thuc`).
- Move the body of `_brain_chay` into `run_lead_op(store, args)`; `_brain_chay` calls it. Add ops `lead_key` (returns key plus connect text for Claude Code `claude mcp add --transport http javis-council <url> --header "Authorization: Bearer <key>"`, Claude Desktop/app custom connector with `<url>?key=<key>`, HTTPS note when no domain, localhost URL `http://localhost:7777/ext/javis-council/mcp` as the local fallback) and `lead_revoke`. Add both to `_BRAIN_OPS` and `_BRAIN_DESC`.
- `_status_txt` adds a line: outside lead connected or not, last seen.
- `LEAD_TOOLS` + `LEAD_INSTRUCTIONS` (English). `call_lead_tool(store, name, args) -> str` maps `council_<op>` to `run_lead_op` with `_ACTOR` set to `LEAD` (reset in `finally`); unknown name raises `KeyError`; `council_read` and `council_log` reuse the existing ops.
- `xu_ly_rpc`: when `who == LEAD`, use `LEAD_TOOLS`, `LEAD_INSTRUCTIONS`, `call_lead_tool`. `_mcp_http`: try `store.lead_matches(key)` first, then `xac_thuc`.
- Update the module docstring with a short "Outside lead" paragraph.

- [ ] **Step 4: Run tests**

Run: `python tests/python/test_javis_council.py && python tests/python/test_english_identifiers.py && python tools/release.py check`
Expected: `PASS: 0 lỗi`, english identifiers OK, fragment ok.

- [ ] **Step 5: Changelog fragment and commit**
`changelog.d/council-lead-key.md`, `bump: minor`, title `Meeting room takes an outside lead such as Claude`, vi and en blocks under `### Thêm mới` / `### Added`.

```bash
git add system/plugins/javis-council/plugin.py tests/python/test_javis_council.py changelog.d/council-lead-key.md docs/superpowers
git commit -m "Meeting room takes an outside lead such as Claude"
```
