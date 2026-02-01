# TCD1304 CCD Synchronization Fix

## Problem Summary
The CCD data shows step changes at different positions in each frame, indicating DMA buffer position is not aligned with ICG timing. With uniform light, all pixels should show similar values.

## Root Cause Analysis - 4 Project Comparison
After analyzing 4 successful reference projects, here is the comprehensive comparison:

| Project | MCU | Data Acquisition | DMA Mode | ICG Sync Method |
| :--- | :--- | :--- | :--- | :--- |
| Your Implementation | STM32H743 | ADC + DMA | Circular ❌ | Tries to copy at ICG but buffer drifts |
| tcd1304-driver-master | STM32F4 | ADC + DMA | Normal ✓ | `HAL_ADC_Start_DMA()` in TIM2 callback |
| tcd1304ap-stm32-ccdview | STM32F401 | ADC + DMA | Normal ✓ | Start DMA in `HAL_TIM_PWM_PulseFinishedCallback` on ICG |
| Dr. Nelson's 16-bit | Teensy 4 (iMXRT1060) | SPI ADC | N/A | FlexPWM + SPI interrupt per pixel |

### Key Insight
All working STM32 projects use Normal (non-circular) DMA mode and restart DMA fresh on each ICG pulse.

Dr. Nelson's comprehensive project uses a completely different approach with FlexPWM timing generator and SPI-based ADC readout - achieving scientific-grade linear response with 16-bit precision. Key learnings from his README:

* Uses "convert" signal synchronized to pixel clock
* SPI reads each pixel immediately after ADC conversion
* No DMA buffer synchronization issue because data is read pixel-by-pixel

## Reference Project Approach (Working)

### tcd1304-driver-master
```c
void HAL_TIM_PeriodElapsedCallback(TIM_HandleTypeDef *htim) {
  if (htim != &htim2) return;
  
  // Start DMA fresh on each ICG period
  if (curr_reading >= 6) {
    HAL_ADC_Start_DMA(&hadc1, (uint32_t*) CCDBuf, CCDBufSz);
  }
  curr_reading++;
}
```

### tcd1304ap-stm32-ccdview
```c
void HAL_TIM_PWM_PulseFinishedCallback(TIM_HandleTypeDef *htim) {
  if (htim->Instance == TIM5) {  // ICG timer
    // Start DMA + ADC trigger on ICG falling edge
    start_data_timer();  // This calls HAL_ADC_Start_DMA()
  }
}
void HAL_ADC_ConvCpltCallback(ADC_HandleTypeDef* hadc) {
  // Stop data timer when DMA complete
  stop_data_timer();
  write_data(&husart1, buffer);  // Send data
}
```

## Proposed Fix
### Change 1: Switch to Non-Circular DMA
Modify ADC DMA configuration to use `DMA_NORMAL` mode instead of `DMA_CIRCULAR`.

**[MODIFY]** `stm32h7xx_hal_msp.c`
* Change `hdma_adc1.Init.Mode = DMA_CIRCULAR` to `hdma_adc1.Init.Mode = DMA_NORMAL`

### Change 2: Start DMA on ICG Interrupt
Modify TIM2 callback to start fresh DMA transfer on each ICG period.

**[MODIFY]** `main.c`
```c
void HAL_TIM_PeriodElapsedCallback(TIM_HandleTypeDef *htim) {
  if (htim->Instance == TIM1) {
    HAL_IncTick();
  }
  
  if (htim->Instance == TIM2) {  // ICG interrupt
    // Previous frame is complete - copy and send
    if (frame_ready) {
      // Data already copied, just mark for transmission
    }
    
    // Start fresh DMA for next frame
    HAL_ADC_Start_DMA(&hadc1, (uint32_t *)Buffer_A, CCD_BUFFER_SIZE);
  }
}
```

### Change 3: Use DMA Complete Callback for Frame Ready
Use `HAL_ADC_ConvCpltCallback` to know when frame capture is complete.

```c
void HAL_ADC_ConvCpltCallback(ADC_HandleTypeDef *hadc) {
  if (hadc->Instance == ADC1) {
    // Frame capture complete - copy to transmission buffer
    ccd_frame.magic = 0xABCD;
    ccd_frame.frame_num = frame_counter++;
    memcpy(ccd_frame.pixels, (void *)Buffer_A, CCD_BUFFER_SIZE * 2);
    frame_ready = 1;
  }
}
```

### Change 4: Remove DMA Start from Initialization
DMA should only start on ICG interrupt, not during initialization.

## Verification Plan
1. Build and flash firmware
2. Run Python plotter with "Single Shot" capture
3. With uniform light, all pixels should show similar values (no step changes)
4. Check FPS is ~30+ (ICG period determines frame rate)

### Alternative: Software Frame Alignment
If hardware sync proves difficult, implement software frame alignment in Python:
* Detect the dummy pixel region (first 32 + last 14 pixels have different values)
* Rotate the array to align the dummy pixels to the correct positions
