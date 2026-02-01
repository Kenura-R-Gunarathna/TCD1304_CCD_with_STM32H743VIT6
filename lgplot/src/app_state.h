/*
 * Application State
 * Shared state container for the application.
 */
#pragma once

#include "config.h"

#include <atomic>
#include <deque>
#include <mutex>
#include <string>
#include <thread>
#include <vector>

#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <winsock2.h>

namespace lgplot {

// Detected peak structure
struct Peak {
  int pixel_index;
  float wavelength;
  float intensity;
};

// Calibration point structure
struct CalibrationPoint {
  int pixel_index;
  float wavelength_nm;
};

// Project structure for organizing snapshots
struct Project {
  std::string name;        // Display name
  std::string folder_name; // Folder name (sanitized)
  std::string description;
  std::string created; // ISO timestamp
};

struct AppState {
  // Spectrum data
  std::vector<float> spectrum_data;
  std::vector<float> pixel_indices;
  std::mutex data_mutex;

  // Frozen snapshot data (for export)
  std::vector<float> snapshot_data;
  bool is_frozen = false;

  // Connection
  ConnectionMode connection_mode = ConnectionMode::None;
  std::atomic<bool> receiver_running{false};
  std::thread receiver_thread;

  // UDP
  SOCKET udp_socket = INVALID_SOCKET;

  // USB Serial
  HANDLE serial_handle = INVALID_HANDLE_VALUE;
  char com_port[32] = "COM3";

  // Statistics
  std::atomic<uint32_t> packets_received{0};
  std::atomic<uint32_t> last_sequence{0};
  std::atomic<float> packets_per_second{0.0f};

  // Console log
  std::deque<std::string> console_log;
  std::mutex log_mutex;

  // UI state
  bool auto_fit_y = true;
  float y_min = 0.0f;
  float y_max = 4095.0f;
  bool show_grid = true;
  bool dark_theme = true;
  bool show_wavelength_axis = true;
  bool show_peaks = true;

  // Wavelength Calibration
  // Formula: wavelength_nm = cal_A * pixel_index + cal_B
  float cal_A = 0.0f; // nm per pixel (dispersion)
  float cal_B = 0.0f; // nm at pixel 0 (offset)
  bool is_calibrated = false;

  // Calibration input UI
  CalibrationPoint cal_point1 = {0, 400.0f};
  CalibrationPoint cal_point2 = {3694, 800.0f};

  // Peak detection
  std::vector<Peak> detected_peaks;
  float peak_threshold = 500.0f; // Minimum intensity for peak
  int peak_min_distance = 50;    // Minimum pixels between peaks

  // Snapshot history viewer
  std::vector<std::string> snapshot_timestamps; // Available snapshot folders
  std::vector<float> history_data; // Currently loaded historical data
  std::vector<Peak> history_peaks; // Peaks from loaded history
  int history_selected_index = -1; // Currently selected snapshot (-1 = none)
  bool history_loaded = false;     // Is history data loaded?

  // Export settings
  char export_folder[256] = "snapshots";

  // Project management
  std::vector<Project> projects;          // Available projects
  int current_project_index = 0;          // Selected project (0 = Default)
  char new_project_name[128] = "";        // For "New Project" input
  char new_project_description[512] = ""; // For "New Project" input
  bool show_new_project_popup = false;    // Show new project dialog
  bool project_needs_save = false;        // Unsaved project changes
  bool show_exit_dialog = false;          // Show exit confirmation dialog
  bool should_exit = false;               // App should exit after dialog

  AppState() {
    spectrum_data.resize(CCD_PIXEL_COUNT, 0.0f);
    snapshot_data.resize(CCD_PIXEL_COUNT, 0.0f);
    pixel_indices.resize(CCD_PIXEL_COUNT);
    for (int i = 0; i < CCD_PIXEL_COUNT; ++i) {
      pixel_indices[i] = static_cast<float>(i);
    }
  }

  // Calculate wavelength from pixel index
  float wavelength_from_pixel(int pixel) const {
    if (!is_calibrated)
      return 0.0f;
    return cal_A * pixel + cal_B;
  }

  // Calculate calibration coefficients from two points
  void calibrate() {
    float dp =
        static_cast<float>(cal_point2.pixel_index - cal_point1.pixel_index);
    if (dp != 0) {
      cal_A = (cal_point2.wavelength_nm - cal_point1.wavelength_nm) / dp;
      cal_B = cal_point1.wavelength_nm - cal_A * cal_point1.pixel_index;
      is_calibrated = true;
    }
  }
};

// Global application state
extern AppState g_app;

} // namespace lgplot
