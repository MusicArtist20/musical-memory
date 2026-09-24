# Melody Memory — Online Foundation Architecture (Turn-Based 2-Player)

**Status:** design only. No implementation code yet (per prompt-(2)).
**Engine:** NVGT, same as the existing offline game. Networking uses NVGT's
built-in `network` / `network_event` classes; messages are JSON via
`json_object` / `parse_json()`. No third-party dependencies.

**Chosen mode:** online is **turn-based two-player**. Two players connect to a
server, face the *same* server-generated melody ladder, alternate attempts, and
the server validates and compares their performances. Everything else in the
game — single-player, Game Settings, Test Speakers, menu music — stays fully
offline and untouched.

---

## 0. Guiding principle

Offline gameplay already exists and works. Online must be an **adapter**, not a
rewrite. The first move is to *extract* the pure gameplay rules out of
`melody_memory.nvgt` into a networking-free module (`game_core.nvgt`), then have
**both** the offline game and the server call that one module. The online path
adds a match layer around the same rules — it does not duplicate them.

---

## 1. Client / server data flow

```
   CLIENT A                    SERVER (authoritative)                 CLIENT B
   --------                    ----------------------                --------
   join {name} ...............>  lobby: hold until 2 players
                                 create match: melody ladder (fixed at start)
   <........................ match_start {opponent, ladder, first_turn}
   turn_start {round, melody, gap_ms, active=A} .................> (same, active=A)
   A plays the melody, then presses 1-8
   note_input {round, index, note} ...> validate (A is active, index, range...)
   <... note_feedback {correct, expected?}
   (turn ends on last note / mistake / give_up)
   <... turn_result {player=A, passed, lives_left} ..............> turn_result (B hears it)
   turn_start {round, melody, active=B} .......... same melody ....> B's turn
   ... rounds advance only after BOTH players attempted the round ...
   match_over {winner, reason, rounds_reached} to both
```

One reliable channel carries everything. A turn-based game needs no realtime
channel; none is opened (no "unnecessary online features").

**Match lifecycle:** lobby → `match_start` → alternating turns → `match_over` →
both clients return to their menus. A third connection waits in the lobby for
the next free pair (the server hosts multiple independent matches).

## 2. Client → server messages

| type | payload | when |
|---|---|---|
| `join` | `protocol_version`, `game_version`, `name?` | on connecting |
| `ready` | — | player confirmed match start |
| `note_input` | `round`, `index`, `note` (0–7) | active player's number-key press |
| `give_up` | `round`, `reason` | active player abandons the turn (counts as a fail) |
| `state_request` | — | resync after stall / reconnect |
| `leave` | — | back to menu / quit |

Replay (`r`) and note-names (`l`) are **not** network messages — pure local
presentation on the attempting client's already-received melody.

## 3. Server → client messages

| type | payload | when |
|---|---|---|
| `welcome` | `player_id` | after `join`, while waiting in lobby |
| `match_start` | `match_id`, `opponent_name`, `lives`, `first_active` | lobby filled |
| `turn_start` | `round`, `melody[]`, `gap_ms`, `active_player`, `attempt` | a turn begins (identical melody to the opponent's attempt of the same round) |
| `note_feedback` | `index`, `correct`, `expected` (only on fail) | reply to each `note_input` |
| `turn_result` | `player`, `round`, `passed`, `lives_left` | a turn ends (both clients receive it — the waiting player hears the opponent's outcome) |
| `match_over` | `winner`, `reason`, `rounds_reached` | match ends |
| `error` | `reason`, `fatal` | protocol/rule violation (non-fatal for "not your turn") |

`melody[]` is sent because an audio game must *play* the notes locally — the
server owns the authoritative copy, the client renders it.

## 4. Communication data structures

**Envelope** (every message, both directions):
```
{ "type": "<message type>",
  "protocol": 1,
  "seq": <uint>,          // per-sender monotonic; receivers drop stale seq
  "payload": { ... } }
```

**Serialization:** one `stringify()`'d `json_object` per message, sent as one
reliable `network.send()` packet. JSON keeps the protocol inspectable and
debuggable, consistent with the game's existing JSON settings/save files.

**Shared state structs** (in `game_core.nvgt`, engine- and network-free):
```
round_state     { int round; int[] melody; int length; int gap_ms; }        // one ladder entry
attempt_state   { int round; int index; int[] submitted; int lives_left; bool over; }  // per player
note_result     { bool correct; int expected; bool round_done; bool passed; }
```
The server holds the fixed ladder (`round_state[]`, generated once per match) plus
two `attempt_state`s (player A, player B). The offline loop uses the very same
`attempt_state`/`note_result` logic, so "an attempt" has exactly one definition.

## 5. Client responsibilities

- Menu, speech, all audio playback. New "Online game" menu item leading to a
  direct-connect screen (type server address — no matchmaking, per the prompt).
- Render match state: play the received melody on your turn; speak progress and
  outcomes of the opponent's turns from `turn_result`/`turn_start` events.
- Collect the active player's key presses and forward them.
- Keep a read-only mirror of both players' attempt states for UI/speech.
- Never decide pass/fail. Local comparison may drive instant click audio, but
  the server's `note_feedback`/`turn_result` verdict always wins.

## 6. Server responsibilities

- Lobby: pair connecting clients into 2-player matches.
- Generate one melody ladder per match (offline rule: round-stable prefix, one
  new random note per round, up to 24) and hand out melodies to render.
- Own the authoritative `attempt_state` for **both** players; enforce turn
  ownership (only the active player's inputs are accepted).
- Validate every submitted note; own lives, round advancement, pass/fail, and
  match end. Compare performances by ladder survival (see §7).
- Reject out-of-turn, out-of-order, out-of-range, premature, or rate-violating
  input.
- Nothing cosmetic: no speech, no audio, no menus on the server.

## 7. Validation approach (server-authoritative)

For every `note_input` the server checks, in order:

1. **Session exists and is live** — ignore unknown/closed peers.
2. **Turn ownership** — sender must be the match's active player; otherwise a
   non-fatal error is sent and the input dropped.
3. **Round matches** — `msg.round == active round` (drops stale/replayed input).
4. **In range** — `0 <= note <= 7`, `index == submitted.length()` (no skipping,
   no rewriting history).
5. **Not over** — reject input once the turn/match has ended.
6. **Rate sanity** — inputs ≥ ~60 ms apart, never before `turn_start`; dropped
   otherwise (basic anti-spam; no elaborate anti-cheat).
7. **Correctness** — `core_validate_note()` against the private ladder melody:
   match → advance `index`; if `index == length` the turn passed;
   mismatch → record `expected`, turn failed.
8. **Consequences** — pass: no life lost. Fail (`note_input` mismatch or
   `give_up`): `lives_left--`. When both players have attempted the current
   round, the match advances to the next round; turn order alternates each
   round for fairness.
9. **Match end** — a player at 0 lives is eliminated (opponent wins); a player
   completing round 24 wins outright; both eliminated in the same round → draw;
   a disconnect counts as resignation (opponent wins). No rejoin in the
   foundation.

Performance comparison is therefore inherent and server-owned: identical
ladder, identical lives, winner is the survivor — no separate scoring system to
build or trust.

Known, accepted limitation: because clients must receive the melody to play it,
a modified client could read the answers. Acceptable for the foundation;
hardening (server-side audio, hashed notes) is noted as future work only.

## 8. Round state and attempt state synchronization

- The server is the only writer of both players' states; clients only mirror.
- Every server message carries `seq`; clients drop anything older than what they
  applied, so late/duplicate packets can never rewind state.
- State transitions happen only inside validated server events — never client-
  side, never on a raw packet.
- `state_request` makes the server resend a full snapshot (`turn_start` + both
  attempt states) so a stalled or reconnected client converges on truth.
- **Offline path untouched:** single-player runs the same `game_core` functions
  locally and keeps its existing JSON save. Online matches keep no local save —
  the server owns match progress.

## 9. Existing offline files that can be reused

| File | Reuse |
|---|---|
| `include/tone_utils.nvgt` | unchanged — note playback + speaker test, used by both modes |
| `include/menu_music.nvgt` | unchanged — menu music system |
| `melody_memory.nvgt` | keeps the whole shell; its inline gameplay lines move to `game_core.nvgt` and are *called* from here. Adds one "Online game" menu item + online match loop. Single-player flow and JSON save unchanged. |
| `menu.nvgt`, `speech.nvgt` | unchanged — online screens and speech use the same accessible UI |
| `settings.nvgt` / save files | offline only; the online mode never reads or writes them |

The melody-generation rule and note comparison currently inside `play_game` /
`play_round` become `game_core` functions — the *same* code the server validates
with.

## 10. New files / systems required

| File | Role |
|---|---|
| `include/game_core.nvgt` | **Pure gameplay.** State structs, melody-ladder generation, note validation, lives/round transitions. No network, audio, speech, or file IO. |
| `include/net_protocol.nvgt` | Message-type constants, envelope build/parse, protocol version. Shared by client and server. |
| `include/net_client.nvgt` | Client transport: connect, poll `network.request()`, queue inbound events, typed send helpers. |
| `melody_memory_server.nvgt` | The server executable: lobby/match table (2 players per match), fixed ladders, authoritative attempt states, validation, dispatch. |
| `melody_memory.nvgt` (modified) | "Online game" menu item, direct-connect screen, online match loop (turn playing + opponent announcements). |

No new third-party dependencies; NVGT's built-in `network` + `json_object`
cover everything.

## 11. How this avoids rewriting the existing offline game later

- **One rulebook, two callers.** Offline and the server both call `game_core`;
  rule changes are made once and inherited by both modes.
- **Presentation is shared.** Speech and audio live in the shell; the online
  loop reuses the same playback/feedback functions as offline.
- **Networking stays at the edges.** `game_core` contains no network types, so
  future features (spectators, co-op, reconnection) never touch gameplay.
- **Additive client change.** The only offline-visible edits are one menu item
  and the move of gameplay lines into `game_core` — the single-player flow and
  save file behave exactly as before.
- **Staged path.** Later stages (rematches, simple stats server-side, extra
  match rules) extend `game_core` and the protocol without re-touching what is
  built here.

---

## Out of scope (explicitly not implemented)

Authentication, accounts, friends, matchmaking, chat, leaderboards, cloud
saves, NAT traversal, reconnection. Direct host/port connect only.
