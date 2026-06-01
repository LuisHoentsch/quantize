<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue'
import SliderControl from './components/ui/SliderControl.vue'

const numColors = ref(3)
const numShades = ref(3)
const diameter = ref(9)
const colorSigma = ref(75.0)
const spaceSigma = ref(75.0)
const passes = ref(3)
const kernelSize = ref(7)
const maxDimension = ref(800)

const autoUpdate = ref(false)

const isProcessing = ref(false)
const hasResult = ref(true)
const beforeImageUrl = ref('/default_image.jpg')
const afterImageUrl = ref('/default_filtered.jpg')

const selectedFile = ref<File | null>(null)

const handleFileUpload = (event: Event) => {
  const target = event.target as HTMLInputElement
  if (target.files && target.files.length > 0) {
    selectedFile.value = target.files[0]
    beforeImageUrl.value = URL.createObjectURL(target.files[0])
    afterImageUrl.value = ''
    hasResult.value = false
    sliderPosition.value = 100
  }
}

const applyFilter = async () => {
  if (!selectedFile.value) {
    alert("Please upload an image first.")
    return
  }

  isProcessing.value = true

  const formData = new FormData()
  formData.append('file', selectedFile.value)
  formData.append('num_colors', numColors.value.toString())
  formData.append('num_shades_per_color', numShades.value.toString())
  formData.append('d', diameter.value.toString())
  formData.append('sigma_color', colorSigma.value.toString())
  formData.append('sigma_space', spaceSigma.value.toString())
  formData.append('passes', passes.value.toString())
  formData.append('ksize', kernelSize.value.toString())
  formData.append('max_dim', maxDimension.value.toString())

  try {
    const response = await fetch('/api/stylize', {
      method: 'POST',
      body: formData
    })
    
    if (!response.ok) throw new Error("Error during Stylized API call")

    const blob = await response.blob()
    afterImageUrl.value = URL.createObjectURL(blob)
    hasResult.value = true
    sliderPosition.value = 50
  } catch (error) {
    console.error(error)
    alert("An error occurred: " + error)
  } finally {
    isProcessing.value = false
  }
}

let applyTimeout: number | undefined

const autoApplyTrigger = () => {
  if (!autoUpdate.value) return
  if (!selectedFile.value) return

  if (applyTimeout) clearTimeout(applyTimeout)
  // Debounce the call to avoid thrashing the server while sliding
  applyTimeout = window.setTimeout(() => {
    applyFilter()
  }, 500) // wait 500ms after last change before rendering
}

watch(
  [numColors, numShades, diameter, colorSigma, spaceSigma, passes, kernelSize, maxDimension],
  () => {
    autoApplyTrigger()
  }
)

// Comparison Slider Logic
const sliderPosition = ref(50)
const containerRef = ref<HTMLElement | null>(null)
let isDragging = false

const updateSlider = (x: number) => {
  if (!containerRef.value) return
  const rect = containerRef.value.getBoundingClientRect()
  let position = ((x - rect.left) / rect.width) * 100
  sliderPosition.value = Math.max(0, Math.min(100, position))
}

const handleMove = (e: MouseEvent | TouchEvent) => {
  if (!isDragging) return
  const x = 'touches' in e ? e.touches[0].clientX : e.clientX
  updateSlider(x)
}

const startDrag = () => { isDragging = true; document.body.style.cursor = 'ew-resize' }
const stopDrag = () => { isDragging = false; document.body.style.cursor = 'default' }

onMounted(async () => {
  window.addEventListener('mouseup', stopDrag)
  window.addEventListener('mousemove', handleMove)
  window.addEventListener('touchend', stopDrag)
  window.addEventListener('touchmove', handleMove)

  try {
    const response = await fetch('/default_image.jpg')
    const blob = await response.blob()
    selectedFile.value = new File([blob], 'default_image.jpg', { type: blob.type })
  } catch (error) {
    console.error('Failed to load default image', error)
  }
})

onUnmounted(() => {
  window.removeEventListener('mouseup', stopDrag)
  window.removeEventListener('mousemove', handleMove)
  window.removeEventListener('touchend', stopDrag)
  window.removeEventListener('touchmove', handleMove)
})

</script>

<template>
  <div class="bg-gray-50 text-gray-900 font-sans min-h-screen md:h-screen flex flex-col md:flex-row md:overflow-hidden">
    <!-- Sidebar -->
    <aside class="w-full md:w-[320px] bg-white border-b md:border-b-0 md:border-r border-gray-200 flex flex-col md:h-full z-10 shrink-0">
      <div class="p-4 overflow-y-auto flex-1">

        <div class="mb-6">
          <div class="flex items-center gap-2 mb-2">
            <h1 class="text-2xl font-bold text-gray-900">Quantize</h1>
          </div>
        </div>

        <!-- Upload -->
        <div class="mb-6">
          <label class="block w-full cursor-pointer">
            <div class="border-2 border-dashed border-gray-300 bg-gray-50 hover:bg-gray-100 hover:border-gray-900 transition-all rounded-xl p-6 text-center group">
              <span class="block text-xs font-semibold tracking-wider text-gray-500 mb-2">UPLOAD IMAGE</span>
            </div>
            <input type="file" accept="image/*" class="hidden" @change="handleFileUpload" />
          </label>
        </div>

        <!-- Parameters -->
        <div class="space-y-6 text-sm">
          <SliderControl label="NUMBER OF COLORS" v-model="numColors" min="1" max="10" />
          <SliderControl label="SHADES PER COLOR" v-model="numShades" min="1" max="10" />
          <SliderControl label="DIAMETER (D)" v-model="diameter" min="5" max="15" />
          <SliderControl label="COLOR SIGMA" v-model="colorSigma" min="50" max="150" />
          <SliderControl label="SPACE SIGMA" v-model="spaceSigma" min="50" max="150" />
          <SliderControl label="PASSES" v-model="passes" min="1" max="15" />

          <!-- Kernel Size -->
          <div class="space-y-2">
            <label class="text-xs font-semibold tracking-wider text-gray-600 mb-2 block">KERNEL SIZE</label>
            <div class="grid grid-cols-4 gap-2">
              <button v-for="size in [3, 5, 7, 9]" :key="size" 
                @click="kernelSize = size"
                :class="['rounded py-2 font-mono transition-all border', 
                  kernelSize === size ? 'bg-gray-900 text-white border-gray-900' : 'bg-gray-50 text-gray-900 border-transparent hover:bg-gray-200']">
                {{ size }}
              </button>
            </div>
          </div>

          <!-- Max Dim -->
          <div class="space-y-2">
            <label class="text-xs font-semibold tracking-wider text-gray-600">MAX. DIMENSION (PX)</label>
            <input type="number" min="500" max="5000" v-model="maxDimension" class="w-full bg-gray-100 border-none rounded p-2 font-mono focus:ring-1 focus:ring-gray-900 outline-none" />
          </div>

        </div>
      </div>

      <!-- Footer -->
      <div class="p-4 border-t border-gray-200 bg-white flex flex-col gap-3">
        <label class="flex items-center justify-between cursor-pointer">
          <span class="text-xs font-semibold tracking-wider text-gray-600">AUTO UPDATE</span>
          <div class="flex items-center">
            <div class="relative">
              <input type="checkbox" v-model="autoUpdate" class="sr-only" />
              <div class="block w-10 h-6 rounded-full transition-colors" :class="autoUpdate ? 'bg-gray-900' : 'bg-gray-300'"></div>
              <div class="dot absolute left-1 top-1 bg-white w-4 h-4 rounded-full transition-transform" :class="{ 'translate-x-4': autoUpdate }"></div>
            </div>
          </div>
        </label>
        
        <button
          @click="applyFilter"
          :disabled="isProcessing || autoUpdate"
          class="w-full bg-gray-900 hover:bg-gray-800 disabled:bg-gray-400 text-white font-bold py-2.5 px-4 rounded-lg flex items-center justify-center gap-2 shadow-lg transition-transform active:scale-95 text-sm">
          {{ isProcessing ? 'Processing...' : 'Apply Filter' }}
        </button>
      </div>
    </aside>    <!-- Main Content -->
    <main class="flex-1 bg-gray-50 relative flex items-center justify-center min-h-[300px]">
      <div class="relative w-full h-full flex items-center justify-center p-4">
        <div ref="containerRef" class="relative group overflow-hidden w-full h-full md:w-[90%] md:h-[90%] min-h-[50vh] rounded-lg shadow-2xl border border-gray-200 select-none">
          <!-- After Image -->
          <img v-if="hasResult" :src="afterImageUrl" class="absolute inset-0 w-full h-full object-contain pointer-events-none" />

          <!-- Before Image -->
          <div class="absolute inset-0 w-full h-full overflow-hidden pointer-events-none" :style="{ width: hasResult ? sliderPosition + '%' : '100%' }">
            <img :src="beforeImageUrl" class="absolute top-0 left-0 h-full object-contain max-w-none" :style="{ width: containerRef?.clientWidth + 'px' }" />
          </div>

          <!-- Labels -->
          <div class="absolute top-4 left-4 bg-white/80 backdrop-blur-md px-3 py-1.5 rounded border border-black/10 shadow-sm z-20">
            <span class="text-[10px] font-bold tracking-widest text-gray-900">BEFORE</span>
          </div>
          <div v-if="hasResult" class="absolute top-4 right-4 bg-white/80 backdrop-blur-md px-3 py-1.5 rounded border border-black/10 shadow-sm z-20">
            <span class="text-[10px] font-bold tracking-widest text-gray-900">AFTER</span>
          </div>

          <!-- Slider Handle -->
          <div v-if="hasResult"
            class="absolute top-0 bottom-0 w-1 bg-white cursor-ew-resize z-30 group/handle flex items-center justify-center"
            :style="{ left: sliderPosition + '%', transform: 'translateX(-50%)' }"
            @mousedown.stop="startDrag"
            @touchstart.stop="startDrag">
            <div class="w-8 h-8 rounded-full bg-white text-gray-900 flex items-center justify-center shadow-lg transition-transform group-hover/handle:scale-110">
              <div class="flex gap-[2px]">
                <div class="w-1 h-3 border-l-2 border-gray-400"></div>
                <div class="w-1 h-3 border-l-2 border-gray-400"></div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<style scoped>
input[type="range"]::-webkit-slider-thumb {
  -webkit-appearance: none;
  height: 16px;
  width: 16px;
  border-radius: 50%;
  background: #111827;
  cursor: pointer;
  margin-top: -6px;
}
</style>
