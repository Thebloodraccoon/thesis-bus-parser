import { ref, computed } from 'vue';

export function useFilters() {
  const selectedDates = ref([]);
  const isTransfer = ref(null);
  const fromCityId = ref([]);
  const toCityId = ref([]);

  const departureTimeFrom = ref('00:00');
  const departureTimeTo = ref('23:59');
  const arrivalTimeFrom = ref('00:00');
  const arrivalTimeTo = ref('23:59');

  const selectedFromCity = computed({
    get: () => fromCityId.value[0] ?? null,
    set: (val) => {
      fromCityId.value = val ? [val] : [];
    },
  });

  const selectedToCity = computed({
    get: () => toCityId.value[0] ?? null,
    set: (val) => {
      toCityId.value = val ? [val] : [];
    },
  });

  function resetFilters() {
    selectedDates.value = [];
    isTransfer.value = null;
    fromCityId.value = [];
    toCityId.value = [];
    departureTimeFrom.value = '00:00';
    departureTimeTo.value = '23:59';
    arrivalTimeFrom.value = '00:00';
    arrivalTimeTo.value = '23:59';
  }

  return {
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
    resetFilters
  };
}
