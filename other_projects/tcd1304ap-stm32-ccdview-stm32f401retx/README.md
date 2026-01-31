# tcd1304ap-stm32-ccdview (STM32F401RETx)



this is firmware for STM32F401RETx microcontrollers that reads pixel data from the TCD1304AP linear CCD sensor and transmits it in realtime over UART

there is an included `ccdview.py` which visualises this data

![ccdview](https://i.imgur.com/LIap1Z3.gif)

there is also `spectrometer.py` which is a modified version of `ccdview.py` that functions as a spectrometer

![spectrometer](https://i.imgur.com/xxWJ7ws.png)

this is an STM32CubeIDE project and uses the STM32F4xx hardware abstraction layer

#### pinouts (NUCLEO F401RE)
| signal | device | stm32 pin | dev board pin | comments |
| --- | --- | --- | --- | --- |
| fM | TIM3-CH3 | PB0 | A3 | to 74HC04 |
| SH | TIM2-CH2 | PA1 | A1 | to 74HC04 |
| ICG | TIM5-CH1 | PA0 | A0 | to 74HC04 |
| DATA | TIM4-CH4 | PB9 | D14 | triggers the ADC -- only for debug |
| OS | ADC1 | PC0 | A5 | input from OS line |
| TX | USART1 | PA9 | D8 | to PC running ccdview.py |
| RX | USART1 | PA10 | D2 | not currently used |

`PC13` or the `B1` button on the NUCLEO F401RE board will start/stop the image acquisition

#### parameters
in `Core/Src/main.c` you will find

    volatile uint8_t exposure = 20;

you can calculate the exposure time like so `exposure*3.7ms = total exposure time`

the minimum exposure value for a 2MHz `fM` is 2, or 7.388ms

    volatile uint8_t avg = 1;

setting this value to >1 will average multiple exposures before sending the data over USART1

> note: sending the 3694 pixels over USART1 at 500000 baud takes ~150ms, so if your total exposure time is much less than this, you might as well average a couple exposures before sending them

#### constants

`Core/Inc/consts.h` contains the following constants

| constant | value | description |
| --- | --- | --- |
| CPU_freq | 84000000 | the frequency of your STM32 chip |
| CCD_freq | 2000000 | the master clock frequency (fM) |
| NUM_PIXELS | 3694 | number of pixels on the CCD |
| BAUD_RATE | 500000 | the USART1 baud rate |

#### ccdview.py usage

you can launch the realtime visualisation script like so:

`python3 ccdview.py <DEVICE> <BAUD RATE>`

`python3 ccdview.py /dev/ttyUSB0 500000`

the usage for `spectrometer.py` is the same