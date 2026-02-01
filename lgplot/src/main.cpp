/*
 * TCD1304 CCD Spectrum Analyzer - Desktop Application
 * ====================================================
 * Real-time visualization of CCD sensor data received via USB Serial or UDP.
 *
 * Features:
 * - ImGui docking layout with Controls, Spectrum Chart, and Console panels
 * - Dual mode: USB Serial or WiFi UDP receiver
 * - ImPlot for high-performance spectrum visualization
 * - Custom layout.ini for persistent user docking preferences
 */

// Windows APIs - Must be included BEFORE GLFW to avoid APIENTRY redefinition
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <winsock2.h>
#include <ws2tcpip.h>
#pragma comment(lib, "ws2_32.lib")

#include "imgui.h"
#include "imgui_impl_glfw.h"
#include "imgui_impl_opengl3.h"
#include "implot.h"

#define GL_SILENCE_DEPRECATION
#include <GLFW/glfw3.h>

#include <fstream>

// Application modules
#include "app_state.h"
#include "config.h"
#include "connection.h"
#include "console.h"
#include "ui_panels.h"

#if defined(_MSC_VER) && (_MSC_VER >= 1900) &&                                 \
    !defined(IMGUI_DISABLE_WIN32_FUNCTIONS)
#pragma comment(lib, "legacy_stdio_definitions")
#endif

using namespace lgplot;

static void glfw_error_callback(int error, const char *description) {
  fprintf(stderr, "GLFW Error %d: %s\n", error, description);
}

int main(int, char **) {
  glfwSetErrorCallback(glfw_error_callback);
  if (!glfwInit())
    return 1;

  const char *glsl_version = "#version 130";
  glfwWindowHint(GLFW_CONTEXT_VERSION_MAJOR, 3);
  glfwWindowHint(GLFW_CONTEXT_VERSION_MINOR, 0);

  GLFWwindow *window = glfwCreateWindow(
      1400, 900, "TCD1304 CCD Spectrum Analyzer", nullptr, nullptr);
  if (window == nullptr)
    return 1;
  glfwMakeContextCurrent(window);
  glfwSwapInterval(1);

  IMGUI_CHECKVERSION();
  ImGui::CreateContext();
  ImPlot::CreateContext();

  ImGuiIO &io = ImGui::GetIO();
  io.ConfigFlags |= ImGuiConfigFlags_NavEnableKeyboard;
  io.ConfigFlags |= ImGuiConfigFlags_DockingEnable;
  io.ConfigFlags |= ImGuiConfigFlags_ViewportsEnable;
  io.IniFilename = LAYOUT_INI_FILE;

  ImGui::StyleColorsDark();
  ImPlot::StyleColorsDark();

  ImGuiStyle &style = ImGui::GetStyle();
  if (io.ConfigFlags & ImGuiConfigFlags_ViewportsEnable) {
    style.WindowRounding = 0.0f;
    style.Colors[ImGuiCol_WindowBg].w = 1.0f;
  }

  ImGui_ImplGlfw_InitForOpenGL(window, true);
  ImGui_ImplOpenGL3_Init(glsl_version);

  bool first_run = !std::ifstream(LAYOUT_INI_FILE).good();

  // Load saved calibration
  load_calibration();

  // Scan for existing projects
  scan_projects();
  scan_snapshot_folders();

  log_message("TCD1304 CCD Spectrum Analyzer started");
  log_message("Select USB (COM port) or UDP (WiFi) connection");

  while (!glfwWindowShouldClose(window)) {
    glfwPollEvents();

    if (glfwGetWindowAttrib(window, GLFW_ICONIFIED) != 0) {
      ImGui_ImplGlfw_Sleep(10);
      continue;
    }

    ImGui_ImplOpenGL3_NewFrame();
    ImGui_ImplGlfw_NewFrame();
    ImGui::NewFrame();

    ImGuiID dockspace_id =
        ImGui::DockSpaceOverViewport(0, ImGui::GetMainViewport());

    if (first_run) {
      setup_default_docking_layout(dockspace_id);
      first_run = false;
    }

    draw_controls_panel();
    draw_calibration_panel();
    draw_snapshot_panel();
    draw_history_viewer_panel();
    draw_spectrum_chart();
    draw_history_chart();
    draw_console_panel();

    // Popup dialogs
    draw_new_project_popup();
    draw_exit_dialog();

    ImGui::Render();
    int display_w, display_h;
    glfwGetFramebufferSize(window, &display_w, &display_h);
    glViewport(0, 0, display_w, display_h);
    glClearColor(0.1f, 0.1f, 0.12f, 1.0f);
    glClear(GL_COLOR_BUFFER_BIT);
    ImGui_ImplOpenGL3_RenderDrawData(ImGui::GetDrawData());

    if (io.ConfigFlags & ImGuiConfigFlags_ViewportsEnable) {
      GLFWwindow *backup_current_context = glfwGetCurrentContext();
      ImGui::UpdatePlatformWindows();
      ImGui::RenderPlatformWindowsDefault();
      glfwMakeContextCurrent(backup_current_context);
    }

    glfwSwapBuffers(window);

    // Handle exit with save dialog
    if (g_app.should_exit) {
      break;
    }
  }

  stop_receiver();
  save_calibration(); // Save calibration on exit

  ImGui_ImplOpenGL3_Shutdown();
  ImGui_ImplGlfw_Shutdown();
  ImPlot::DestroyContext();
  ImGui::DestroyContext();

  glfwDestroyWindow(window);
  glfwTerminate();

  return 0;
}
