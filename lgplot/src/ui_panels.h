/*
 * UI Panels
 * ImGui panel drawing functions.
 */
#pragma once

#include "imgui.h"
#include <string>

namespace lgplot {

// Panel drawing functions
void draw_controls_panel();
void draw_calibration_panel();
void draw_snapshot_panel();
void draw_spectrum_chart();
void draw_console_panel();

// Snapshot history viewer
void draw_history_viewer_panel();
void draw_history_chart();
void scan_snapshot_folders();
bool load_snapshot_history(int index);

// Layout
void setup_default_docking_layout(ImGuiID dockspace_id);

// Calibration persistence
void save_calibration();
void load_calibration();

// Snapshot functions
void freeze_frame();
void unfreeze_frame();
bool export_snapshot();

// Peak detection
void detect_peaks();

// Project management
void scan_projects();
void create_project(const char *name, const char *description);
void save_project_json(int project_index);
std::string get_current_project_folder();
void draw_new_project_popup();
void draw_exit_dialog();

} // namespace lgplot
