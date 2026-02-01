/*
 * Console Logging Implementation
 */
#include "console.h"
#include "app_state.h"

#include <chrono>
#include <cstdarg>
#include <cstdio>
#include <ctime>

namespace lgplot {

void log_message(const char *fmt, ...) {
  char buffer[512];
  va_list args;
  va_start(args, fmt);
  vsnprintf(buffer, sizeof(buffer), fmt, args);
  va_end(args);

  auto now = std::chrono::system_clock::now();
  auto time = std::chrono::system_clock::to_time_t(now);
  tm local_tm;
  localtime_s(&local_tm, &time);

  char time_str[32];
  strftime(time_str, sizeof(time_str), "%H:%M:%S", &local_tm);

  std::string msg = std::string("[") + time_str + "] " + buffer;

  std::lock_guard<std::mutex> lock(g_app.log_mutex);
  g_app.console_log.push_back(msg);
  if (g_app.console_log.size() > MAX_LOG_LINES) {
    g_app.console_log.pop_front();
  }
}

} // namespace lgplot
