# CubeMX Configuration Notes

This file documents manual code changes that need to be reapplied after regenerating code from STM32CubeMX.

---

## Double-Buffer DMA Configuration

CubeMX doesn't directly support Double-Buffer DMA mode in the GUI. The following manual changes must be made after code generation:

### 1. Buffer Definitions (in `/* USER CODE BEGIN PV */`)

```c
// Double-Buffer DMA: Two buffers in SRAM3 (non-cached on H7)
__attribute__((section(".sram3"),
               aligned(32))) uint16_t Buffer_A[CCD_BUFFER_SIZE];
__attribute__((section(".sram3"),
               aligned(32))) uint16_t Buffer_B[CCD_BUFFER_SIZE];

// Pointer to the buffer that is SAFE to read
volatile uint16_t *ready_buffer = NULL;
```

### 2. DMA Callback (in `/* USER CODE BEGIN 0 */`)

```c
void HAL_ADC_ConvCpltCallback(ADC_HandleTypeDef *hadc) {
  // CT bit tells us which buffer DMA is NOW writing to
  if (DMA1_Stream0->CR & DMA_SxCR_CT) {
    ready_buffer = Buffer_A;  // DMA writing to B, A is safe
  } else {
    ready_buffer = Buffer_B;  // DMA writing to A, B is safe
  }
  buffer_updated = 1;
}
```

### 3. Enable Double-Buffer Mode (in `/* USER CODE BEGIN 2 */`)

**IMPORTANT**: DBM bit can only be modified when the stream is disabled!

```c
// Step 1: Start ADC DMA normally (HAL configures the stream)
HAL_ADC_Start_DMA(&hadc1, (uint32_t *)Buffer_A, CCD_BUFFER_SIZE);

// Step 2: Disable stream to modify DBM bit (required by reference manual)
DMA1_Stream0->CR &= ~DMA_SxCR_EN;
while (DMA1_Stream0->CR & DMA_SxCR_EN);  // Wait until disabled

// Step 3: Enable Double-Buffer mode and set second buffer address
DMA1_Stream0->CR |= DMA_SxCR_DBM;
DMA1_Stream0->M1AR = (uint32_t)Buffer_B;

// Step 4: Re-enable stream
DMA1_Stream0->CR |= DMA_SxCR_EN;
```

### 4. Update Send Function

Change `memcpy` source from old buffer name to `ready_buffer`:

```c
memcpy(ccd_frame.pixels, (const void *)ready_buffer, CCD_BUFFER_SIZE * 2);
```

---

## CubeMX Settings to Verify

### DMA Configuration
- **Mode**: Circular (required for double-buffer)
- **Data Width**: Half Word (16-bit)
- **Memory Increment**: Enable
- **Peripheral Increment**: Disable

### ADC1 Configuration  
- **External Trigger**: TIM4 CC4
- **Trigger Edge**: Rising
- **DMA Continuous Requests**: Enable
- **Conversion Data Management**: DMA Circular Mode

### NVIC Priorities
| Interrupt | Priority | Note |
|-----------|----------|------|
| DMA1_Stream0 | 4 | Higher priority for stable transfer |
| TIM2 | 5 | Lower priority for ICG pulses |

---

## Linker Script (.ld file)

Ensure SRAM3 is defined for the buffers:

```ld
.sram3 (NOLOAD) :
{
  . = ALIGN(32);
  *(.sram3)
  . = ALIGN(32);
} >RAM_D2
```

Or if using memory region directly:
```ld
MEMORY
{
  RAM_D2 (xrw) : ORIGIN = 0x30000000, LENGTH = 288K
}
```

---

## Quick Checklist After Code Regeneration

- [ ] Re-add `Buffer_A` and `Buffer_B` definitions
- [ ] Re-add `ready_buffer` pointer
- [ ] Re-add `HAL_ADC_ConvCpltCallback` with CT bit check
- [ ] Re-add DBM mode enable before `HAL_ADC_Start_DMA`
- [ ] Update `Send_CCD_Frame_Binary` to use `ready_buffer`
- [ ] Verify NVIC priorities are set correctly
