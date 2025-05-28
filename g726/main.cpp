#include <iostream>
#include <spandsp.h>
#include <cstdio>
#include <string>
#include <cstdint>
#include <cstddef>


#define BLOCK_SIZE (90)

// TIP To <b>Run</b> code, press <shortcut actionId="Run"/> or
// click the <icon src="AllIcons.Actions.Execute"/> icon in the gutter.
extern "C" {
    int16_t decodeFromByteArray(const uint8_t* input, int16_t* output,  uint16_t blockSize,uint8_t encoding, uint8_t packing,int bitrate) {
        g726_state_t *g726 =g726_init(NULL, bitrate, encoding, packing);
        int16_t samplesDecoded;
        samplesDecoded = g726_decode(g726, output, input,blockSize);
        return  samplesDecoded;
    }
}

