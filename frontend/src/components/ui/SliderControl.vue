<script setup lang="ts">
defineProps<{
  label: string
  modelValue: number | string
  min: number | string
  max: number | string
}>()
const emit = defineEmits<{
  (e: 'update:modelValue', value: number): void
}>()
</script>

<template>
  <div class="space-y-2">
    <div class="flex justify-between items-center">
      <label class="text-xs font-semibold tracking-wider text-gray-600">{{ label }}</label>
      <span class="font-mono text-gray-900 bg-gray-100 px-2 py-1 rounded">{{ modelValue }}</span>
    </div>
    <input 
      type="range" 
      :min="min" 
      :max="max" 
      :value="modelValue" 
      @input="emit('update:modelValue', Number(($event.target as HTMLInputElement).value))" 
      class="w-full h-1 bg-gray-200 rounded-lg appearance-none cursor-pointer" 
    />
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