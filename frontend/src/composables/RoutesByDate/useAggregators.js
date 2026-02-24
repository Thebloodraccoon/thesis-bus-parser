import { ref } from 'vue';
import apiClient from '@/api/axios';
import { useToast } from 'primevue/usetoast';
import { computed } from 'vue';

export function useAggregators() {
    const aggregators = ref({});
    const aggregatorsData = ref({});
    const allAggregators = ref([]);
    const selectedSites = ref([]);
    const toast = useToast();

    const fetchAggregators = async (filterActive = true) => {
        try {
            const params = {};
            if (filterActive) {
                params.is_site_active = true;
            }

            const { data } = await apiClient.get('/sites/', { params });

            aggregators.value = Object.fromEntries(data.map(site => [site.id, site.name]));
            aggregatorsData.value = Object.fromEntries(data.map(site => [site.id, site]));

            allAggregators.value = data.map(site => ({
                label: site.name,
                value: site.id
            }));

        } catch (error) {
            toast.add({
                severity: 'error',
                summary: 'FAILED',
                detail: 'Agents failed to load',
                life: 3000
            });
        }
    };

    return {
        aggregators,
        aggregatorsData,
        allAggregators,
        selectedSites,
        fetchAggregators
    };
}

export function useAggregatorOptions(allAggregators, selectedSites) {
    return computed(() => {
        const selected = (allAggregators.value || [])
            .filter(aggregator => selectedSites.value.includes(aggregator.value))
            .sort((a, b) => a.label.localeCompare(b.label));

        const notSelected = (allAggregators.value || [])
            .filter(aggregator => !selectedSites.value.includes(aggregator.value))
            .sort((a, b) => a.label.localeCompare(b.label));

        const groups = [];

        if (selected.length > 0) {
            groups.push({ label: 'Selected', items: selected });
        }

        groups.push({ label: 'All agents', items: notSelected });

        return groups;
    });
}
