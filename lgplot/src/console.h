/*
 * Console Logging Module
 * Thread-safe logging to the console panel.
 */
#pragma once

namespace lgplot {

// Log a formatted message to the console panel
void log_message(const char* fmt, ...);

} // namespace lgplot
