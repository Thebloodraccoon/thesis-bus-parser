<script setup>
import { FilterMatchMode, FilterOperator } from '@primevue/core/api';
import { ref, watch, computed, onMounted } from 'vue';
import apiClient from '@/api/axios';

const customers1 = ref([]); // Данные для таблицы
const filters1 = ref(null);
const loading1 = ref(false);
const expandedRows = ref([]);

// Фильтрация и инициализация
const initFilters = () => {
    filters1.value = {
        global: { value: null, matchMode: FilterMatchMode.CONTAINS },
        name: { operator: FilterOperator.AND, constraints: [{ value: null, matchMode: FilterMatchMode.STARTS_WITH }] },
        'country.name': { operator: FilterOperator.AND, constraints: [{ value: null, matchMode: FilterMatchMode.STARTS_WITH }] },
        status: { operator: FilterOperator.OR, constraints: [{ value: null, matchMode: FilterMatchMode.EQUALS }] }
    };
};

initFilters();

// Функция загрузки данных с API
const fetchCustomers = async () => {
    loading1.value = true;
    try {
        const response = await apiClient.get('/api/customers'); // Укажи свой эндпоинт
        customers1.value = response.data || [];
    } catch (error) {
        console.error('Ошибка загрузки данных:', error);
    } finally {
        loading1.value = false;
    }
};

// Автоматическая загрузка данных при монтировании
onMounted(fetchCustomers);

// Функция очистки фильтров
const clearFilter = () => {
    initFilters();
};

// Управление раскрытием строк
const expandAll = () => {
    expandedRows.value = customers1.value.reduce((acc, item) => {
        acc[item.id] = true;
        return acc;
    }, {});
};

const collapseAll = () => {
    expandedRows.value = [];
};

</script>

<template>
    <div class="card">
        <div class="font-semibold text-xl mb-4">Фильтрация</div>
        <DataTable
            :value="customers1"
            :paginator="true"
            :rows="10"
            dataKey="id"
            :rowHover="true"
            v-model:filters="filters1"
            filterDisplay="menu"
            :loading="loading1"
            :globalFilterFields="['name', 'country.name', 'status']"
            showGridlines
        >
            <template #header>
                <div class="flex justify-between">
                    <Button type="button" icon="pi pi-filter-slash" label="Очистить фильтры" outlined @click="clearFilter()" />
                    <span class="p-input-icon-left">
                        <i class="pi pi-search" />
                        <InputText v-model="filters1.global.value" placeholder="Поиск..." />
                    </span>
                </div>
            </template>
            <template #empty> Нет данных для отображения. </template>
            <template #loading> Загрузка данных, пожалуйста подождите... </template>

            <Column field="name" header="Имя" style="min-width: 12rem">
                <template #body="{ data }">
                    {{ data.name }}
                </template>
                <template #filter="{ filterModel }">
                    <InputText v-model="filterModel.value" type="text" placeholder="Поиск по имени" />
                </template>
            </Column>

            <Column header="Страна" filterField="country.name" style="min-width: 12rem">
                <template #body="{ data }">
                    <span>{{ data.country.name }}</span>
                </template>
                <template #filter="{ filterModel }">
                    <InputText v-model="filterModel.value" type="text" placeholder="Поиск по стране" />
                </template>
            </Column>

            <Column field="status" header="Статус" :filterMenuStyle="{ width: '12rem' }" style="min-width: 12rem">
                <template #body="{ data }">
                    <Tag :value="data.status" />
                </template>
                <template #filter="{ filterModel }">
                    <Select v-model="filterModel.value" :options="['Active', 'Inactive']" placeholder="Выбрать" showClear />
                </template>
            </Column>
        </DataTable>
    </div>
</template>

<style scoped>
.card {
    padding: 20px;
}
</style>
