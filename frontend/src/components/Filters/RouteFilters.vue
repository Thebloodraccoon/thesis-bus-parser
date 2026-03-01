<script setup>
import FiltersDateAndType from "@/components/Filters/FiltersDateAndType.vue";
import FiltersCities from "@/components/Filters/FiltersCities.vue";
import FiltersTime from "@/components/Filters/FiltersTime.vue";
import FiltersAggregators from "@/components/Filters/FiltersAggregators.vue";
import {onMounted, ref, watch} from "vue";
import apiClient from "@/api/axios";

const props = defineProps({
  selectedDate: Date,
  isTransfer: [Boolean, null],
  fromCityIds: Array,
  toCityIds: Array,
  departureTimeFrom: String,
  departureTimeTo: String,
  arrivalTimeFrom: String,
  arrivalTimeTo: String,
  selectedSites: Array,
  allAggregators: Array,
  cities: Object,
  loading: Boolean,
  selectedPresetId: [String, null]
});

const emit = defineEmits([
  'update:selectedDate',
  'update:isTransfer',
  'update:fromCityIds',
  'update:toCityIds',
  'update:departureTimeFrom',
  'update:departureTimeTo',
  'update:arrivalTimeFrom',
  'update:arrivalTimeTo',
  'update:selectedSites',
  'update:selectedPresetId',
  'reset'
]);
const selectedPresetIdLocal = ref(props.selectedPresetId);

const routesOptions = ref([]);
const selectedRouteId = ref(null);
const filtersVisible = ref(true);


watch(() => props.selectedPresetId, (val) => {
  selectedPresetIdLocal.value = val;
});

watch(selectedPresetIdLocal, (val) => {
  emit('update:selectedPresetId', val);
});

watch(selectedRouteId, (id) => {
  const selectedRoute = routesOptions.value.find(route => route.value === id);
  if (selectedRoute) {
    emit('update:fromCityIds', selectedRoute.stopping);
    emit('update:toCityIds', selectedRoute.stopping);
  }
});

const resetFilters = () => {
  selectedRouteId.value = null;
  emit('reset');
};

onMounted(async () => {
  const { data } = await apiClient.get('/presets/routes');
  routesOptions.value = data.map(route => ({
    label: `ID: ${route.route_id} – ${route.name}`,
    value: route.route_id,
    stopping: route.stopping,
    searchable: `${route.route_id} ${route.name}`.toLowerCase()
  }));
});

const customFilter = (option, searchText) => {
  if (!searchText) return true;
  return option.searchable.includes(searchText.toLowerCase());
};

</script>

<template>
  <div>
    <!-- Кнопка переключения видимости фильтров -->
<Button
  class="mb-3"
  icon="pi pi-sliders-h"
  text
  rounded
  size="small"
  :label="filtersVisible ? 'Collapse filters' : 'Show filters'"
  @click="filtersVisible = !filtersVisible"
/>


    <transition name="slide-fade">
      <div v-show="filtersVisible" class="filter-container w-1/3">
        <div class="w-full flex gap-4 mb-6 items-end">
          <FiltersDateAndType
              :selectedDate="props.selectedDate"
              :isTransfer="props.isTransfer"
              :loading="loading"
              @update:selectedDate="emit('update:selectedDate', $event)"
              @update:isTransfer="emit('update:isTransfer', $event)"
              @reset="resetFilters"
          />
        </div>

        <div class="w-full flex gap-4 mb-6 items-start">
          <FiltersCities
              :cities="props.cities"
              :fromCityIds="props.fromCityIds"
              :toCityIds="props.toCityIds"
              :loading="loading"
              @update:fromCityIds="emit('update:fromCityIds', $event)"
              @update:toCityIds="emit('update:toCityIds', $event)"
          />

          <div class="flex flex-col gap-4 self-start">
            <FiltersTime
                :departureTimeFrom="props.departureTimeFrom"
                :departureTimeTo="props.departureTimeTo"
                :arrivalTimeFrom="props.arrivalTimeFrom"
                :arrivalTimeTo="props.arrivalTimeTo"
                :loading="loading"
                @update:departureTimeFrom="emit('update:departureTimeFrom', $event)"
                @update:departureTimeTo="emit('update:departureTimeTo', $event)"
                @update:arrivalTimeFrom="emit('update:arrivalTimeFrom', $event)"
                @update:arrivalTimeTo="emit('update:arrivalTimeTo', $event)"
            />
          </div>
        </div>

        <div class="w-full flex gap-4 mb-5 items-start">
          <FiltersAggregators
              :allAggregators="props.allAggregators"
              :selectedSites="props.selectedSites"
              :loading="loading"
              @update:selectedSites="emit('update:selectedSites', $event)"
          />
        </div>
        <div class="mb-5">
          <div class="flex gap-2 mt-4">
            <Button label="Reset" severity="secondary" @click="resetFilters" />
            <Button label="Confirm" severity="primary" @click="$emit('apply')" />
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<style scoped>
.slide-fade-enter-active,
.slide-fade-leave-active {
  transition: max-height 0.4s ease, opacity 0.4s ease, margin 0.4s ease;
  overflow: hidden;
}

.slide-fade-enter-from,
.slide-fade-leave-to {
  max-height: 0;
  opacity: 0;
  margin-bottom: 0;
}

.slide-fade-enter-to,
.slide-fade-leave-from {
  max-height: 1000px; /* больше, чем фильтры занимают */
  opacity: 1;
  margin-bottom: 1.5rem; /* или то, что у тебя по дизайну */
}

</style>
