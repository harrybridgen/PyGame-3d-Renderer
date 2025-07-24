[Youtube Demo](https://youtu.be/y7Pkr4E4Nlk)
![blocks](blocks.img)
---
# Software 3D Block Renderer

By Harry Bridgen

## Overview

This is a Python-based 3D rendering engine built from scratch using Pygame. It implements a software rasterizer to render a block world in real time, without using any hardware-accelerated 3D APIs like OpenGL or DirectX.

Inspired by voxel games and basic 3D engines, this project demonstrates real-time projection, face culling, camera movement, and custom 3D transformations entirely in Python.

## Features

- Software 3D projection using manual matrix math
- Real-time rendering of block faces and terrain grid
- Face culling based on visibility and adjacency
- Yaw/pitch camera with mouse look and smoothing
- Block placement at the center of the screen
- Dynamic ground generation based on camera position
- Toggleable face rendering
- Adjustable window resizing and FPS display

## Controls

- **W/A/S/D** — Move forward/left/backward/right
- **Space / Left Shift** — Move camera up/down
- **Mouse Movement** — Look around
- **Left Click** — Place a new block in front of the camera
- **F** — Toggle filled face rendering
- **Esc** — Quit

## Technical Details

- Manual matrix and vector math for camera transformation
- Projection via custom FOV and aspect ratio handling
- Visibility and clipping checks for near/far planes
- Block face visibility determined by adjacency and normal-backface tests
- Performance-optimized using spatial hashing and deferred face sorting

## Requirements

- Python 3.x
- `pygame`

Install dependencies with:

```bash
pip install pygame
```

Run the program:

```bash
python your_script.py
```

## Notes

This project was developed independently as a personal experiment in low-level 3D rendering concepts using only 2D drawing capabilities. It serves both as a technical exercise and a foundation for further exploration into software-based 3D engines.

## Author

Harry Bridgen  
[github.com/harrybridgen](https://github.com/harrybridgen)

---
![one](https://github.com/harrybridgen/PyGame-3d-Renderer/assets/105605342/786999f5-da1f-4d7c-a725-bb35cab301b3)
![two](https://github.com/harrybridgen/PyGame-3d-Renderer/assets/105605342/f2aad66e-e364-4a01-95b1-32326483c959)
