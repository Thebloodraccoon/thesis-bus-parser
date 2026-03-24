import {ref, computed} from 'vue';
import apiClient from '@/api/axios';
import {useToast} from 'primevue/usetoast';

export function useRoutes({
                              cities,
                              aggregators,
                              selectedDate,
                              page,
                              size,
                              selectedSites,
                              fromCityIds,
                              toCityIds,
                              departureTimeFrom,
                              departureTimeTo,
                              arrivalTimeFrom,
                              arrivalTimeTo,
                              isTransfer
                          }) {
    const routesData = ref([]);
    const totalRecords = ref(0);
    const loading = ref(false);
    const toast = useToast();

    const currencySymbols = {
        UAH: '₴',
        USD: '$',
        EUR: '€'
    };

    const fetchRoutes = async () => {
        loading.value = true;

        const formatTime = (val) => /^([01]\d|2[0-3]):([0-5]\d)$/.test(val);
        const times = [departureTimeFrom.value, departureTimeTo.value, arrivalTimeFrom.value, arrivalTimeTo.value];
        for (const t of times) {
            if (t && !formatTime(t)) {
                loading.value = false;
                return;
            }
        }

        try {
            const formattedDate = new Date(selectedDate.value.getTime() - selectedDate.value.getTimezoneOffset() * 60000).toISOString().split('T')[0];
            const params = {
                departure_date: formattedDate,
                page: page.value,
                size: size.value,
                sites: selectedSites.value
            };

            if (fromCityIds.value.length) params.from_city_ids = fromCityIds.value;
            if (toCityIds.value.length) params.to_city_ids = toCityIds.value;
            if (departureTimeFrom.value) params.departure_time_from = departureTimeFrom.value;
            if (departureTimeTo.value) params.departure_time_to = departureTimeTo.value;
            if (arrivalTimeFrom.value) params.arrival_time_from = arrivalTimeFrom.value;
            if (arrivalTimeTo.value) params.arrival_time_to = arrivalTimeTo.value;
            if (isTransfer.value !== null) params.is_transfer = isTransfer.value;

            const {data} = await apiClient.get('/routes/routes-by-date', {
                params,
                paramsSerializer: (params) => {
                    const searchParams = new URLSearchParams();
                    Object.keys(params).forEach((key) => {
                        const value = params[key];
                        if (Array.isArray(value)) value.forEach((v) => searchParams.append(key, v));
                        else searchParams.append(key, value);
                    });
                    return searchParams.toString();
                }
            });

            totalRecords.value = data.total;
            routesData.value = data.items.map((route) => {
                const from = cities.value[route.from_city] || `#${route.from_city}`;
                const to = cities.value[route.to_city] || `#${route.to_city}`;

                const row = {
                    route: `${from} - ${to}`,
                    fromCityId: route.from_city,
                    toCityId: route.to_city
                };

                for (const id in route.agents) {
                    const aggregatorName = aggregators.value[id] || `#${id}`;
                    const agentData = route.agents[id];

                    row[aggregatorName] = Object.keys(agentData).length
                        ? {
                            routeId: agentData.id,
                            currency: currencySymbols[agentData.currency] || agentData.currency,
                            count: agentData.total_segments_count,
                            min: agentData.min_price,
                            max: agentData.max_price,
                            median: agentData.median_price
                        }
                        : null;
                }

                return row;
            });


        } catch (error) {
            const toast = useToast();
            toast.add({severity: 'error', summary: 'Error', detail: 'Failed to load data', life: 3000});
        } finally {
            loading.value = false;
        }
    };

    const firstRecord = computed(() => (page.value - 1) * size.value + 1);
    const lastRecord = computed(() => Math.min(page.value * size.value, totalRecords.value));

    return {
        fetchRoutes,
        routesData,
        totalRecords,
        loading,
        firstRecord,
        lastRecord
    };
}
