# lgplot - TCD1304 CCD Spectrum Analyzer

Real-time spectrum visualization for TCD1304 CCD sensor data. **CMake-based project** with clean Visual Studio integration.


## ✨ Features

- 🔌 **Dual Mode**: USB Serial (921600 baud) or WiFi UDP (port 8080)
- 📊 **Real-time Plotting**: 3694 pixels with ImPlot
- 🎨 **Docking UI**: Customizable ImGui panels
- 💾 **Persistent Layout**: Saved to `lgplot_layout.ini`
- 🧩 **Modular Code**: Clean `src/` structure

## 🏗️ Project Structure

```
lgplot/
├── main.cpp                 # Application entry point
├── src/
│   ├── config.h            # Constants & configuration
│   ├── app_state.h/cpp     # Application state
│   ├── console.h/cpp       # Logging system
│   ├── connection.h/cpp    # USB Serial & UDP receivers
│   └── ui_panels.h/cpp     # ImGui UI panels
├── CMakeLists.txt          # Build configuration
├── CMakePresets.json       # VS integration
└── vcpkg.json              # Dependencies
```

## 🚀 Quick Start

### Visual Studio

1. **Open Folder:**
   ```
   File → Open → Folder → Select: lgplot_cmake
   ```

2. **Select Configuration:**
   - Dropdown: "x64-debug" or "x64-release"

3. **Select Startup Item:**
   - Dropdown: "lgplot.exe"

4. **Build & Run:**
   - Press **F5**

### Command Line

```powershell
# Configure
cmake --preset x64-debug

# Build
cmake --build out/build/x64-debug

# Run
.\out\build\x64-debug\lgplot.exe
```

## 📦 Dependencies

Automatically installed via **vcpkg manifest mode**:

- **imgui** (docking, glfw, opengl3 bindings)
- **implot** (plotting library)
- **glfw3** (windowing)

No manual installation needed! vcpkg handles everything during CMake configure.

## 🎮 Usage

### USB Serial Mode

1. Connect ESP32 via USB
2. In Controls panel:
   - Enter COM port (e.g., "COM3")
   - Click "USB Connect"
3. View live spectrum

### WiFi UDP Mode

1. Connect to ESP32 WiFi: `CCD_TCD1304`
2. Click "UDP Connect (WiFi)"
3. View live spectrum

### UI Controls

- **Auto-fit Y Axis**: Automatic scaling
- **Y Min/Max**: Manual range control
- **Show Grid**: Toggle grid lines
- **Dark Theme**: Switch color scheme

## 🔧 Building from Scratch

### Prerequisites

- Visual Studio 2026 (or 2022+)
- CMake 3.10+
- vcpkg (integrated with VS)

### First Build

```powershell
# 1. Configure (downloads dependencies)
cmake --preset x64-debug

# 2. Build
cmake --build out/build/x64-debug

# 3. Run
.\out\build\x64-debug\lgplot.exe
```

## 🐛 Troubleshooting

### "Cannot find imgui.h"

**Solution:** Delete CMake cache
```powershell
Remove-Item -Recurse out
# Then reconfigure in VS: Project → Delete Cache and Reconfigure
```

### "Select Startup Item" error

**Solution:** 
1. Click startup item dropdown
2. Select "lgplot.exe"
3. Press F5

### vcpkg not installing

**Check environment:**
```powershell
echo $env:VCPKG_ROOT
# Should output: C:\vcpkg or VS integrated path
```

## 📝 Code Organization

### Modular Design

- **config.h**: All constants (ports, baud rates, pixel counts)
- **app_state**: Shared state (spectrum data, connection info)
- **console**: Thread-safe logging with timestamps
- **connection**: USB Serial and UDP receiver threads
- **ui_panels**: ImGui panels (Controls, Spectrum, Console)
- **main.cpp**: Initialization, main loop, cleanup

### Adding Features

1. **New constant**: Add to `src/config.h`
2. **New state**: Add to `src/app_state.h`
3. **New UI panel**: Add to `src/ui_panels.cpp`
4. **New connection type**: Add to `src/connection.cpp`

## 🔬 Testing

### Without Hardware

Use ESP32 dummy data mode (see `esp32/README.md`)

### With Hardware

1. Flash ESP32 firmware
2. Connect via USB or WiFi
3. Click connect button
4. Verify packet rate in Statistics panel

## 📊 Performance

- **Rendering**: 60 FPS (vsync)
- **Packet Rate**: ~100 packets/sec (UDP)
- **Latency**: <10ms (USB Serial)
- **Memory**: ~5MB runtime

## 🎨 Customization

### Layout

- Drag panel title bars to rearrange
- Dock to edges or as tabs
- Delete `lgplot_layout.ini` to reset

### Theme

Toggle "Dark Theme" checkbox in Controls panel

## 📄 License

MIT License

---

**Parent Project:** [ch2_fl](../README.md)
