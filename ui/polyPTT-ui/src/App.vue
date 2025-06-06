<script lang="ts" setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
const isRecording = ref(false)
const isListening = ref(false)
const selectedTarget = ref('')
const channel = ref('1')

const connectionStatus = ref('Disconnected')

let mediaStream: MediaStream | null = null
let audioContext: AudioContext | null = null
let audioCtx: AudioContext

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

function initAudio(event) {
  if(event!=undefined)  isListening.value = true;
  audioCtx.resume()
}

async function startRecording(): Promise<void> {
  initAudio()
  if (websocket == undefined || websocket?.readyState != WebSocket.OPEN) {
    console.warn('WebSocket is closed or not ready')
    return
  }

  let target = ''
  if (selectedTarget != undefined && selectedTarget.value != '') {
    target = ` target:${selectedTarget.value}`
  }

  websocket.send(`start_broadcast${target} channel:${channel.value}`)

  mediaStream = await navigator.mediaDevices.getUserMedia({ audio: true })
  audioContext = new AudioContext({ sampleRate: 16000 })

  const source = audioContext.createMediaStreamSource(mediaStream)
  processor = audioContext.createScriptProcessor(16384, 1, 1)

  source.connect(processor)
  processor.connect(audioContext.destination)

  processor.onaudioprocess = async (e: AudioProcessingEvent) => {
    if (!websocket || websocket.readyState !== WebSocket.OPEN) return

    const input = e.inputBuffer.getChannelData(0)
    const buffer = audioContext!.createBuffer(1, input.length, audioContext!.sampleRate)
    buffer.copyToChannel(input, 0)

    try {
      const resampled = input
      const pcm16 = floatTo16BitPCM(resampled)

      websocket.send(pcm16.buffer)
    } catch (err) {
      console.error('Resampling error:', err)
    }
  }

  isRecording.value = true
}
function handlePCMData(data: ArrayBuffer) {
  const int16 = new Int16Array(data)
  const float32 = new Float32Array(int16.length)

  // Convert 16-bit PCM to float [-1, 1]
  for (let i = 0; i < int16.length; i++) {
    float32[i] = int16[i] / 32768
  }

  audioCtx.resume()
  const buffer = audioCtx.createBuffer(1, float32.length, 8000)
  buffer.getChannelData(0).set(float32)

  const source = audioCtx.createBufferSource()
  source.buffer = buffer
  source.connect(audioCtx.destination)
  source.start()
}

function stopRecording(): void {
  processor?.disconnect()
  mediaStream?.getTracks().forEach((t) => t.stop())
  audioContext?.close()
  if (websocket) {
    websocket.send('stop_broadcast')
  }

  processor = null
  audioContext = null
  mediaStream = null
  isRecording.value = false
}

function toggleRecording(): void {
  isRecording.value ? stopRecording() : startRecording()
}

function Reconnect(): void {
  initAudio()
  if (websocket?.readyState === WebSocket.OPEN) {
    websocket?.close()
  }

  const wsBaseUrl =
    window.location.protocol == 'https:'
      ? `wss://${window.location.hostname}/ws`
      : `ws://${window.location.hostname}:8765`
  console.log(wsBaseUrl)
  websocket = new WebSocket(`${wsBaseUrl}`)
  websocket.binaryType = 'arraybuffer'
  websocket.onopen = () => {
    console.log('Connected')
    connectionStatus.value = 'Connected'
  }

  websocket.onmessage = (event) => {
    console.log('Received message:', event.data)
    connectionStatus.value = `${event.data.byteLength} bytes received `

    if (event.data instanceof ArrayBuffer) {
      handlePCMData(event.data)
    }
  }

  websocket.onerror = () => {
    console.log('websocket Error')
    connectionStatus.value = 'WebSocket Error'
  }

  websocket.onclose = () => {
    console.log('Disconnected')
    connectionStatus.value = 'Disconnected'
  }
}

onMounted(() => {
  audioCtx = new AudioContext({ sampleRate: 8000 })
  Reconnect()
})

onBeforeUnmount(() => {
  websocket?.close()
  audioCtx?.close()
  audioContext?.close()
})
</script>

<style scoped>
body {
  font-family: sans-serif;
}
</style>
<template>
  <div class="column">
    <h1 class="text-xl font-bold">Polycom PPT</h1>
    <div class="box">
      Channel:
      <select v-model="channel">
        <option v-for="n in 50" :key="n" :value="n">
          {{ n > 25 ? ` Paging channel ${n - 25}` : `PTT Channel ${n}` }}
        </option>
      </select>

      <select v-model="selectedTarget" id="target">
        <option value="">Broadcast to all</option>
        <option value="192.168.1.79:5001">Basement</option>
        <option value="192.168.1.81:5001">Bedroom</option>
        <option value="192.168.1.76:5001">Living room</option>
      </select>

      <button @click="toggleRecording" class="mt-4 px-4 py-2 bg-blue-600 text-white rounded">
        {{ isRecording ? 'Stop Broadcasting' : 'Start Broadcasting' }}
      </button>
      <button @click="initAudio">
        {{ isListening ? 'Listening' : 'Click to start listening' }}
      </button>
      <button @click="Reconnect" class="mt-4 px-4 py-2 bg-blue-600 text-white rounded">
        Reconnect
      </button>
      Status:{{ connectionStatus }}
    </div>
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

.centered-column {
  display: flex;
  flex-direction: column;
  justify-content: center; /* vertical center */
  align-items: center; /* horizontal center */
  height: 100vh; /* full screen height */
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
  .box {
    width: 800px;
    height: 100px;
    margin: 10px;
  }

  header .wrapper {
    display: flex;
    place-items: flex-start;
    flex-wrap: wrap;
  }
}
</style>
