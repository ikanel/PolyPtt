<script lang="ts" setup>
import { ref } from 'vue'

const isRecording = ref(false)

let mediaStream: MediaStream | null = null
let audioContext: AudioContext | null = null
let processor: ScriptProcessorNode | null = null
let websocket: WebSocket | null = null

function floatTo16BitPCM(input: Float32Array): Int16Array {
  const output = new Int16Array(input.length)
  for (let i = 0; i < input.length; i++) {
    let s = Math.max(-1, Math.min(1, input[i]))
    output[i] = s < 0 ? s * 0x8000 : s * 0x7fff
  }
  return output
}

function resampleBuffer(audioBuffer: AudioBuffer, targetSampleRate = 16000): Promise<AudioBuffer> {
  const offlineCtx = new OfflineAudioContext(
    1,
    Math.ceil(audioBuffer.duration * targetSampleRate),
    targetSampleRate,
  )
  const source = offlineCtx.createBufferSource()
  source.buffer = audioBuffer
  source.connect(offlineCtx.destination)
  source.start()
  return offlineCtx.startRendering()
}

async function startRecording(): Promise<void> {
  websocket = new WebSocket('ws://localhost:8080')
  websocket.binaryType = 'arraybuffer'

  mediaStream = await navigator.mediaDevices.getUserMedia({ audio: true })
  audioContext = new AudioContext({ sampleRate: 44100 })

  const source = audioContext.createMediaStreamSource(mediaStream)
  processor = audioContext.createScriptProcessor(4096, 1, 1)

  source.connect(processor)
  processor.connect(audioContext.destination)

  processor.onaudioprocess = async (e: AudioProcessingEvent) => {
    if (!websocket || websocket.readyState !== WebSocket.OPEN) return

    const input = e.inputBuffer.getChannelData(0)
    const buffer = audioContext!.createBuffer(1, input.length, audioContext!.sampleRate)
    buffer.copyToChannel(input, 0)

    try {
      const resampledBuffer = await resampleBuffer(buffer, 16000)
      const resampled = resampledBuffer.getChannelData(0)
      const pcm16 = floatTo16BitPCM(resampled)

      websocket.send(pcm16.buffer)
    } catch (err) {
      console.error('Resampling error:', err)
    }
  }

  isRecording.value = true
}

function stopRecording(): void {
  processor?.disconnect()
  mediaStream?.getTracks().forEach((t) => t.stop())
  audioContext?.close()
  websocket?.close()

  processor = null
  audioContext = null
  mediaStream = null
  websocket = null
  isRecording.value = false
}

function toggleRecording(): void {
  isRecording.value ? stopRecording() : startRecording()
}
</script>

<style scoped>
body {
  font-family: sans-serif;
}
</style>
<template>
  <div class="p-4">
    <h1 class="text-xl font-bold">16kHz PCM Mic Streamer</h1>
    <button @click="toggleRecording" class="mt-4 px-4 py-2 bg-blue-600 text-white rounded">
      {{ isRecording ? 'Stop Recording' : 'Start Recording' }}
    </button>
  </div>
</template>

<style scoped>
header {
  line-height: 1.5;
}

.logo {
  display: block;
  margin: 0 auto 2rem;
}

@media (min-width: 1024px) {
  header {
    display: flex;
    place-items: center;
    padding-right: calc(var(--section-gap) / 2);
  }

  .logo {
    margin: 0 2rem 0 0;
  }

  header .wrapper {
    display: flex;
    place-items: flex-start;
    flex-wrap: wrap;
  }
}
</style>
