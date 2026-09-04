# Design

The screens are source in this repository, not only a hosted canvas. `artboards/` holds one
`.dc.html` per screen — plain HTML with inline styles, readable and diffable — and `generator/`
holds the Python that produces them. Regenerating is the test that the design still builds:

```sh
cd design/generator && for f in *.py; do case $f in _*) continue;; esac; python3 "$f"; done
```

Every generator writes into `../artboards/`, whatever directory it is run from.

## Layout

| Path | What it is |
|---|---|
| `artboards/*.dc.html` | One screen each. The design source of truth. |
| `canvas.json` | Page and position manifest: which artboards sit on which page, and where. |
| `generator/_common.py` | Tokens, icon set, chip and avatar helpers, and the artboard wrapper. **Every value comes from here.** |
| `generator/_shell.py` | Top bar, navigation rail, toolbar and tabs — the frame every screen shares. |
| `generator/_charts.py` | Inline SVG chart primitives: line, bar, stacked, donut, gauge, sparkline. |
| `generator/<screens>.py` | One file per group of screens. |

## Rules

- **Tokens only.** Colours, spacing, radii, type sizes and control heights come from the CSS custom
  properties in `_common.py`, which carry the values F062 specifies. A raw hex or pixel value in a
  screen is a bug — the token sheet and the ticket must agree.
- **One visual system.** Every element is a themed MUI component in the built product; these
  artboards reproduce that anatomy. No screen introduces a second look.
- **Real content.** Screens use plausible task names, people, dates and numbers at real density, so
  a reviewer can judge whether the layout is usable rather than whether it is pretty.
- **Both themes and the brand hue are levers.** Each artboard declares a `theme` and `brand` tweak;
  the brand hue re-derives every accent through `color-mix`.
- **Every file stays under 500 lines**, like the rest of the repository.

## Relationship to the tickets

A feature ticket's section 3 names its artboard. The ticket is the contract and the artboard is the
picture: when they disagree, the ticket wins and the artboard is corrected. `docs/design-canvas.md`
links the published canvas, which is a rendering of exactly these files.

## Publishing

The canvas is seeded from `artboards/` plus `canvas.json` and published as an Artifact. Seed from
inside `artboards/` with a copy of the manifest beside the files:

```sh
cd design/artboards && cp ../canvas.json . \
  && node <skill>/seed-canvas.mjs --template <skill>/payload.template.html \
       --out /tmp/opshub-canvas.html --title "OpsHub Design System" \
       $(python3 -c "import json;print(' '.join('--artboard '+a['file'] for a in json.load(open('canvas.json'))['artboards']))") \
       --canvas canvas.json && rm canvas.json
```

The seeded output is a build artifact and is deliberately not committed — it embeds a 2 MB editor and
is regenerated on every change.
