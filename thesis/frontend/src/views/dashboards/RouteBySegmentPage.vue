<script setup>
import { computed, nextTick, onMounted, ref } from 'vue';
import { useRoute } from 'vue-router';
import { useFilters } from '@/composables/RoutesBySegment/useFilters';
import { useRoutesLoader } from '@/composables/RoutesBySegment/useRoutesLoader';
import { useCities, useFlatCityOptions } from '@/composables/RoutesByDate/useCities';
import { useAggregators } from '@/composables/RoutesByDate/useAggregators';

import DateRangeFilter from '@/components/RoutesBySegment/DateRangeFilter.vue';
import FiltersDateAndType from '@/components/Filters/FiltersDateAndType.vue';
import FiltersTime from '@/components/Filters/FiltersTime.vue';
import FiltersAggregators from '@/components/Filters/FiltersAggregators.vue';
import FiltersSingleCity from '@/components/RoutesBySegment/FiltersSingleCity.vue';
import RoutesTableByDates from '@/components/RoutesBySegment/RoutesTableByDates.vue';
import RouteTripsDialog from '@/components/RouteTripsDialog.vue';
import { useUserStore } from '@/stores/useUserStore';
import apiClient from '@/api/axios';
import FilterPresets from "@/components/Filters/FilterPresets.vue";

const userStore = useUserStore();
const { isAnalyticOrAdmin, fetchCurrentUser } = userStore;

onMounted(async () => {
  fetchCurrentUser();
});

const route = useRoute();

const {
  selectedDates,
  isTransfer,
  fromCityId,
  toCityId,
  departureTimeFrom,
  departureTimeTo,
  arrivalTimeFrom,
  arrivalTimeTo,
  selectedFromCity,
  selectedToCity,
  resetFilters,
} = useFilters();

const { cities, fetchCities } = useCities();
const cityOptions = useFlatCityOptions(cities);
const { allAggregators, selectedSites, fetchAggregators } = useAggregators();

const { loadRoutes, routeData, loading, dates, formattedTable, aggregators } = useRoutesLoader(
  {
    selectedDates,
    isTransfer,
    fromCityId,
    toCityId,
    departureTimeFrom,
    departureTimeTo,
    arrivalTimeFrom,
    arrivalTimeTo,
    selectedFromCity,
    selectedToCity
  },
  selectedSites,
  allAggregators
);

const showDialog = ref(false);
const selectedRouteId = ref(null);
const selectedDate = ref(null);
const selectedAgentId = ref(null);
const selectedCellStats = ref(null);

function openDialog({ routeId, date, agentId }) {
  selectedRouteId.value = routeId;
  selectedDate.value = date;
  selectedAgentId.value = agentId;

  const cell = formattedTable.value
    ?.find(row => row.date === date)
    ?.[agentId];

  selectedCellStats.value = cell
    ? {
        min: cell.min ?? null,
        median: cell.median ?? null,
        max: cell.max ?? null,
        currency: cell.currency ?? '',
        count: cell.count ?? 0,
      }
    : null;

  showDialog.value = true;
}

const citiesName = computed(() => {
  const from = cityOptions.value.find(c => c.value === selectedFromCity.value)?.label || '';
  const to = cityOptions.value.find(c => c.value === selectedToCity.value)?.label || '';
  return from && to ? `${from} — ${to}` : '';
});

const fromQuery = computed(() => Number(route.query.fromCityId));
const toQuery = computed(() => Number(route.query.toCityId));

const dateRangeRef = ref(null);
const selectedPresetId = ref(null);

onMounted(async () => {
  await fetchCities();
  await fetchAggregators();

  const allSiteIds = allAggregators.value.map(a => a.value);

  if (route.query.siteIds) {
    selectedSites.value = route.query.siteIds.split(',').map((id) => Number(id));
  } else {
    selectedSites.value = allSiteIds;
  }

  if (fromQuery.value) fromCityId.value = [fromQuery.value];
  if (toQuery.value) toCityId.value = [toQuery.value];

  if (route.query.isTransfer !== undefined) {
    isTransfer.value = route.query.isTransfer === 'true';
  }

  if (route.query.departureTimeFrom) departureTimeFrom.value = route.query.departureTimeFrom;
  if (route.query.departureTimeTo) departureTimeTo.value = route.query.departureTimeTo;
  if (route.query.arrivalTimeFrom) arrivalTimeFrom.value = route.query.arrivalTimeFrom;
  if (route.query.arrivalTimeTo) arrivalTimeTo.value = route.query.arrivalTimeTo;

  await nextTick();
  loadRoutes();
});

function generateDateRange(start, end) {
  const result = [];
  const current = new Date(start);
  while (current <= end) {
    result.push(current.toLocaleDateString('sv-SE'));
    current.setDate(current.getDate() + 1);
  }
  return result;
}

function applyFilters() {
  const range = dateRangeRef.value?.getRange();
  if (range?.[0] && range?.[1]) {
    selectedDates.value = generateDateRange(range[0], range[1]);
  }
  loadRoutes();
}

const exporting = ref(false);

async function exportToCSV() {
  if (!selectedFromCity.value || !selectedToCity.value || !selectedDates.value?.length) return;

  exporting.value = true;
  try {
    const params = new URLSearchParams();
    params.set('from_city_id', selectedFromCity.value);
    params.set('to_city_id',   selectedToCity.value);
    selectedDates.value.forEach(d => params.append('departure_dates', d));

    if (departureTimeFrom.value && departureTimeFrom.value !== '00:00')
      params.set('departure_time_from', departureTimeFrom.value);
    if (departureTimeTo.value && departureTimeTo.value !== '23:59')
      params.set('departure_time_to', departureTimeTo.value);
    if (arrivalTimeFrom.value && arrivalTimeFrom.value !== '00:00')
      params.set('arrival_time_from', arrivalTimeFrom.value);
    if (arrivalTimeTo.value && arrivalTimeTo.value !== '23:59')
      params.set('arrival_time_to', arrivalTimeTo.value);
    if (isTransfer.value !== null && isTransfer.value !== undefined)
      params.set('is_transfer', isTransfer.value);
    (selectedSites.value || []).forEach(id => params.append('sites', id));

    const response = await apiClient.get(`/routes/export-segment?${params.toString()}`, {
      responseType: 'blob',
    });

    const disposition = response.headers['content-disposition'] || '';
    const match = disposition.match(/filename="?([^"]+)"?/);
    const filename = match ? match[1] : `segment_${selectedFromCity.value}_${selectedToCity.value}.csv`;

    const url = URL.createObjectURL(new Blob([response.data], { type: 'text/csv' }));
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  } catch (err) {
    console.error('Segment export failed:', err);
  } finally {
    exporting.value = false;
  }
}
</script>

<template>
  <div class="filter-container w-1/3">
    <!-- Дата и тип маршрута -->
    <div class="w-full flex gap-4 mb-6 items-end">
      <DateRangeFilter
        ref="dateRangeRef"
        :modelValue="selectedDates"
        :loading="loading"
      />
      <FiltersDateAndType
        :showDate="false"
        :showTransfer="true"
        v-model:isTransfer="isTransfer"
        @reset="resetFilters"
        :loading="loading"
      />
    </div>

    <div class="w-full flex gap-4 mb-6 items-start justify-between">
      <div class="flex flex-col gap-4">
        <FiltersSingleCity
          label="City of departure"
          :cityOptions="cityOptions"
          v-model:selectedCityId="selectedFromCity"
          :loading="loading"
          :required="true"
        />
        <FiltersSingleCity
          label="City of arrival"
          :cityOptions="cityOptions"
          v-model:selectedCityId="selectedToCity"
          :loading="loading"
          :required="true"
        />
      </div>
      <div class="flex flex-col gap-4">
        <FiltersTime
          v-model:departureTimeFrom="departureTimeFrom"
          v-model:departureTimeTo="departureTimeTo"
          v-model:arrivalTimeFrom="arrivalTimeFrom"
          v-model:arrivalTimeTo="arrivalTimeTo"
          :loading="loading"
        />
      </div>
    </div>

    <div class="w-full flex gap-4 mb-5 items-start">
      <FiltersAggregators
        :loading="loading"
        :allAggregators="allAggregators"
        v-model:selectedSites="selectedSites"
        @update:selectedSites="(val) => (selectedSites.value = val)"
      />

      <FilterPresets
        v-if="isAnalyticOrAdmin"
        v-model:selectedPresetId="selectedPresetId"
        :fromCityIds="fromCityId"
        :toCityIds="toCityId"
        :selectedSites="selectedSites"
        :departureTimeFrom="departureTimeFrom"
        :departureTimeTo="departureTimeTo"
        :arrivalTimeFrom="arrivalTimeFrom"
        :arrivalTimeTo="arrivalTimeTo"
        :isTransfer="isTransfer"
        :loading="loading"
        @update:fromCityIds="(val) => fromCityId = val"
        @update:toCityIds="(val) => toCityId = val"
        @update:selectedSites="(val) => selectedSites = val"
        @update:departureTimeFrom="(val) => departureTimeFrom = val"
        @update:departureTimeTo="(val) => departureTimeTo = val"
        @update:arrivalTimeFrom="(val) => arrivalTimeFrom = val"
        @update:arrivalTimeTo="(val) => arrivalTimeTo = val"
        @update:isTransfer="(val) => isTransfer = val"
        @reset="resetFilters"
      />
    </div>

    <div class="flex gap-2 mb-5">
      <Button label="Reset" severity="secondary" @click="resetFilters" :disabled="loading" />
      <Button label="Confirm" severity="primary" @click="applyFilters" :disabled="loading" />
      <Button
        label="Export CSV"
        icon="pi pi-download"
        severity="secondary"
        :loading="exporting"
        :disabled="loading || !selectedFromCity || !selectedToCity || !selectedDates?.length || !formattedTable?.length"
        @click="exportToCSV"
      />
    </div>
  </div>

  <RoutesTableByDates
    :routesData="formattedTable"
    :aggregators="aggregators"
    :loading="loading"
    :size="5"
    :openDialog="openDialog"
  />

  <RouteTripsDialog
    :visible="showDialog"
    @update:visible="showDialog = $event"
    :routeId="selectedRouteId"
    :aggregatorName="aggregators[selectedAgentId]"
    :selectedDate="selectedDate"
    :departureTimeFrom="departureTimeFrom"
    :departureTimeTo="departureTimeTo"
    :arrivalTimeFrom="arrivalTimeFrom"
    :arrivalTimeTo="arrivalTimeTo"
    :isTransfer="isTransfer"
    :CitiesName="citiesName"
    :cellStats="selectedCellStats"
  />
</template>
