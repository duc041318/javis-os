# Meeting room: an outside lead (lead key)

Short design, approved by the owner on 2026-11-22 ("A").

## Intent
The owner wants Claude (Claude Desktop, Claude Code or the Claude app) to be the LEAD of the meeting room, with
Javis, Hermes and Muse as the hands. Today only the model running inside Javis can lead, through the
`javis_council` tool. Hermes and Muse already plug into `/ext/javis-council/mcp` as members.

## Goals
- The owner asks Javis for a lead key ("cấp khoá đầu não"). Plugging that key into an outside MCP client gives it
  the lead's tools: status, assign, answer, meet, next round, conclude, read, log, cancel.
- Same endpoint `/ext/javis-council/mcp`. A member key still sees only its own inbox tools.
- The log names who led: the inside brain stays "Javis", the outside lead shows as its own name.

## Non-goals / anti-goals
- The outside lead cannot add or remove members: member keys are issued only inside Javis, so they never pass
  through a cloud model.
- No change for Hermes and Muse. No new server, no new port.
- Javis as a hand is reached through Javis Gate (already shipped), not through this change.

## Approaches
- A (picked): a lead key on the existing council MCP endpoint. One plugin file plus tests.
- B: a separate MCP server. Duplicates the store and needs its own process. Rejected.
- C: no code, the lead talks to Javis through Javis Gate and Javis relays. Works today, but a second model sits in
  the middle (slower, double cost) and Claude is not the lead itself. Rejected.

## Design
- Store: `d["lead"] = {"key_hash", "created", "last_seen", "active"}`. Key prefix `jl_`, 32 random bytes, shown once,
  only the sha256 is kept, compared with `hmac.compare_digest`.
- `javis_council` gains `op=lead_key` (issue or reissue, returns the key once with connect instructions for
  Claude Code, Claude Desktop and the Claude app) and `op=lead_revoke`.
- MCP: a `jl_` key resolves to the lead. `tools/list` returns the lead tools, `instructions` the lead brief,
  `tools/call` runs the same code path as `javis_council` (shared function), with the actor set to the lead so log
  lines read "Đầu não ngoài". Member names `lead` and `javis` are reserved.
- Status shows whether an outside lead is connected and when it was last seen.
- Text the members send stays fenced as DATA in what the lead reads, as today.
- New identifiers are English (hard rule since 2026-11-22). New prompt and tool text is English.

## Left to the builder
Exact tool descriptions and wording of the connect instructions.
