<script setup>
import { ref, computed, onMounted, watch } from 'vue';
import apiClient from '@/api/axios';
import ProgressSpinner from 'primevue/progressspinner';
import InputText from 'primevue/inputtext';
import TreeTable from 'primevue/treetable';
import Column from 'primevue/column';
import Card from 'primevue/card';

const allCities = ref([]); // Все города + станции
const loadingCities = ref(true);
const error = ref(null);
const expandedKeys = ref({}); // Открытые узлы
const globalFilter = ref(''); // Поле поиска

const currentPage = ref(1);
const rowsPerPage = ref(10);

const onPageChange = (event) => {
    currentPage.value = event.page + 1;
    rowsPerPage.value = event.rows;
};
// **Фильтрация без изменения количества станций**
const filteredCities = computed(() => {
    if (!globalFilter.value.trim()) {
        return allCities.value; // Если нет фильтра, показываем все
    }

    const filterText = globalFilter.value.toLowerCase();

    return allCities.value
        .map((city) => {
            const matchesCity = city.data.name.toLowerCase().includes(filterText) || city.data.likeBusId.toString().includes(filterText);

            // Находим, есть ли совпадения среди станций
            const matchingStations = city.children.some((station) => station.data.name.toLowerCase().includes(filterText) || station.data.likeBusId.toString().includes(filterText));

            // Если город найден — показываем все его станции
            if (matchesCity) {
                return { ...city, children: city.children }; // Показываем все станции
            }

            // Если найдена станция — возвращаем город **со всеми его станциями**
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
        const response = await apiClient.get('/scraper/cities/');

        allCities.value = response.data.map((city) => ({
            key: `city-${city.id}`,
            data: {
                id: city.id,
                name: city.name_ru,
                type: 'Город',
                likeBusId: city.like_bus_id
            },
            children: city.stations.map((station) => ({
                key: `station-${station.id}`,
                data: {
                    id: station.id,
                    name: station.name_ru,
                    type: 'Станция',
                    likeBusId: station.like_bus_id
                },
                leaf: true
            }))
        }));
    } catch (err) {
        error.value = 'Ошибка загрузки данных';
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
        <!-- Глобальный лоудер -->
        <div v-if="loadingCities" class="flex justify-center py-10">
            <ProgressSpinner />
        </div>

        <Card v-else>
            <template #title>
                <div class="flex justify-between items-center">
                    Список городов и станций
                    <InputText v-model="globalFilter" placeholder="Поиск по названию, или ID" class="w-full sm:w-80" />
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
                    <Column field="name" header="Название" :expander="true" :style="{ width: '50%' }"></Column>
                    <Column field="type" header="Тип" :style="{ width: '15%' }"></Column>
                    <Column field="likeBusId" header="LikeBus ID" :style="{ width: '10%' }"></Column>
                </TreeTable>
            </template>
        </Card>
    </div>
</template>
