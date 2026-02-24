<script setup>
import TimeInputDropdown from '@/components/TimeInputDropdown.vue';

const props = defineProps({
  departureTimeFrom: String,
  departureTimeTo: String,
  arrivalTimeFrom: String,
  arrivalTimeTo: String,
  loading: Boolean
});

const emit = defineEmits([
  'update:departureTimeFrom',
  'update:departureTimeTo',
  'update:arrivalTimeFrom',
  'update:arrivalTimeTo'
]);
</script>

<template>
  <div class="flex flex-col sm:flex-row flex-wrap gap-4">
    <div class="flex flex-col sm:flex-row gap-4">
      <div class="flex flex-col">
        <label class="text-sm font-medium mb-1">Departure From</label>
        <TimeInputDropdown
          :loading="props.loading"
          :modelValue="props.departureTimeFrom"
          @update:modelValue="emit('update:departureTimeFrom', $event)"
          placeholder="00:00"
        />
      </div>

      <div class="flex flex-col">
        <label class="text-sm font-medium mb-1">Departure to</label>
        <TimeInputDropdown
          :loading="props.loading"
          :modelValue="props.departureTimeTo"
          @update:modelValue="emit('update:departureTimeTo', $event)"
          placeholder="23:59"
        />
      </div>
    </div>

    <div class="flex flex-col sm:flex-row gap-4 mt-2">
      <div class="flex flex-col">
        <label class="text-sm font-medium mb-1">Arrival from</label>
        <TimeInputDropdown
          :loading="props.loading"
          :modelValue="props.arrivalTimeFrom"
          @update:modelValue="emit('update:arrivalTimeFrom', $event)"
          placeholder="00:00"
        />
      </div>

      <div class="flex flex-col">
        <label class="text-sm font-medium mb-1">Arrival before</label>
        <TimeInputDropdown
          :loading="props.loading"
          :modelValue="props.arrivalTimeTo"
          @update:modelValue="emit('update:arrivalTimeTo', $event)"
          placeholder="23:59"
        />
      </div>
    </div>
  </div>
</template>