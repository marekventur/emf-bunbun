# BunBun 🐰

A tiny pixel bunny that lives on your [EMF Tildagon badge](https://tildagon.badge.emfcamp.org/).
Pet it, feed it, dress it in new colours — and keep it happy while you
wander the camp.

All pixel art hand-drawn by Marek Ventur.

## What it does

- **Chills** on your badge as an always-on companion: blinks, and now and
  then lazily flops an ear.
- **Gets hungry** every 2–3 hours: ear droops, eyes go sleepy, and the
  LED ring slowly breathes orange — the badge faces outward, so people
  around you will tell you your bunny needs feeding.
- **Feed it** and it munches a big carrot back to happiness.
- **Pet it** for one of three reactions: floating hearts, twinkling gold
  stars, or a snappy little jump. Pet it too much and it needs a nap.
- **Stroke it** (2026 boards): brush across the touch pads — the ear on
  the side you stroke flops toward your hand.
- **Idle personality**: it blinks, glances around, lazily flops an ear,
  and drifts off for little naps when left alone.
- **Battery peek**: press A for battery % and a time-remaining estimate
  learned from your badge's real drain rate.
- **Flip-to-face-me** (2026 boards): lift the badge to look at it and
  the bunny flips round to face you.
- **Four hand-picked colour palettes** (carol, choco, sky, berry), each
  with a matching day or night background.

## Controls

Buttons as labelled on the badge:

| Button | Action |
|--------|--------|
| A | battery peek |
| C | pet |
| D | change colours |
| E | feed |
| F | exit |
| keyboard "B" | summon BunBun from any app (keeb hexpansion) |

Tip: put `BunBun` in a file called `autoexec.bat` at the root of the
badge filesystem and the badge boots straight into BunBun.

(And one secret button. Explorers welcome.)

## Install

Get it from the [Tildagon app store](https://apps.badge.emfcamp.org/) —
search for **BunBun**.

## Development

The app is one file, `app.py`, drawn entirely with chunky pixel-art
sprites (see `art/` for the original drawings).

To run it on a badge over USB (needs `pip install mpremote`):

```sh
mpremote mkdir apps
mpremote mkdir apps/bunny
mpremote cp app.py :/apps/bunny/app.py
mpremote cp __init__.py :/apps/bunny/__init__.py
mpremote cp metadata.json :/apps/bunny/metadata.json
mpremote reset
```

To iterate quickly, use the desktop simulator from
[badge-2024-software](https://github.com/emfcamp/badge-2024-software):
clone it, copy `app.py`, `__init__.py`, and `metadata.json` into
`sim/apps/bunny/`, then run the sim (see its README). Note the sim runs
CPython while the badge runs MicroPython — always test on hardware too.

## License

MIT
