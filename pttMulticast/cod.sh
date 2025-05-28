#!/bin/bash
files=(1 2 3 4 5 6 7 8 9)
codecs=("alaw" "mulaw" "s16be" "s16le")
#codecs=("alaw" "mulaw" )

#kbps=(16 24 32 40)
kbps=(24)


for k in "${kbps[@]}"; do
  for c in "${codecs[@]}"; do
    for f in "${files[@]}"; do

      echo "ffplay -autoexit -f $c  -b:a 16000  phone_$/{k}_${f}.pcm"
      ffplay -autoexit -f $c -b:a 24000  -ar 8000  phone_${k}_${f}.pcm
     # -b:a 16000  -ar 16000
    done
  done
done
#g722 g726 g726le  G.723.1 G.729

