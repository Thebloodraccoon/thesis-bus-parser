<script setup>
import MultiSelect from 'primevue/multiselect';
import { useCityOptions } from '@/composables/RoutesByDate/useCities';
import { computed } from 'vue';

const props = defineProps({
  cityOptions: Array,
  cities: Object,
  fromCityIds: Array,
  toCityIds: Array,
  loading: Boolean
});

const emit = defineEmits([
  'update:fromCityIds',
  'update:toCityIds'
]);

// Универсальная логика: если cityOptions не передан, формируем его из cities
const resolvedCityOptions = computed(() => {
  if (props.cityOptions) return props.cityOptions;
  return useCityOptions(
    computed(() => props.cities || {}),
    computed(() => props.fromCityIds || []),
    computed(() => props.toCityIds || [])
  ).value;
});
</script>

<template>
  <div class="space-y-4">
    <!-- Город отправки -->
    <div>
      <label class="block text-sm font-medium mb-1">Город отправки</label>
      <MultiSelect
        :disabled="props.loading"
        :modelValue="props.fromCityIds"
        @update:modelValue="emit('update:fromCityIds', $event)"
        :options="resolvedCityOptions"
        optionLabel="label"
        optionValue="value"
        optionGroupLabel="label"
        optionGroupChildren="items"
        placeholder="Выберите города"
        filter
        class="w-64"
        :maxSelectedLabels="0"
      >
        <template #value="{ value }">
          <span v-if="value?.length">{{ value.length }} город(ов) выбрано</span>
          <span v-else class="text-gray-400">Выберите города</span>
        </template>
      </MultiSelect>
    </div>

    <!-- Город прибытия -->
    <div>
      <label class="block text-sm font-medium mb-1">Город прибытия</label>
      <MultiSelect
        :disabled="props.loading"
        :modelValue="props.toCityIds"
        @update:modelValue="emit('update:toCityIds', $event)"
        :options="resolvedCityOptions"
        optionLabel="label"
        optionValue="value"
        optionGroupLabel="label"
        optionGroupChildren="items"
        placeholder="Выберите города"
        filter
        class="w-64"
        :maxSelectedLabels="0"
      >
        <template #value="{ value }">
          <span v-if="value?.length">{{ value.length }} город(ов) выбрано</span>
          <span v-else class="text-gray-400">Выберите города</span>
        </template>
      </MultiSelect>
    </div>
  </div>
</template>
