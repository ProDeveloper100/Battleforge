# ⚡ BATTLE FORGE

> **A cyberpunk infinite survival shooter — built entirely in Python with zero external assets.**

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=flat-square&logo=python)
![Pygame](https://img.shields.io/badge/Pygame-2.5%2B-green?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey?style=flat-square)

---

## 🎮 What is Battle Forge?

Battle Forge is a single-file cyberpunk arcade survival shooter built with Python and Pygame. You play as a cybernetic soldier running through an infinite procedurally generated neon world, fighting off waves of enemies, collecting power-ups, and surviving boss encounters.

There are **no image files, no sprites, no art assets** in this project. Every single visual — the player, enemies, bosses, platforms, particles, glowing effects, and menus — is drawn entirely through Pygame's drawing API using pure code, shapes, and math.

---

## 🚀 Quick Start

### Install dependencies
```bash
pip install pygame noise
```

### Run the game
```bash
python game.py
```

That's it. No setup, no config files, no asset folders.

---

## 🕹️ Controls

| Key | Action |
|-----|--------|
| `A` / `←` | Move left |
| `D` / `→` | Move right |
| `Space` / `↑` | Jump |
| `Space` (x2) | Double jump |
| `Left Click` / `F` | Shoot toward cursor |
| `ESC` | Pause |

---

## ✨ Features

### World
- **Infinite procedural generation** using Perlin Noise — the map never repeats
- **6 unique biomes** that transition seamlessly as you run: Neon City, Toxic Wasteland, Crimson Desert, Frozen Void, Cyberpunk Industrial, Neon Jungle
- Each biome has unique colours, platform styles, and enemy spawn pools
- Parallax star background with chunk loading/unloading for performance

### Enemies
| Enemy | Behaviour |
|-------|-----------|
| 🦇 Bat | Swarms and dives, sine-wave flight path |
| 🐟 Fish | Patrols platforms and leaps at high speed |
| 🚜 Tank | Slow ground walker, shoots homing projectiles |
| 🚁 Drone | Flies in sine wave, fires missiles |

- All enemy bullets have a **400px range limit** — they can't chase you forever
- Difficulty scales gradually over time — gentle start, intense later

### Boss System
- A massive **Cyber-Mech boss** spawns every 90 seconds
- Three rotating attack patterns: chase, horizontal strafe, hover and shoot
- Triple-spread bullet attacks
- Full-width boss HP bar on HUD
- Drops 3 power-ups on death

### Power-ups
| Power-up | Effect | Duration |
|----------|--------|----------|
| 🛡️ Shield | Absorbs one hit completely | 8s |
| ⚡ Rapid Fire | Halves shoot cooldown | 10s |
| 💥 Double DMG | Bullets deal 2x damage | 10s |
| 💨 Speed Boost | Increases movement speed | 8s |
| ❤️ +2 HP | Instant heal | Instant |

- Drop from killed enemies (12% chance) and spawn naturally in the world
- Active power-ups shown as a draining bar at the bottom-left of the HUD

### Visual Effects
- Neon glow on every entity, platform, and bullet
- Particle system for explosions, hits, deaths, and power-up pickups
- Camera shake on damage
- Floating damage numbers
- Screen-wide power-up flash on pickup
- Animated city background on menus with flickering windows and rising particles
- Cinematic intro sequence with city silhouette, lightning bolts, and lore text

### Game Systems
- Username login and local leaderboard (saves to `battle_forge_scores.json`)
- One best score per username — no duplicate entries
- Combo kill system with score multipliers
- Pause menu with resume, restart, and quit to menu
- Game Over screen with new high score detection

---

## 🗂️ Project Structure

```
battle_forge/
│
└── game.py          # The entire game — 1,200+ lines, single file
```

No folders. No assets. No config. One file runs everything.

---

## 🛠️ How It's Built

### Procedural Generation
The world is generated using **Perlin Noise** (via the `noise` library, with a pure-Python fallback if unavailable). Terrain height is calculated per tile, platforms are placed based on noise values, and biomes cycle every 15 chunks. Chunks are loaded on demand and unloaded when out of range to keep memory usage flat.

### Procedural Sprites
Every sprite is a `pygame.Surface` drawn at runtime using `pygame.draw` primitives:
- `pygame.draw.rect` — armour plates, platforms, UI
- `pygame.draw.circle` — drone rotors, glow effects, particles
- `pygame.draw.polygon` — bat wings, fish tails, lightning
- `pygame.draw.ellipse` — fish body, bat body
- `pygame.draw.line` — gun barrels, jetpack vents, scanlines
- `math.sin` for bobbing, flapping, pulsing, and exhaust animations

### Particle System
A lightweight particle system handles all visual effects. Each particle has position, velocity, gravity, size, colour, fade, and lifetime. The system preallocates nothing — particles are appended and filtered each frame.

### Camera
Smooth follow camera with configurable lag (10% lerp per frame) and a shake system that triggers on damage.

### Chunk System
The world is divided into 20-tile chunks. Only 4-5 chunks are active at any time. Chunks outside the visible range plus a 3-chunk buffer are evicted from memory.

---

## 📦 Dependencies

| Library | Purpose | Required |
|---------|---------|----------|
| `pygame` | Rendering, input, audio | ✅ Yes |
| `noise` | Perlin noise terrain generation | ❌ Optional (has fallback) |

```bash
pip install pygame noise
```

---

## 🖥️ Compatibility

Tested on:
- Ubuntu 22.04 / 24.04 with Python 3.12 and Pygame 2.5.2
- Windows 10/11 with Python 3.12

> **Note:** Python 3.14 is not currently supported by Pygame. Use Python 3.10, 3.11, or 3.12 for best compatibility.

---

## 🎯 Difficulty Curve

| Time | Difficulty Multiplier | Spawn Interval | Notes |
|------|----------------------|----------------|-------|
| 0:00 | ×1.0 | 3.0s | Calm start |
| 0:45 | ×1.02 | 2.7s | First enemies ramp up |
| 1:30 | ×1.03 | ~2.4s | **First boss spawns** |
| 3:00 | ×1.07 | ~1.8s | Second boss, faster enemies |
| 5:00+ | ×1.11+ | ~1.2s | Intense — multiple enemies per spawn |

---

## 📸 Screenshots

> Login screen with animated city background, scrolling buildings, flickering windows, and rising neon particles.

> In-game: procedural neon platforms, enemy sprites, power-up hexagons, combo counter, and HUD.

> Boss encounter: full-width HP bar, triple spread bullets, and death explosion with 50+ particles.

---

## 🤝 Contributing

Pull requests are welcome. If you want to add:
- New enemy types
- Additional boss patterns
- New biomes
- Sound effects

Open an issue first so we can discuss the approach.

---

## 📄 License

MIT License — free to use, modify, and distribute.

---

## 👤 Author

Built by **Aarez** as a personal project to learn Pygame, procedural generation, and game architecture.

> *"Every visual you see is drawn by code — no assets, no downloads, just math."*
