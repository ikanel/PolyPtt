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
    void decode(std::string outfile, uint8_t encoding, uint8_t packing,int bitrate) {

        const char *infile = "/Users/ikanel/code/PolycomPTT/pttMulticast/phone.g726";
        //const char *outfile = "/Users/ikanel/code/PolycomPTT/pttMulticast/phone.pcm";

        std::string s = "/Users/ikanel/code/PolycomPTT/pttMulticast/phone_24_";
        s+=outfile;
        FILE *fin = fopen(infile, "rb");
        FILE *fout = fopen(s.c_str(), "wb");
        if (!fin || !fout) {
            perror("File error");
            return;
        }


        g726_state_t *g726 =g726_init(NULL, bitrate, encoding, packing);

        uint8_t input[BLOCK_SIZE];
        int16_t output[BLOCK_SIZE*4];

        size_t bytesRead;
        int bytesDecoded;

        while ((bytesRead = fread(input, 1, BLOCK_SIZE, fin)) > 0) {
                bytesDecoded = g726_decode(g726, output, input,bytesRead);
                fwrite(output, sizeof(int16_t), bytesDecoded, fout);
        }
        fclose(fin);
        fclose(fout);
    }
}

int main() {
    // TIP Press <shortcut actionId="RenameElement"/> when your caret is at the
    // <b>lang</b> variable name to see how CLion can help you rename it.
    auto lang = "C++";
    std::cout << "Hello and welcome to " << lang << "!\n";
    /*
    decode("1.pcm", G726_ENCODING_LINEAR, G726_PACKING_LEFT,16000);
    decode("2.pcm", G726_ENCODING_LINEAR, G726_PACKING_LEFT,24000);
    decode("3.pcm", G726_ENCODING_LINEAR, G726_PACKING_LEFT,32000);
    decode("4.pcm", G726_ENCODING_LINEAR, G726_PACKING_LEFT,40000);

    decode("5.pcm", G726_ENCODING_LINEAR, G726_PACKING_NONE,16000);
    decode("6.pcm", G726_ENCODING_LINEAR, G726_PACKING_NONE,24000);
    decode("7.pcm", G726_ENCODING_LINEAR, G726_PACKING_NONE,32000);
    decode("8.pcm", G726_ENCODING_LINEAR, G726_PACKING_NONE,40000);
*/




    decode("1.pcm", G726_ENCODING_ALAW, G726_PACKING_RIGHT,24000);
    decode("2.pcm",G726_ENCODING_LINEAR, G726_PACKING_RIGHT,24000);
    decode("3.pcm",G726_ENCODING_ULAW, G726_PACKING_RIGHT,24000);

    decode("4.pcm", G726_ENCODING_LINEAR, G726_PACKING_LEFT,24000);
    decode("5.pcm", G726_ENCODING_ALAW, G726_PACKING_LEFT,24000);
    decode("6.pcm", G726_ENCODING_ULAW, G726_PACKING_LEFT,24000);

    decode("7.pcm", G726_ENCODING_LINEAR, G726_PACKING_NONE,24000);
    decode("8.pcm",G726_ENCODING_ALAW, G726_PACKING_NONE,24000);
    decode("9.pcm", G726_ENCODING_ULAW, G726_PACKING_NONE,24000);

    return 0;
}
