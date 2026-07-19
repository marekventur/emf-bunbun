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
- **Four hand-picked colour palettes** (carol, choco, sky, berry), each
  with a matching day or night background.

## Controls

Buttons as labelled on the badge:

| Button | Action |
|--------|--------|
| C | pet |
| D | change colours |
| E | feed |
| F | exit |

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
