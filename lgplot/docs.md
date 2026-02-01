# Code Documentation - Spectrum Analyzer

This document provides a detailed, beginner-friendly explanation of how the code works.

## Table of Contents

1. [Overview](#overview)
2. [Program Structure](#program-structure)
3. [Initialization](#initialization)
4. [Main Loop](#main-loop)
5. [UI Components](#ui-components)
6. [Data Generation](#data-generation)
7. [Rendering](#rendering)
8. [Key Concepts](#key-concepts)

---

## Overview

This application creates a real-time spectrum analyzer with two main components:
- **Controls Panel**: Interactive sliders and buttons to adjust parameters
- **Live Spectrum Plot**: Animated graph showing a simulated signal

The program uses:
- **GLFW**: Creates the window and handles input
- **OpenGL**: Renders graphics
- **ImGui**: Creates the user interface
- **ImPlot**: Draws the plot/graph

---

## Program Structure

### Headers and Includes

```cpp
#include <glad/glad.h>           // OpenGL function loader
#include <GLFW/glfw3.h>          // Window management
#include "imgui.h"               // Core ImGui
#include "imgui_impl_glfw.h"     // ImGui GLFW backend
#include "imgui_impl_opengl3.h"  // ImGui OpenGL3 backend
#include "implot.h"              // Plotting library
#include <iostream>              // Console output
#include <cmath>                 // Math functions (sin, exp)
#include <vector>                // Dynamic arrays
#include <random>                // Random number generation
```

**Why these libraries?**
- `glad` must come before `GLFW/glfw3.h` to properly load OpenGL functions
- ImGui backends connect ImGui to GLFW and OpenGL
- Standard library headers provide math and data structures

---

## Initialization

### 1. GLFW Setup

```cpp
glfwSetErrorCallback(glfw_error_callback);
if (!glfwInit()) {
    cerr << "Failed to initialize GLFW" << endl;
    return -1;
}
```

**What's happening:**
- Sets up error reporting for GLFW
- Initializes the GLFW library
- Returns error if initialization fails

### 2. Window Creation

```cpp
const char* glsl_version = "#version 130";
glfwWindowHint(GLFW_CONTEXT_VERSION_MAJOR, 3);
glfwWindowHint(GLFW_CONTEXT_VERSION_MINOR, 0);

GLFWwindow* window = glfwCreateWindow(1600, 900, "Spectrum Analyzer", nullptr, nullptr);
```

**What's happening:**
- Specifies OpenGL version 3.0 and GLSL version 130
- Creates a 1600x900 pixel window
- Window title is "Spectrum Analyzer - ImGui + ImPlot"

### 3. OpenGL Context

```cpp
glfwMakeContextCurrent(window);
glfwSwapInterval(1); // Enable vsync

if (!gladLoadGLLoader((GLADloadproc)glfwGetProcAddress)) {
    cerr << "Failed to initialize GLAD" << endl;
    return -1;
}
```

**What's happening:**
- Makes the window's OpenGL context current
- Enables VSync (limits frame rate to monitor refresh rate)
- Loads OpenGL functions using GLAD

### 4. ImGui Initialization

```cpp
IMGUI_CHECKVERSION();
ImGui::CreateContext();
ImPlot::CreateContext();
ImGuiIO& io = ImGui::GetIO();
io.ConfigFlags |= ImGuiConfigFlags_NavEnableKeyboard;
io.ConfigFlags |= ImGuiConfigFlags_NavEnableGamepad;
io.ConfigFlags |= ImGuiConfigFlags_DockingEnable;
```

**What's happening:**
- Verifies ImGui version compatibility
- Creates ImGui and ImPlot contexts (required for both libraries)
- Gets the IO object to configure ImGui
- Enables keyboard navigation, gamepad support, and window docking

### 5. ImGui Styling and Backend

```cpp
ImGui::StyleColorsDark();
ImGui_ImplGlfw_InitForOpenGL(window, true);
ImGui_ImplOpenGL3_Init(glsl_version);
```

**What's happening:**
- Applies the dark color theme
- Initializes ImGui's GLFW backend (handles input)
- Initializes ImGui's OpenGL3 backend (handles rendering)

---

## Main Loop

The main loop runs continuously until the window is closed:

```cpp
while (!glfwWindowShouldClose(window)) {
    // 1. Poll events
    glfwPollEvents();
    
    // 2. Start ImGui frame
    ImGui_ImplOpenGL3_NewFrame();
    ImGui_ImplGlfw_NewFrame();
    ImGui::NewFrame();
    
    // 3. Update animation time
    if (animate) {
        time += 0.016f; // ~60 FPS
    }
    
    // 4. Generate data
    // ... (generate spectrum data)
    
    // 5. Create UI
    // ... (create dockspace, controls, plot)
    
    // 6. Render
    ImGui::Render();
    glClear(GL_COLOR_BUFFER_BIT);
    ImGui_ImplOpenGL3_RenderDrawData(ImGui::GetDrawData());
    glfwSwapBuffers(window);
}
```

### Loop Breakdown

**Step 1: Poll Events**
- Processes keyboard, mouse, and window events
- Must be called every frame

**Step 2: Start ImGui Frame**
- Prepares ImGui for a new frame
- Must call all three `NewFrame()` functions in this order

**Step 3: Update Time**
- Increments time for animation (0.016s ≈ 60 FPS)
- Only updates if animation is enabled

**Step 4: Generate Data**
- Creates the spectrum data points (explained below)

**Step 5: Create UI**
- Defines all windows, buttons, sliders, and plots

**Step 6: Render**
- `ImGui::Render()`: Finalizes ImGui drawing data
- `glClear()`: Clears the screen
- `ImGui_ImplOpenGL3_RenderDrawData()`: Draws ImGui to screen
- `glfwSwapBuffers()`: Displays the rendered frame

---

## Data Generation

### Signal Components

The spectrum is composed of three parts:

#### 1. Gaussian Peak (Main Signal)

```cpp
float animated_peak = peak_position + 5.0f * sin(time * 0.5f);
float gaussian = amplitude * exp(-pow(x - animated_peak, 2) / (2 * peak_width * peak_width));
```

**What's happening:**
- `animated_peak`: Peak position wobbles using sine wave
- `gaussian`: Bell curve formula: `A * e^(-(x-μ)²/(2σ²))`
  - `A` = amplitude
  - `μ` = peak position (animated)
  - `σ` = peak width

#### 2. Sine Wave Component

```cpp
float sine_component = 0.2f * amplitude * sin(frequency * x * 0.1f + time);
```

**What's happening:**
- Adds a sine wave to the signal
- Frequency controlled by slider
- Phase shifts with time for animation

#### 3. Random Noise

```cpp
std::random_device rd;
std::mt19937 gen(rd());
std::uniform_real_distribution<float> noise_dist(-1.0f, 1.0f);

float noise = noise_level * noise_dist(gen);
```

**What's happening:**
- Uses Mersenne Twister random number generator
- Generates random values between -1 and 1
- Scaled by `noise_level` slider

#### Final Signal

```cpp
y_data[i] = gaussian + sine_component + noise;
```

All three components are added together for each data point.

---

## UI Components

### Dockspace (Fullscreen Container)

```cpp
ImGuiViewport* viewport = ImGui::GetMainViewport();
ImGui::SetNextWindowPos(viewport->WorkPos);
ImGui::SetNextWindowSize(viewport->WorkSize);
```

**What's happening:**
- Gets the main viewport (entire window area)
- Sets next window to fill the entire viewport
- Creates an invisible fullscreen window for docking

### Controls Panel

```cpp
ImGui::Begin("Controls");

ImGui::Checkbox("Animate", &animate);
ImGui::SliderFloat("Frequency", &frequency, 0.1f, 20.0f, "%.1f Hz");
ImGui::ColorEdit3("Background Color", (float*)&clear_color);

if (ImGui::Button("Reset Parameters")) {
    // Reset values
}

ImGui::End();
```

**Widget Types:**
- `Checkbox`: Boolean toggle
- `SliderFloat`: Drag slider for float values
  - Parameters: label, variable pointer, min, max, format
- `ColorEdit3`: RGB color picker
- `Button`: Clickable button (returns true when clicked)
- `Text`: Display text
- `Separator`: Horizontal line

### Live Spectrum Plot

```cpp
if (ImPlot::BeginPlot("Spectrum Analyzer", ImVec2(-1, -1))) {
    ImPlot::SetupAxes("Frequency (Hz)", "Amplitude");
    ImPlot::SetupAxisLimits(ImAxis_X1, 0, num_points, ImGuiCond_Always);
    ImPlot::SetupAxisLimits(ImAxis_Y1, -0.5, amplitude * 1.5 + 0.5, ImGuiCond_Always);
    
    ImPlot::PlotLine("Signal", x_data.data(), y_data.data(), num_points);
    ImPlot::PlotShaded("Signal", x_data.data(), y_data.data(), num_points);
    
    ImPlot::EndPlot();
}
```

**What's happening:**
- `BeginPlot()`: Starts a plot region (size -1,-1 = fill available space)
- `SetupAxes()`: Labels for X and Y axes
- `SetupAxisLimits()`: Sets axis ranges
  - `ImGuiCond_Always`: Update every frame
- `PlotLine()`: Draws the line graph
- `PlotShaded()`: Fills area under the curve
- `EndPlot()`: Finishes the plot

---

## Rendering

### Clear Screen

```cpp
int display_w, display_h;
glfwGetFramebufferSize(window, &display_w, &display_h);
glViewport(0, 0, display_w, display_h);
glClearColor(clear_color.x, clear_color.y, clear_color.z, clear_color.w);
glClear(GL_COLOR_BUFFER_BIT);
```

**What's happening:**
- Gets the actual framebuffer size (handles high-DPI displays)
- Sets OpenGL viewport to match window size
- Sets clear color (background)
- Clears the screen

### Draw ImGui

```cpp
ImGui_ImplOpenGL3_RenderDrawData(ImGui::GetDrawData());
glfwSwapBuffers(window);
```

**What's happening:**
- Renders all ImGui draw commands to OpenGL
- Swaps front/back buffers (displays the frame)

---

## Key Concepts

### Immediate Mode GUI

ImGui uses "immediate mode" - you describe your UI every frame:

```cpp
// Every frame, you write:
if (ImGui::Button("Click Me")) {
    // Handle click
}
```

This is different from "retained mode" where you create widgets once and update them.

### Frame Rate Independence

```cpp
time += 0.016f; // Assumes 60 FPS
```

**Better approach** (frame-rate independent):
```cpp
time += ImGui::GetIO().DeltaTime;
```

This makes animation speed consistent regardless of frame rate.

### Static Variables

```cpp
static float frequency = 5.0f;
```

`static` variables keep their value between function calls. This is how ImGui widgets remember their state.

### Data Ownership

```cpp
static std::vector<float> x_data(num_points);
static std::vector<float> y_data(num_points);
```

Data must persist between frames. Using `static` ensures the vectors aren't destroyed after each loop iteration.

### Pointers to Variables

```cpp
ImGui::SliderFloat("Frequency", &frequency, 0.1f, 20.0f);
```

The `&` passes the address of `frequency`. ImGui modifies the variable directly when you move the slider.

---

## Cleanup

```cpp
ImGui_ImplOpenGL3_Shutdown();
ImGui_ImplGlfw_Shutdown();
ImPlot::DestroyContext();
ImGui::DestroyContext();
glfwDestroyWindow(window);
glfwTerminate();
```

**What's happening:**
- Shuts down ImGui backends (in reverse order of initialization)
- Destroys ImPlot and ImGui contexts
- Destroys the window
- Terminates GLFW

**Important:** Always clean up in reverse order of initialization!

---

## Common Patterns

### Creating a Window

```cpp
ImGui::Begin("Window Title");
// ... widgets ...
ImGui::End();
```

### Conditional Rendering

```cpp
if (show_window) {
    ImGui::Begin("Optional Window", &show_window);
    // ... widgets ...
    ImGui::End();
}
```

The `&show_window` adds a close button that sets `show_window = false`.

### Styling

```cpp
ImGui::PushStyleVar(ImGuiStyleVar_WindowPadding, ImVec2(10, 10));
// ... widgets with custom padding ...
ImGui::PopStyleVar();
```

Always pop style changes after use!

---

## Further Learning

### Next Steps

1. **Modify the code**: Change colors, add new sliders, try different formulas
2. **Add features**: Save/load parameters, export data, add more plot types
3. **Explore ImGui demo**: Run `ImGui::ShowDemoWindow()` to see all widgets
4. **Read the source**: ImGui demo source code is excellent documentation

### Resources

- [ImGui Manual](https://github.com/ocornut/imgui/wiki)
- [ImPlot Demo](https://github.com/epezent/implot#demo)
- [LearnOpenGL](https://learnopengl.com/) - Understanding the graphics pipeline
- [The Cherno C++ Series](https://www.youtube.com/playlist?list=PLlrATfBNZ98dudnM48yfGUldqGD0S4FFb)

---

## Troubleshooting

### "Assertion failed" errors
- Usually means you forgot to call `Begin()` before widgets or `End()` after
- Check that every `Begin()` has a matching `End()`

### Plot not showing
- Make sure `BeginPlot()` returns true
- Check that data arrays have valid values
- Verify axis limits are reasonable

### Slow performance
- Reduce `num_points` (fewer data points)
- Disable VSync: `glfwSwapInterval(0)`
- Profile your code to find bottlenecks

---

**Happy coding!** 🚀
