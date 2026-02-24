<script setup>
import MultiSelect from 'primevue/multiselect';
import { useAggregatorOptions } from '@/composables/RoutesByDate/useAggregators';
import {computed, watch} from 'vue';

const props = defineProps({
  allAggregators: Array,
  selectedSites: Array,
  loading: Boolean
});

const emit = defineEmits([
  'update:selectedSites'
]);

const aggregatorOptions = useAggregatorOptions(
  computed(() => props.allAggregators),
  computed(() => props.selectedSites)
);

watch(() => props.selectedPresetId, (presetId) => {
  if (!presetId) {
    // Пустой шаблон — выбрать всех
    const allSiteIds = props.allAggregators.map(agg => agg.value);
    emit('update:selectedSites', allSiteIds);
  }
});

</script>

<template>
  <div>
    <label class="block text-sm font-medium mb-1">Фильтр по агрегаторам</label>
    <MultiSelect
      :disabled="props.loading"
      :modelValue="props.selectedSites"
      @update:modelValue="emit('update:selectedSites', $event)"
      :options="aggregatorOptions"
      optionLabel="label"
      optionValue="value"
      optionGroupLabel="label"
      optionGroupChildren="items"
      placeholder="Фильтр по агрегаторам"
      class="mb-4 w-64"
      :maxSelectedLabels="0"
    >
      <template #value="{ value }">
        <span v-if="value && value.length">{{ value.length }} агент(ов) выбрано</span>
        <span v-else class="text-gray-400">Выберите агрегаторы</span>
      </template>
    </MultiSelect>
  </div>
</template>
