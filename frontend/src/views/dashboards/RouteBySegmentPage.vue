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
const selectedAggregator = ref(null);
const selectedCellStats = ref(null);

function openDialog({ routeId, date, aggregator }) {
  selectedRouteId.value = routeId;
  selectedDate.value = date;
  selectedAggregator.value = aggregator;

  const cell = formattedTable.value
    ?.find(row => row.date === date)
    ?.[aggregator];

  selectedCellStats.value = cell
    ? {
        min: cell.competitorMin ?? cell.ourMin ?? null,
        median: cell.median ?? null,
        max: cell.competitorMax ?? cell.ourMax ?? null,
        currency: cell.currency ?? '',
        ourCount: cell.ourCount ?? 0,
        competitorCount: cell.competitorCount ?? 0,
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

    <div class="w-full flex gap-4 mb-5 justify-between items-start">
      <FiltersAggregators
        :loading="loading"
        :allAggregators="allAggregators"
        v-model:selectedSites="selectedSites"
        @update:selectedSites="(val) => (selectedSites.value = val)"
      />
    </div>

    <div class="flex gap-2 mb-5">
      <Button label="Reset" severity="secondary" @click="resetFilters" :disabled="loading" />
      <Button label="Confirm" severity="primary" @click="applyFilters" :disabled="loading" />
    </div>
  </div>

  <RoutesTableByDates
    :routesData="formattedTable"
    :dates="dates"
    :aggregators="aggregators"
    :loading="loading"
    :size="5"
    :openDialog="openDialog"
  />

  <RouteTripsDialog
    :visible="showDialog"
    @update:visible="showDialog = $event"
    :routeId="selectedRouteId"
    :aggregatorName="aggregators[selectedAggregator]"
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