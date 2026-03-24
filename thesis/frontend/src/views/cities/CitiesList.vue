<script setup>
import { ref, computed, onMounted, watch } from 'vue';
import apiClient from '@/api/axios';
import ProgressSpinner from 'primevue/progressspinner';
import InputText from 'primevue/inputtext';
import TreeTable from 'primevue/treetable';
import Column from 'primevue/column';
import Card from 'primevue/card';

const allCities = ref([]);
const loadingCities = ref(true);
const error = ref(null);
const expandedKeys = ref({});
const globalFilter = ref('');

const currentPage = ref(1);
const rowsPerPage = ref(10);

const onPageChange = (event) => {
    currentPage.value = event.page + 1;
    rowsPerPage.value = event.rows;
};

const filteredCities = computed(() => {
    if (!globalFilter.value.trim()) {
        return allCities.value;
    }

    const filterText = globalFilter.value.toLowerCase();

    return allCities.value
        .map((city) => {
            const matchesCity = city.data.name.toLowerCase().includes(filterText) || city.data.likeBusId.toString().includes(filterText);
            const matchingStations = city.children.some((station) => station.data.name.toLowerCase().includes(filterText) || station.data.likeBusId.toString().includes(filterText));
            if (matchesCity) {
                return { ...city, children: city.children };
            }

            if (matchingStations) {
                return { ...city, children: city.children };
            }

            return null;
        })
        .filter((city) => city !== null);
});

const fetchCities = async () => {
    try {
        loadingCities.value = true;
        const response = await apiClient.get('/cities/');

        allCities.value = response.data.map((city) => ({
            key: `city-${city.id}`,
            data: {
                id: city.id,
                name: city.name_ua,
                type: 'City',
                likeBusId: city.like_bus_id
            }
        }));
    } catch (err) {
        error.value = 'Data Upload Error';
    } finally {
        loadingCities.value = false;
    }
};

onMounted(() => fetchCities());

watch(globalFilter, () => {
    currentPage.value = 1;
});
</script>

<template>
    <div class="p-4 relative">
        <div v-if="loadingCities" class="flex justify-center py-10">
            <ProgressSpinner />
        </div>

        <Card v-else>
            <template #title>
                <div class="flex justify-between items-center">
                    List of cities and stations
                    <InputText v-model="globalFilter" placeholder="Search by name, or ID" class="w-full sm:w-80" />
                </div>
            </template>
            <template #content>
                <div v-if="error" class="text-red-500 text-center">{{ error }}</div>
                <TreeTable
                    :value="filteredCities"
                    v-model:expandedKeys="expandedKeys"
                    paginator
                    :rows="rowsPerPage"
                    :totalRecords="filteredCities.length"
                    :first="(currentPage - 1) * rowsPerPage"
                    @page="onPageChange"
                    paginatorTemplate="FirstPageLink PrevPageLink PageLinks NextPageLink LastPageLink RowsPerPageDropdown"
                    :rowsPerPageOptions="[10, 25, 50, 100]"
                >
                    <Column field="name" header="Name" :expander="true" :style="{ width: '50%' }"></Column>
                    <Column field="type" header="Type" :style="{ width: '15%' }"></Column>
                    <Column field="likeBusId" header="LikeBus ID" :style="{ width: '10%' }"></Column>
                </TreeTable>
            </template>
        </Card>
    </div>
</template>
