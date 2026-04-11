<script setup>
import RouteTable from "@/components/RoutesByDate/RouteTable.vue";
import { computed, onMounted, ref } from 'vue';

import RouteTripsDialog from "@/components/RouteTripsDialog.vue";
import ScrollToTop from "@/components/ScrollToTop.vue";
import { useAggregators } from "@/composables/RoutesByDate/useAggregators";
import { useCities } from "@/composables/RoutesByDate/useCities";
import { usePagination } from "@/composables/RoutesByDate/usePagination";
import { useRoutes } from "@/composables/RoutesByDate/useRoutes";
import { useExport } from "@/composables/RoutesByDate/useExport";

// Trip Dialog
const showTripsDialog = ref(false);
const selectedRouteId = ref(null);
const selectedAggregatorName = ref(null);
const selectedCitiesName = ref(null);

const openTripsDialog = (routeData, aggregatorName, selectedCities) => {
    if (!routeData || (routeData.ourCount === 0 && routeData.competitorCount === 0)) return;
    selectedAggregatorName.value = aggregatorName;
    selectedCitiesName.value = selectedCities;
    selectedRouteId.value = routeData.routeId;
    showTripsDialog.value = true;
};

// Filters
const selectedDate = ref(new Date());
const departureTimeFrom = ref('00:00');
const departureTimeTo = ref('23:59');
const arrivalTimeFrom = ref('00:00');
const arrivalTimeTo = ref('23:59');
const isTransfer = ref(null);
const fromCityIds = ref([]);
const toCityIds = ref([]);

// Data
const { cities, fetchCities } = useCities();
const { aggregators, allAggregators, selectedSites, fetchAggregators } = useAggregators();
const { page, size, rowsPerPageOptions } = usePagination();

const { fetchRoutes, routesData, loading, totalRecords, firstRecord, lastRecord } = useRoutes({
    cities, aggregators, selectedDate, page, size, selectedSites,
    fromCityIds, toCityIds, departureTimeFrom, departureTimeTo, arrivalTimeFrom, arrivalTimeTo, isTransfer
});

const { exportToCSV, exporting } = useExport({
  selectedDate,
  fromCityIds,
  toCityIds,
  departureTimeFrom,
  departureTimeTo,
  arrivalTimeFrom,
  arrivalTimeTo,
  isTransfer,
  selectedSites,
});

const selectedPresetId = ref(null);

const updateWeekDatesAndData = () => {
  weekDates.value = getNextWeekDates(selectedDate.value);
  selectedWeekDate.value = null;
  weekDataCache.value = {};
  fetchWeekData();
};

const resetFilters = async () => {
  selectedDate.value = new Date();
  fromCityIds.value = [];
  toCityIds.value = [];
  departureTimeFrom.value = '00:00';
  departureTimeTo.value = '23:59';
  arrivalTimeFrom.value = '00:00';
  arrivalTimeTo.value = '23:59';
  isTransfer.value = null;
  page.value = 1;
  selectedPresetId.value = null;
  selectedSites.value = allAggregators.value.map(a => a.value);
  await fetchRoutes();
  updateWeekDatesAndData();
};

const applyFilters = async () => {
  page.value = 1;
  await fetchRoutes();
  updateWeekDatesAndData();
};

const citiesLoaded = ref(false);
const aggregatorsLoaded = ref(false);

const isReady = computed(() => citiesLoaded.value && aggregatorsLoaded.value);

// --- Лента дат следующей недели ---
function getNextWeekDates(baseDate) {
  const date = new Date(baseDate);
  const day = date.getDay();
  const diffToNextMonday = ((8 - day) % 7) || 7;
  const monday = new Date(date);
  monday.setDate(date.getDate() + diffToNextMonday);
  return Array.from({ length: 7 }, (_, i) => {
    const d = new Date(monday);
    d.setDate(monday.getDate() + i);
    return d;
  });
}

const weekDates = ref(getNextWeekDates(selectedDate.value));
const selectedWeekDate = ref(null);
const weekDataCache = ref({});
const weekLoading = ref(false);

function getDateKey(date) {
  return date.toISOString().split('T')[0];
}

async function fetchWeekData() {
  weekLoading.value = true;
  const cache = {};
  const promises = weekDates.value.map(async (date) => {
    const dateKey = getDateKey(date);
    if (weekDataCache.value[dateKey]) {
      cache[dateKey] = weekDataCache.value[dateKey];
      return;
    }
    const tempDate = ref(date);
    const tempPage = ref(page.value);
    const tempSize = ref(size.value);
    const tempSelectedSites = ref([...selectedSites.value]);
    const tempFromCityIds = ref([...fromCityIds.value]);
    const tempToCityIds = ref([...toCityIds.value]);
    const tempDepartureTimeFrom = ref(departureTimeFrom.value);
    const tempDepartureTimeTo = ref(departureTimeTo.value);
    const tempArrivalTimeFrom = ref(arrivalTimeFrom.value);
    const tempArrivalTimeTo = ref(arrivalTimeTo.value);
    const tempIsTransfer = ref(isTransfer.value);
    const { fetchRoutes, routesData, totalRecords } = useRoutes({
      cities, aggregators, selectedDate: tempDate, page: tempPage, size: tempSize, selectedSites: tempSelectedSites,
      fromCityIds: tempFromCityIds, toCityIds: tempToCityIds, departureTimeFrom: tempDepartureTimeFrom, departureTimeTo: tempDepartureTimeTo,
      arrivalTimeFrom: tempArrivalTimeFrom, arrivalTimeTo: tempArrivalTimeTo, isTransfer: tempIsTransfer
    });
    await fetchRoutes();
    cache[dateKey] = {
      routesData: JSON.parse(JSON.stringify(routesData.value)),
      totalRecords: totalRecords.value
    };
  });
  await Promise.all(promises);
  weekDataCache.value = { ...weekDataCache.value, ...cache };
  weekLoading.value = false;
}

const tableRoutesData = computed(() => {
  if (selectedWeekDate.value) {
    const key = getDateKey(selectedWeekDate.value);
    return weekDataCache.value[key]?.routesData || [];
  }
  return routesData.value;
});
const tableTotalRecords = computed(() => {
  if (selectedWeekDate.value) {
    const key = getDateKey(selectedWeekDate.value);
    return weekDataCache.value[key]?.totalRecords || 0;
  }
  return totalRecords.value;
});

onMounted(async () => {
  await fetchCities();
  citiesLoaded.value = true;

  await fetchAggregators();
  aggregatorsLoaded.value = true;
  selectedSites.value = allAggregators.value.map(a => a.value);

  if (isReady.value) {
    await fetchRoutes();
    updateWeekDatesAndData();
  }
});

const selectedDialogDate = computed(() => selectedWeekDate.value || selectedDate.value);

</script>

<template>
    <RouteFilters
        v-model:selectedDate="selectedDate"
        v-model:isTransfer="isTransfer"
        v-model:fromCityIds="fromCityIds"
        v-model:toCityIds="toCityIds"
        v-model:departureTimeFrom="departureTimeFrom"
        v-model:departureTimeTo="departureTimeTo"
        v-model:arrivalTimeFrom="arrivalTimeFrom"
        v-model:arrivalTimeTo="arrivalTimeTo"
        v-model:selectedSites="selectedSites"
        v-model:selectedPresetId="selectedPresetId"
        :allAggregators="allAggregators"
        :cities="cities"
        :loading="loading"
        @reset="resetFilters"
        @apply="applyFilters"
    />

    <div class="flex items-center justify-between mt-4 mb-2">
      <span class="text-sm text-gray-500 font-medium">
          Showing {{ firstRecord }}–{{ lastRecord }} from {{ tableTotalRecords }} records
      </span>

      <Button
        label="Export CSV"
        icon="pi pi-download"
        severity="secondary"
        :loading="exporting"
        :disabled="loading || tableTotalRecords === 0"
        @click="exportToCSV"
      />
    </div>

    <RouteTable
      :routesData="tableRoutesData"
      :cities="cities"
      :aggregators="aggregators"
      :loading="loading"
      :size="size"
      :openTripsDialog="openTripsDialog"
      :departureTimeFrom="departureTimeFrom"
      :departureTimeTo="departureTimeTo"
      :arrivalTimeFrom="arrivalTimeFrom"
      :arrivalTimeTo="arrivalTimeTo"
      :isTransfer="isTransfer"
      :selectedSites="selectedSites"
    />

    <div class="flex justify-end mt-2">
        <Paginator
          :rows="size"
          :first="(page - 1) * size"
          :totalRecords="tableTotalRecords"
          :rowsPerPageOptions="rowsPerPageOptions.map(o => o.value)"
          @page="($event) => {
            page = $event.page + 1;
            size = $event.rows;
            fetchRoutes();
          }"
        />
    </div>

    <RouteTripsDialog
        :visible="showTripsDialog"
        @update:visible="showTripsDialog = $event"
        :routeId="selectedRouteId"
        :departureTimeFrom="departureTimeFrom"
        :departureTimeTo="departureTimeTo"
        :arrivalTimeFrom="arrivalTimeFrom"
        :arrivalTimeTo="arrivalTimeTo"
        :isTransfer="isTransfer"
        :aggregatorName="selectedAggregatorName"
        :CitiesName="selectedCitiesName"
        :selectedDate="selectedDialogDate"
    />

  <ScrollToTop />
</template>
