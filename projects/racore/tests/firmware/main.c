#include <stdint.h>

#define KAI_MAGIC 0x4B4D54
#define KAI_ID_OFF 0x000
#define KAI_CTRL_OFF 0x008
#define KAI_STATUS_OFF 0x00C

// Memory Map
#define SCRATCHPAD_BASE 0x10000000
#define DMA_BASE        0x20000000
#define PTAHCORE_BASE   0x30000000

volatile uint32_t* const DMA = (volatile uint32_t*)DMA_BASE;
volatile uint32_t* const PTAHCORE = (volatile uint32_t*)PTAHCORE_BASE;

void main() {
    // Basic test: Read PtahCore ID
    uint32_t id = PTAHCORE[KAI_ID_OFF / 4];
    
    if ((id & 0xFFFFFF) == KAI_MAGIC) {
        // success
        PTAHCORE[KAI_CTRL_OFF / 4] = 0; 
    }

    // Infinite loop
    while (1) {
        // WFI or halt equivalent
    }
}
