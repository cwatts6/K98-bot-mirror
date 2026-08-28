# Codex Chat Starter — King of All Britain KVK Card Background

Execute the attached **Codex Task Pack — King of All Britain KVK Card Background** in one pass.

The supplied production asset is:

```text
King_of_All_Britain_Stats_Card.png
```

Copy it byte-for-byte to:

```text
assets/kvk/cards/King_of_All_Britain_Stats_Card.png
```

Locked asset contract:

- dimensions: `1180 × 640`
- SHA-256: `987be4495471936db491d25d00bb3eb9c23e259a86ed02d3e46b361fa3b6d605`
- do not recompress, resave, crop, recolour, or otherwise modify it

Implement the narrow production change:

1. Add `"king of all britain"` to `MODE_BACKGROUNDS` in both:
   - `kvk/rendering/kvk_stats_card_renderer.py`
   - `kvk/rendering/kvk_targets_card_renderer.py`
2. Point both entries to `King_of_All_Britain_Stats_Card.png`.
3. Preserve existing normalisation and fallback order.
4. Add focused tests for both resolvers, normalised variants, asset dimensions, King of All Britain rendering, and unknown-mode fallback.
5. Render and visually inspect local Stats, More Stats, and Targets smoke artifacts.
6. Run the selected validators/tests, PR review, and the routed Codex Security **Changes review with Deep Off**.
7. Create a branch, commit, push, and PR against `K98-bot-mirror/main`.
8. Do not merge, promote, or deploy. Return the complete handoff defined by the task pack.

Keep the PR strictly scoped. No SQL, command, payload, publication-state, layout, typography, or broad renderer-refactor changes are authorised.
