# CCD Monitor

Python GUI for TCD1304 CCD Spectrometer, built with DearPyGui.

## Features
- Real-time spectral visualization (up to ~30 FPS).
- **Multi-Mode Control**: Switch between Fast, ONE-SHOT (Stable), and Long Exposure modes.
- **Robust Connection**: Handles USB disconnects without crashing.
- **Recording**: Save raw data to `.npz` files.

## Setup & Run

This project is managed with `uv`.

1. **Install Dependencies**:
   ```bash
   uv sync
   ```

2. **Run the Monitor**:
   ```bash
   uv run ccd_oscilloscope.py
   ```
