# TCD1304 Synchronization Strategy & Reference Project Comparison

## 1. Executive Summary

We analyzed 4 successful reference projects to determine the best way to eliminate data flickering and achieve stable synchronization with the TCD1304 CCD sensor.

**Key Finding:** All working STM32 projects use **Normal (non-circular) DMA** mode and restart the DMA transfer freshly on each ICG (Integration Clear Gate) pulse. This prevents buffer drift which is the root cause of the current invalid data/flickering.

### 4-Project Comparison Table

| Project | MCU | Data Method | DMA Mode | ICG Sync Method |
|---------|-----|-------------|----------|-----------------|
| **Your Current Implementation** | STM32H743 | ADC + DMA | **Circular** ❌ | Tries to copy at ICG but buffer drifts |
| **tcd1304-driver-master** | STM32F4 | ADC + DMA | **Normal** ✓ | `HAL_ADC_Start_DMA()` in TIM2 callback |
| **tcd1304ap-stm32-ccdview** | STM32F401 | ADC + DMA | **Normal** ✓ | Start DMA in `HAL_TIM_PWM_PulseFinishedCallback` on ICG |
| **Dr. Nelson's 16-bit** | Teensy 4 | SPI ADC | N/A | FlexPWM + SPI interrupt per pixel |

---

## 2. Detailed Reference Analysis

### A. tcd1304ap-stm32-ccdview (RECOMMENDED)
This project offers the cleanest architecture for STM32.

*   **Logic**:
    1.  **ICG Pulse Ends**: `HAL_TIM_PWM_PulseFinishedCallback` fires.
    2.  **Start Capture**: Starts the "DATA" timer (which triggers ADC) and starts **fresh DMA** transfer (`HAL_ADC_Start_DMA`).
    3.  **DMA Complete**: `HAL_ADC_ConvCpltCallback` fires after N pixels.
    4.  **Stop Capture**: Stops the "DATA" timer.
*   **Why it works**: By treating each frame as a discrete "shot", the DMA buffer (`buffer[0]`) is mathematically guaranteed to correspond to the first pixel from the ADC every single time. There is no possibility of drift.

### B. tcd1304-driver-master
*   **Logic**: Uses Circular DMA but adds a "flush" logic. It counts ICG pulses and only starts the read on the 6th ICG.
*   **Drawback**: More complex state machine (flushing, counting). Still requires stopping/restarting DMA to stay synced.

### C. Dr. Nelson's Scientific-Grade Project (Teensy 4)
*   **Logic**: Does not use STM32-style DMA. Uses a high-speed Teensy 4 processor with a custom "FlexPWM" timing generator. The ADC is read via SPI (not internal ADC), and data is fetched pixel-by-pixel using interrupts or tight loops.
*   **Takeaway**: Confirms that strict synchronization (pixel-level control) is key to scientific linearity.

---

## 3. Recommended Implementation Plan for STM32H743

We will adapt the **tcd1304ap-stm32-ccdview** approach for your H743.

### Step 1: Configure DMA
In `stm32h7xx_hal_msp.c` (or via CubeMX settings if you regenerate):
- Change ADC DMA mode from `DMA_CIRCULAR` to `DMA_NORMAL`.

### Step 2: Implement ICG Sync Callback
In `main.c`, modify `HAL_TIM_PeriodElapsedCallback` (assuming TIM2 tracks ICG period):

```c
void HAL_TIM_PeriodElapsedCallback(TIM_HandleTypeDef *htim) {
  // Handle SysTick
  if (htim->Instance == TIM1) {
    HAL_IncTick();
  }

  // Handle ICG (Frame Start)
  if (htim->Instance == TIM2) {
    // 1. Clear any previous flags if needed
    
    // 2. Start the ADC Trigger Timer (TIM4)
    // This ensures ADC only runs/converts when we are ready
    HAL_TIM_PWM_Start(&htim4, TIM_CHANNEL_1); 

    // 3. Start Fresh DMA Transfer
    // This aligns the Start-Of-Buffer with the Start-Of-Frame
    HAL_ADC_Start_DMA(&hadc1, (uint32_t *)Buffer_A, CCD_BUFFER_SIZE);
  }
}
```

### Step 3: Implement Frame Complete Callback
In `main.c`:

```c
void HAL_ADC_ConvCpltCallback(ADC_HandleTypeDef *hadc) {
  if (hadc->Instance == ADC1) {
    // 1. Stop the ADC Trigger Timer (TIM4)
    // This prevents extra ADC conversions between frames
    HAL_TIM_PWM_Stop(&htim4, TIM_CHANNEL_1);

    // 2. Mark Frame as Ready
    // Since we are using a single buffer (Buffer_A) in Normal mode, 
    // we should copy it or send it now.
    
    // Example: Copy to USB buffer
    memcpy(ccd_frame.pixels, Buffer_A, CCD_BUFFER_SIZE * 2);
    ccd_frame.frame_num = frame_counter++;
    frame_ready = 1; 
  }
}
```

### Summary of Fix
1.  **Stop Continuous DMA**: It allows drift.
2.  **Start DMA on ICG**: Locks alignment.
3.  **Stop ADC on Completion**: Prevents overrun.

This ensures that `Buffer_A[0]` is **always** the first pixel of the frame, eliminating the flickering/shifting data.
