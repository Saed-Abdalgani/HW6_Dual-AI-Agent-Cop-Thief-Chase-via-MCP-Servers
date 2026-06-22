# PRD — Natural-Language Protocol

## Purpose

Phase P5 replaces rigid inter-agent signaling with free-text messages sent through MCP
`send_message` and received through MCP `receive_message`.

## Requirements

- Agents may describe intent, pressure, uncertainty, taunts, hints, and bluffs.
- Messages must not transfer raw grid coordinates such as `(2, 3)` or `2,3`.
- Messages may use coarse spatial cues: north, south, east, west, corner, center, wall, edge.
- Empty, misleading, or garbled messages must not crash a turn.
- Parser output is advisory only; the rules engine remains authoritative for legal actions.

## Message Styles

- Cop messages should probe, pressure, or suggest a closing route.
- Thief messages may evade, bluff, or reveal partial truth.
- LLM messages are sanitized before MCP transmission; coordinate-like fragments are removed.

## Examples

Allowed:

- `I am pressing toward the eastern side from the central lanes.`
- `I might be quiet near the northern western lanes, unless that silence is bait.`
- `Which wall are you hugging now?`

Forbidden:

- `I am at (2, 3).`
- `Move to 4,1 next.`
- `My exact cell is [0, 2].`

## Ambiguity Policy

The parser extracts coarse cues and assigns confidence. Ambiguous messages leave the belief mostly
unchanged and increase uncertainty. Strategies must remain able to choose a legal fallback action
when no useful natural-language signal is available.

## Evidence

Each sub-game writes JSON Lines transcripts to `results/nl_transcript_subgame_<n>.jsonl`.
Each line records timestamp, agent, action, move count, and the final transmitted message.
