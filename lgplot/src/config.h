/*
 * Application Configuration
 * Contains global constants and configuration settings.
 */
#pragma once

#include <cstddef>
#include <cstdint>

namespace lgplot {

// Network Configuration
constexpr int UDP_PORT = 8080;
constexpr int CCD_PIXEL_COUNT = 3694;

// Serial Configuration (Partner's protocol)
constexpr int USB_BAUD_RATE = 1000000;    // 1 Mbps to match Processing code
constexpr uint8_t USB_FRAME_START = 0x11; // New data frame indicator
constexpr uint8_t USB_PIXEL_START = 0xA5; // Pixel data start byte
constexpr uint8_t USB_PIXEL_END = 0x5A;   // Pixel data stop byte

// UI Configuration
constexpr const char *LAYOUT_INI_FILE = "lgplot_layout.ini";
constexpr size_t MAX_LOG_LINES = 200;

// Connection modes
enum class ConnectionMode { None = 0, UDP, USB };

} // namespace lgplot
