<script setup>
import RouteFilters from "@/components/Filters/RouteFilters.vue";
import RouteTable from "@/components/RoutesByDate/RouteTable.vue";
import { computed, onMounted, ref } from 'vue';

import RouteTripsDialog from "@/components/RouteTripsDialog.vue";
import ScrollToTop from "@/components/ScrollToTop.vue";
import { useAggregators } from "@/composables/RoutesByDate/useAggregators";
import { useCities } from "@/composables/RoutesByDate/useCities";
import { usePagination } from "@/composables/RoutesByDate/usePagination";
import { useRoutes } from "@/composables/RoutesByDate/useRoutes";

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

const selectedPresetId = ref(null);

// Удаляем watch на фильтры для weekDates и fetchWeekData
// Вместо этого вызываем fetchWeekData и weekDates только в applyFilters и resetFilters

const updateWeekDatesAndData = () => {
  weekDates.value = getNextWeekDates(selectedDate.value);
  selectedWeekDate.value = null; // сбрасываем выбор
  weekDataCache.value = {}; // сбрасываем кэш
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
  // Сбрасываем страницу на первую при применении новых фильтров
  page.value = 1;
  await fetchRoutes();
  updateWeekDatesAndData();
};

const citiesLoaded = ref(false);
const aggregatorsLoaded = ref(false);

const isReady = computed(() => citiesLoaded.value && aggregatorsLoaded.value);

// --- Лента дат следующей недели ---
function getNextWeekDates(baseDate) {
  // Получаем понедельник следующей недели относительно baseDate
  const date = new Date(baseDate);
  const day = date.getDay();
  // 0 - воскресенье, 1 - понедельник ...
  // Сдвиг до понедельника следующей недели
  const diffToNextMonday = ((8 - day) % 7) || 7;
  const monday = new Date(date);
  monday.setDate(date.getDate() + diffToNextMonday);
  // Формируем массив дат пн-вс
  return Array.from({ length: 7 }, (_, i) => {
    const d = new Date(monday);
    d.setDate(monday.getDate() + i);
    return d;
  });
}

const weekDates = ref(getNextWeekDates(selectedDate.value));
const selectedWeekDate = ref(null); // null = показываем основную дату

// Кэш: ключ - ISO дата, значение - { routesData, totalRecords, ... }
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
    // Если уже есть в кэше - не грузим
    if (weekDataCache.value[dateKey]) {
      cache[dateKey] = weekDataCache.value[dateKey];
      return;
    }
    // Создаём временные reactive-объекты для useRoutes
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

// Обновлять weekDates и weekDataCache при изменении фильтров или основной даты
// watch([
//   selectedDate, fromCityIds, toCityIds, departureTimeFrom, departureTimeTo, arrivalTimeFrom, arrivalTimeTo, isTransfer, selectedSites, size, page
// ], () => {
//   weekDates.value = getNextWeekDates(selectedDate.value);
//   selectedWeekDate.value = null; // сбрасываем выбор
//   weekDataCache.value = {}; // сбрасываем кэш
//   fetchWeekData();
// }, { immediate: true });

// --- Для таблицы ---
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

  // Загружаем данные при первоначальной загрузке
  if (isReady.value) {
    await fetchRoutes();
    updateWeekDatesAndData();
  }
});

// --- Для RouteTripsDialog ---
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

    <!-- Лента дат следующей недели -->
    <div class="flex gap-2 justify-start my-4 pl-4">
      <template v-for="date in weekDates" :key="getDateKey(date)">
        <button
          class="px-3 py-2 rounded transition-colors duration-200 border font-medium shadow-sm"
          :class="[
            // Выделение выбранной даты
            selectedWeekDate && getDateKey(selectedWeekDate) === getDateKey(date)
              ? 'bg-primary-500 text-white border-primary-600 dark:bg-primary-400 dark:text-surface-900 dark:border-primary-300'
              : 'bg-surface-0 text-surface-900 border-surface-200 hover:bg-primary-50 hover:text-primary-700 dark:bg-surface-900 dark:text-surface-0 dark:border-surface-700 dark:hover:bg-primary-900 dark:hover:text-primary-100',
            // Выходные
            [6, 0].includes(date.getDay()) ? 'border-red-500 dark:border-red-400' : '',
            // Неактивное состояние при загрузке
            (weekLoading || loading) ? 'opacity-50 cursor-not-allowed pointer-events-none' : ''
          ]"
          @click="selectedWeekDate = date"
          :disabled="weekLoading || loading"
        >
          <span>{{ date.toLocaleDateString('ru-RU', { weekday: 'short', day: '2-digit', month: '2-digit' }) }}</span>
        </button>
      </template>
      <button
        v-if="selectedWeekDate"
        class="ml-4 px-3 py-2 rounded border bg-gray-100 text-gray-700 border-gray-400 dark:bg-surface-800 dark:text-surface-100 dark:border-surface-600 hover:bg-primary-50 hover:text-primary-700 dark:hover:bg-primary-900 dark:hover:text-primary-100 transition-colors duration-200 font-medium shadow-sm"
        @click="selectedWeekDate = null"
        :disabled="weekLoading || loading"
        :class="(weekLoading || loading) ? 'opacity-50 cursor-not-allowed pointer-events-none' : ''"
      >Сбросить</button>
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

<div class="flex items-center justify-between mt-2">
  <span class="text-sm text-gray-500">
    Показано {{ firstRecord }}–{{ lastRecord }} из {{ tableTotalRecords }} записей
  </span>

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