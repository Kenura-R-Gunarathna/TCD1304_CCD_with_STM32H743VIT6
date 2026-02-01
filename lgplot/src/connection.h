/*
 * Connection Module
 * USB Serial and UDP receiver functionality.
 */
#pragma once

namespace lgplot {

// USB Serial
bool open_serial_port();
void close_serial_port();
bool start_usb_receiver();

// UDP
bool start_udp_receiver();

// General
void stop_receiver();

} // namespace lgplot
