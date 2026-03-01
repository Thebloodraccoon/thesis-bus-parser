<script setup>
import {computed, ref} from 'vue'

const props = defineProps({
  label: String,
  selectedCityId: Number,
  cityOptions: Array,
  required: Boolean,
  loading: Boolean
})

const emit = defineEmits(['update:selectedCityId'])

const modelValue = computed({
  get: () => props.selectedCityId,
  set: (val) => emit('update:selectedCityId', val)
})

const filterValue = ref('')

const filteredCities = computed(() => {
  if (!filterValue.value) return props.cityOptions
  return props.cityOptions.filter(city =>
    city.label.toLowerCase().includes(filterValue.value.toLowerCase())
  )
})
</script>

<template>
  <div class="w-64">
    <label class="block text-sm font-medium text-gray-700 mb-1">
      {{ label }}
      <span v-if="required" class="text-red-500">*</span>
    </label>

    <Dropdown
      :options="filteredCities"
      :modelValue="props.selectedCityId"
      @update:modelValue="emit('update:selectedCityId', $event)"
      :disabled="props.loading"
      optionLabel="label"
      optionValue="value"
      placeholder="Select city"
      class="w-64"
      :filter="true"
      filterPlaceholder="Search for the city..."
      @filter="filterValue = $event.value"
      :showClear="true"
      :filterFields="['label']"
    >
      <template #option="slotProps">
        <div>{{ slotProps.option.label }}</div>
      </template>
    </Dropdown>

  </div>
</template>