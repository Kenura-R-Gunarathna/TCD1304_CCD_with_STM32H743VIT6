"""
CCD Oscilloscope - DearPyGui Real-time Spectrum Viewer
Receives binary CCD frames from STM32 via USB CDC (COM port)

Frame format:
- 2 bytes: Magic (0xABCD)
- 2 bytes: Frame number
- 7388 bytes: 3694 x 16-bit pixels (little-endian)

Usage:
    pip install dearpygui pyserial numpy
    python ccd_oscilloscope.py
"""

import dearpygui.dearpygui as dpg
import serial
import serial.tools.list_ports
import struct
import numpy as np
import threading
import time
import os
from datetime import datetime

# Configuration
CCD_PIXELS = 3694
FRAME_HEADER_SIZE = 4
FRAME_SIZE = FRAME_HEADER_SIZE + CCD_PIXELS * 2  # 7392 bytes
MAGIC = 0xABCD
BAUD_RATE = 115200  # Doesn't matter for USB CDC, but required

# TCD1304 useful pixel range (excluding dummy pixels)
USEFUL_START = 32    # First light-sensitive pixel
USEFUL_END = 3679    # Last light-sensitive pixel (3648 pixels total)

class CCDReceiver:
    def __init__(self):
        self.pixels = np.zeros(CCD_PIXELS, dtype=np.uint16)
        self.frame_count = 0
        self.fps = 0
        self.running = True
        self.connected = False
        self.serial = None
        self.lock = threading.Lock()
        self.last_fps_time = time.time()
        self.fps_frame_count = 0
        self.frozen = False  # Pause updates
        self.avg_buffer = []  # For averaging
        self.frame_ready = False  # Only True when complete frame received
        self.last_frame_count = -1  # Track frame changes
        self.single_shot_pending = False  # For single shot capture
        self.recording = False  # Recording state
        self.recording_conditional = False  # Conditional recording (only when not frozen)
        self.recorded_frames = []  # Store frames for recording
        self.recording_file = None  # File handle for recording
        self.recording_dir = "recordings"  # Directory for saved recordings
        
    def find_stm32_port(self):
        """Find STM32 CDC COM port automatically"""
        ports = serial.tools.list_ports.comports()
        for port in ports:
            # STM32 CDC typically shows as "STMicroelectronics" or "USB Serial"
            if "STM" in port.description or "USB Serial" in port.description:
                return port.device
        # Return first available port if no STM32 found
        if ports:
            return ports[0].device
        return None
    
    def connect(self, port=None):
        """Connect to the STM32 CDC device"""
        # Close any existing connection first
        if self.serial and self.serial.is_open:
            try:
                self.serial.close()
            except:
                pass
        self.connected = False
        
        if port is None:
            port = self.find_stm32_port()
        
        if port is None:
            print("No COM port found!")
            return False
            
        try:
            self.serial = serial.Serial(port, BAUD_RATE, timeout=0.5)
            self.connected = True
            self.running = True
            print(f"Connected to {port}")
            return True
        except Exception as e:
            print(f"Failed to connect to {port}: {e}")
            self.connected = False
            return False
    
    def read_frame(self):
        """Read one frame from the serial port"""
        if not self.connected or self.serial is None:
            return False
            
        try:
            # Look for magic header
            while self.running:
                byte1 = self.serial.read(1)
                if len(byte1) == 0:
                    return False
                    
                if byte1[0] == 0xCD:  # First byte of magic (little-endian)
                    byte2 = self.serial.read(1)
                    if len(byte2) > 0 and byte2[0] == 0xAB:
                        # Found magic! Read rest of frame
                        data = self.serial.read(FRAME_SIZE - 2)
                        if len(data) == FRAME_SIZE - 2:
                            # Parse frame number
                            frame_num = struct.unpack('<H', data[0:2])[0]
                            
                            # Parse pixels
                            with self.lock:
                                self.pixels = np.frombuffer(data[2:], dtype=np.uint16).copy()
                                self.frame_count = frame_num
                                self.frame_ready = True  # Mark complete frame
                                
                                # Record frame if recording is active
                                if self.recording or (self.recording_conditional and not self.frozen):
                                    # Store frame data for saving
                                    frame_data = {
                                        'frame_num': frame_num,
                                        'timestamp': time.time(),
                                        'pixels': self.pixels.copy()
                                    }
                                    self.recorded_frames.append(frame_data)
                            
                            # Calculate FPS
                            self.fps_frame_count += 1
                            now = time.time()
                            if now - self.last_fps_time >= 1.0:
                                self.fps = self.fps_frame_count
                                self.fps_frame_count = 0
                                self.last_fps_time = now
                            
                            return True
        except Exception as e:
            print(f"Read error: {e}")
            return False
        
        return False
    
    def get_pixels(self):
        """Thread-safe pixel access"""
        with self.lock:
            return self.pixels.copy()
    
    def stop(self):
        """Stop receiver and close serial"""
        self.running = False
        if self.serial:
            self.serial.close()
    
    def start_recording(self, conditional=False):
        """Start recording frames"""
        with self.lock:
            self.recording = not conditional
            self.recording_conditional = conditional
            self.recorded_frames = []
        
        # Create recordings directory if it doesn't exist
        if not os.path.exists(self.recording_dir):
            os.makedirs(self.recording_dir)
    
    def stop_recording(self):
        """Stop recording and save frames to NumPy .npz file"""
        # Get frames and clear recording state thread-safely
        with self.lock:
            if not (self.recording or self.recording_conditional):
                return None
            
            if len(self.recorded_frames) == 0:
                self.recording = False
                self.recording_conditional = False
                return None
            
            # Copy frames for saving (release lock before file I/O)
            frames_to_save = self.recorded_frames.copy()
            self.recorded_frames = []
            self.recording = False
            self.recording_conditional = False
        
        # Generate filename with timestamp
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(self.recording_dir, f"ccd_recording_{ts}.npz")
        
        try:
            n_frames = len(frames_to_save)
            
            # Build 2D pixel array (frames × pixels)
            pixels_2d = np.zeros((n_frames, CCD_PIXELS), dtype=np.uint16)
            frame_numbers = np.zeros(n_frames, dtype=np.uint16)
            timestamps = np.zeros(n_frames, dtype=np.float64)
            
            for i, frame_data in enumerate(frames_to_save):
                pixels_2d[i, :] = frame_data['pixels']
                frame_numbers[i] = frame_data['frame_num']
                timestamps[i] = frame_data['timestamp']
            
            # Detect dropped frames (gaps in frame number sequence)
            frame_gaps = np.diff(frame_numbers.astype(np.int32))
            dropped_frames = []
            for i, gap in enumerate(frame_gaps):
                if gap != 1 and gap != -65535:  # Allow rollover (65535 -> 0)
                    # Frames were dropped between frame_numbers[i] and frame_numbers[i+1]
                    for missing in range(1, gap):
                        dropped_frames.append(int(frame_numbers[i]) + missing)
            
            # Calculate timing statistics
            dt = np.diff(timestamps) * 1000  # Convert to ms
            timing_stats = {
                'mean_interval_ms': float(np.mean(dt)) if len(dt) > 0 else 0,
                'std_interval_ms': float(np.std(dt)) if len(dt) > 0 else 0,
                'min_interval_ms': float(np.min(dt)) if len(dt) > 0 else 0,
                'max_interval_ms': float(np.max(dt)) if len(dt) > 0 else 0,
            }
            
            # Save as NumPy compressed archive
            np.savez_compressed(
                filename,
                pixels=pixels_2d,
                frame_numbers=frame_numbers,
                timestamps=timestamps,
                dropped_frames=np.array(dropped_frames, dtype=np.int32),
                timing_mean_ms=timing_stats['mean_interval_ms'],
                timing_std_ms=timing_stats['std_interval_ms']
            )
            
            # Print diagnostics
            print(f"\n=== Recording Saved: {filename} ===")
            print(f"Frames: {n_frames}, Shape: {pixels_2d.shape}")
            print(f"Frame timing: {timing_stats['mean_interval_ms']:.2f} ± {timing_stats['std_interval_ms']:.2f} ms")
            if dropped_frames:
                print(f"WARNING: {len(dropped_frames)} dropped frames detected!")
            else:
                print("Frame continuity: OK (no gaps)")
            
            return {
                'filename': filename,
                'n_frames': n_frames,
                'dropped_count': len(dropped_frames),
                'timing': timing_stats
            }
            
        except Exception as e:
            print(f"Error saving recording: {e}")
            return None

# Global receiver instance
receiver = CCDReceiver()

def receiver_thread():
    """Background thread for continuous reading"""
    while receiver.running:
        if receiver.connected:
            receiver.read_frame()
        else:
            time.sleep(0.5)

def align_frame(pixels, threshold_percentile=30):
    """
    Align frame by detecting the steepest edge (gradient).
    Works even when signal is saturated - finds the largest change in signal.
    
    The TCD1304 has ~32 dark/dummy pixels at the start followed by active pixels.
    We detect this boundary using gradient analysis.
    
    Args:
        pixels: numpy array of pixel values
        threshold_percentile: fallback percentile (used if gradient fails)
    
    Returns:
        aligned pixels (shifted to consistent start position)
    """
    # Method 1: Find steepest rising edge using gradient
    # This works regardless of absolute signal level
    gradient = np.diff(pixels[:300].astype(np.float32))  # First 300 samples
    
    # Find the largest positive gradient (rising edge)
    max_gradient_idx = np.argmax(gradient)
    
    # Check if gradient is significant (not just noise)
    max_gradient_val = gradient[max_gradient_idx]
    median_gradient = np.median(np.abs(gradient))
    
    if max_gradient_val > median_gradient * 3:  # Significant edge found
        transition_idx = max_gradient_idx + 1  # +1 because diff shifts by 1
    else:
        # Fallback: use threshold method
        threshold = np.percentile(pixels, threshold_percentile)
        above_threshold = pixels > threshold
        
        transition_idx = None
        for i in range(1, min(200, len(pixels))):
            if not above_threshold[i-1] and above_threshold[i]:
                transition_idx = i
                break
        
        if transition_idx is None:
            # Last resort: find minimum in first 100 pixels
            transition_idx = np.argmin(pixels[:100])
    
    # Target alignment: transition should be at pixel 32 (USEFUL_START)
    shift = USEFUL_START - transition_idx
    
    # Roll the array to align
    if shift != 0:
        aligned = np.roll(pixels, shift)
        return aligned
    return pixels

def update_plot():
    """Update the plot with latest data - only on complete frames"""
    if not receiver.connected or receiver.frozen:
        return
    
    # Only update when a NEW complete frame is ready
    if not receiver.frame_ready:
        return
    
    with receiver.lock:
        receiver.frame_ready = False  # Mark as consumed
        pixels = receiver.pixels.copy()
        frame_num = receiver.frame_count
    
    # Invert if checkbox is checked (TCD1304 output is inverted)
    if dpg.get_value("invert_check"):
        pixels = 65535 - pixels
    
    # Apply frame alignment if checkbox is checked
    if dpg.does_item_exist("align_check") and dpg.get_value("align_check"):
        pixels = align_frame(pixels)
    
    # Use useful pixel range only if checkbox is checked
    if dpg.get_value("useful_only"):
        x_data = list(range(USEFUL_START, USEFUL_END))
        y_data = pixels[USEFUL_START:USEFUL_END].tolist()
        dpg.set_axis_limits("x_axis", USEFUL_START, USEFUL_END)
    else:
        x_data = list(range(CCD_PIXELS))
        y_data = pixels.tolist()
        dpg.set_axis_limits("x_axis", 0, CCD_PIXELS)
    
    dpg.set_value("spectrum", [x_data, y_data])
    current_time = time.strftime("%H:%M:%S", time.localtime())
    
    # Update status with recording info (thread-safe)
    with receiver.lock:
        record_info = ""
        if receiver.recording:
            record_info = f" | REC: ALL ({len(receiver.recorded_frames)} frames)"
        elif receiver.recording_conditional:
            record_info = f" | REC: RUN ({len(receiver.recorded_frames)} frames)"
    
    dpg.set_value("status_text", f"Frame: {frame_num} | FPS: {receiver.fps} | Time: {current_time}{record_info}")
    
    # Handle single shot - freeze after displaying this frame
    if receiver.single_shot_pending:
        receiver.single_shot_pending = False
        receiver.frozen = True

def connect_callback():
    """Called when Connect button is pressed"""
    port = dpg.get_value("port_input")
    if port is None or port.strip() == "":
        port = None  # Auto-detect
    if receiver.connect(port):
        dpg.set_value("status_text", f"Connected to {receiver.serial.port}")
    else:
        dpg.set_value("status_text", "Connection failed!")

def disconnect_callback():
    """Called when Disconnect button is pressed"""
    receiver.stop()
    dpg.set_value("status_text", "Disconnected")

def refresh_ports():
    """Refresh available COM ports"""
    ports = [p.device for p in serial.tools.list_ports.comports()]
    if ports:
        dpg.configure_item("port_input", default_value=ports[0])
        dpg.set_value("ports_list", f"Available: {', '.join(ports)}")
    else:
        dpg.set_value("ports_list", "No ports found")

# Create DearPyGui context
dpg.create_context()

# Create main window
with dpg.window(label="CCD Oscilloscope", tag="primary", width=1200, height=700):
    
    # Connection controls
    with dpg.group(horizontal=True):
        dpg.add_input_text(label="COM Port", tag="port_input", default_value="", width=100,
                          hint="Leave empty for auto-detect")
        dpg.add_button(label="Refresh", callback=refresh_ports)
        dpg.add_button(label="Connect", callback=connect_callback)
        dpg.add_button(label="Disconnect", callback=disconnect_callback)
        dpg.add_text("", tag="ports_list")
    
    # Status bar
    dpg.add_text("Status: Not connected", tag="status_text")
    dpg.add_separator()
    
    # Main plot
    with dpg.plot(label="CCD Spectrum", height=500, width=-1, tag="main_plot"):
        dpg.add_plot_legend()
        
        # X axis - Pixel index
        dpg.add_plot_axis(dpg.mvXAxis, label="Pixel Index", tag="x_axis")
        dpg.set_axis_limits("x_axis", 0, CCD_PIXELS)
        
        # Y axis - ADC value
        dpg.add_plot_axis(dpg.mvYAxis, label="ADC Value (16-bit)", tag="y_axis")
        dpg.set_axis_limits("y_axis", 0, 65535)
        
        # Spectrum line
        dpg.add_line_series(list(range(CCD_PIXELS)), 
                           [0] * CCD_PIXELS, 
                           label="Spectrum",
                           parent="y_axis", 
                           tag="spectrum")
    
    # Controls row 1: Signal processing
    with dpg.group(horizontal=True):
        dpg.add_checkbox(label="Invert Signal", default_value=True, tag="invert_check")
        dpg.add_checkbox(label="Useful Pixels Only (32-3679)", default_value=False, tag="useful_only")
        dpg.add_checkbox(label="Align Frames", default_value=True, tag="align_check")
        
    # Controls row 2: Capture control
    with dpg.group(horizontal=True):
        def single_shot():
            """Capture next frame and freeze"""
            receiver.frozen = False
            # Wait for next frame, then freeze
            receiver.single_shot_pending = True
        dpg.add_button(label="Single Shot", callback=single_shot)
        dpg.add_button(label="Run", callback=lambda: setattr(receiver, 'frozen', False))
        dpg.add_button(label="Stop", callback=lambda: setattr(receiver, 'frozen', True))
    
    # Controls row 3: Recording control
    with dpg.group(horizontal=True):
        def start_record_continuous():
            """Start recording all frames (continuous)"""
            receiver.start_recording(conditional=False)
            dpg.set_value("record_status", "Recording: ALL frames")
        
        def start_record_conditional():
            """Start recording only when chart is running"""
            receiver.start_recording(conditional=True)
            dpg.set_value("record_status", "Recording: Only when RUNNING")
        
        def stop_record():
            """Stop recording and save to file"""
            result = receiver.stop_recording()
            if result:
                status = f"Saved {result['n_frames']} frames to .npz"
                if result['dropped_count'] > 0:
                    status += f" | {result['dropped_count']} DROPPED!"
                else:
                    status += " | No gaps"
                status += f" | {result['timing']['mean_interval_ms']:.1f}ms/frame"
                dpg.set_value("record_status", status)
            else:
                dpg.set_value("record_status", "No frames recorded")
        
        dpg.add_button(label="Record (All)", callback=start_record_continuous)
        dpg.add_button(label="Record (Run Only)", callback=start_record_conditional)
        dpg.add_button(label="Stop Record", callback=stop_record)
        dpg.add_text("", tag="record_status")
    
    # Controls row 2: Y-axis
    with dpg.group(horizontal=True):
        dpg.add_text("Y-Axis Range:")
        dpg.add_slider_int(label="Max", default_value=65535, min_value=1000, max_value=65535,
                          callback=lambda s, a: dpg.set_axis_limits("y_axis", 0, a), width=200)
        dpg.add_checkbox(label="Auto-fit Y", default_value=False, tag="autofit_y")

# Configure viewport
dpg.create_viewport(title='CCD Oscilloscope - STM32 Binary Receiver', width=1250, height=750)
dpg.setup_dearpygui()
dpg.show_viewport()
dpg.set_primary_window("primary", True)

# Initial port refresh (NO auto-connect)
refresh_ports()

# Start receiver thread
recv_thread = threading.Thread(target=receiver_thread, daemon=True)
recv_thread.start()

# Main render loop
while dpg.is_dearpygui_running():
    update_plot()
    
    # Auto-fit Y axis if enabled
    if dpg.get_value("autofit_y") and receiver.connected:
        pixels = receiver.get_pixels()
        if len(pixels) > 0:
            max_val = max(np.max(pixels), 1000)
            dpg.set_axis_limits("y_axis", 0, int(max_val * 1.1))
    
    dpg.render_dearpygui_frame()

# Cleanup
receiver.stop()
dpg.destroy_context()
