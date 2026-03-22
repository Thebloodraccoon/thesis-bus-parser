import { ref, computed } from 'vue';
import { fetchRouteByCities } from '@/composables/RoutesBySegment/fetchRouteByCities';

export function useRoutesLoader(filters, selectedSites, allAggregators) {
  const routeData = ref(null);
  const loading = ref(false);

  async function loadRoutes() {
    if (!filters.selectedFromCity.value || !filters.selectedToCity.value || !filters.selectedDates.value.length) {
      return;
    }

    try {
      loading.value = true;
      const response = await fetchRouteByCities({
        fromCityId: filters.selectedFromCity.value,
        toCityId: filters.selectedToCity.value,
        departureDates: filters.selectedDates.value,
        departureTimeFrom: filters.departureTimeFrom.value,
        departureTimeTo: filters.departureTimeTo.value,
        arrivalTimeFrom: filters.arrivalTimeFrom.value,
        arrivalTimeTo: filters.arrivalTimeTo.value,
        isTransfer: filters.isTransfer.value,
        siteIds: selectedSites.value
      });
      routeData.value = response;
    } catch (err) {
      console.error('Route loading error:', err);
    } finally {
      loading.value = false;
    }
  }

  const dates = computed(() => {
    const all = Object.values(routeData.value?.agents || {}).flatMap((obj) =>
      Object.keys(obj)
    );
    return [...new Set(all)].sort();
  });

  const formattedTable = computed(() => {
    if (!routeData.value?.agents || !filters.selectedDates.value?.length) return [];

    const agentIds = Object.keys(routeData.value.agents);

    return filters.selectedDates.value.map((date) => {
      const row = { date };

      agentIds.forEach((agentId) => {
        const raw = routeData.value.agents?.[agentId]?.[date];
        row[agentId] = raw?.id
          ? {
              id: raw.id,
              min: raw.min_price,
              max: raw.max_price,
              median: raw.median_price,
              count: raw.total_segments_count,
              currency: raw.currency,
            }
          : null;
      });

      return row;
    });
  });

  // 🔄 Агенты, которые реально есть в ответе (с их названиями)
  const aggregators = computed(() => {
    const agentIds = Object.keys(routeData.value?.agents || {});
    const result = {};

    agentIds.forEach((id) => {
      const agg = allAggregators.value?.find((a) => a.value === Number(id));
      if (agg) {
        result[id] = agg.label;
      }
    });

    return result;
  });

  return {
    loadRoutes,
    routeData,
    loading,
    dates,
    formattedTable,
    aggregators, // 👈 отдаём сюда
  };

}
