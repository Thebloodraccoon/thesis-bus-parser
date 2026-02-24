import { ref, computed } from 'vue';
import apiClient from '@/api/axios';
import { useToast } from 'primevue/usetoast';

export function useCities() {
    const cities = ref({});
    const toast = useToast();

    const fetchCities = async () => {
        try {
            const { data } = await apiClient.get('/cities/');
            cities.value = Object.fromEntries(data.map((city) => [city.id, city.name_ru]));
        } catch (error) {
            toast.add({ severity: 'error', summary: 'FAILED', detail: 'Failed to load cities', life: 3000 });
        }
    };

    return {
        cities,
        fetchCities
    };
}

export function useCityOptions(cities, fromCityIds, toCityIds) {
    return computed(() => {
        const selected = Object.entries(cities.value || {})
            .filter(([id]) => fromCityIds.value?.includes(Number(id)) || toCityIds.value?.includes(Number(id)))
            .map(([id, name]) => ({ label: name, value: Number(id) }))
            .sort((a, b) => a.label.localeCompare(b.label));

        const notSelected = Object.entries(cities.value || {})
            .filter(([id]) => !fromCityIds.value?.includes(Number(id)) && !toCityIds.value?.includes(Number(id)))
            .map(([id, name]) => ({ label: name, value: Number(id) }))
            .sort((a, b) => a.label.localeCompare(b.label));

        const groups = [];
        if (selected.length > 0) {
            groups.push({ label: 'Selected', items: selected });
        }
        groups.push({ label: 'All cities', items: notSelected });

        return groups;
    });
}

export function useFlatCityOptions(cities) {
  return computed(() =>
    Object.entries(cities.value || {})
      .map(([id, name]) => ({ label: name, value: Number(id) }))
      .sort((a, b) => a.label.localeCompare(b.label))
  )
}
