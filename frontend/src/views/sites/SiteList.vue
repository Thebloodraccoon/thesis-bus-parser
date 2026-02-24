<script setup>
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { useSites } from '@/composables/SiteComposables/useSites';
import { useUserStore } from '@/stores/useUserStore';
import { formatDate } from '@/service/dateUtils';

const router = useRouter();

const { sites, loading, fetchSites, deleteSite } = useSites();

const userStore = useUserStore();
const { isAdmin, fetchCurrentUser } = userStore;

const globalFilter = ref('');
const filterTable = ref({
    global: { value: null, matchMode: 'contains' }
});

function goToCreate() {
    router.push('/site/create');
}

onMounted(() => {
    fetchCurrentUser();
    fetchSites();
});
</script>

<template>
    <div class="sites-list">
        <h1>Список сайтов</h1>
        <div class="flex flex-wrap gap-2 items-center justify-between mb-3">
            <InputText v-model="globalFilter" placeholder="Поиск..." class="w-full sm:w-80" />
            <Button v-if="isAdmin" type="button" icon="pi pi-plus" label="Добавить сайт" @click="goToCreate" class="p-button-success" />
        </div>

        <DataTable
            :value="sites"
            :loading="loading"
            :globalFilterFields="['name', 'url']"
            :filters="filterTable"
            responsiveLayout="scroll"
            stripedRows
        >
            <Column field="id" header="ID" sortable :style="{ width: '5%' }" />
            <Column field="name" header="Название" sortable :style="{ width: '15%' }" />
            <Column field="url" header="URL" sortable :style="{ width: '25%' }" />
            <Column field="last_parsed" header="Последний сбор данные в" sortable :style="{ width: '25%' }">
                <template #body="{ data }">
                    {{ formatDate(data.last_parsed) }}
                </template>
            </Column>
            <Column field="threads" header="Threads" sortable :style="{ width: '5%' }" />
            <Column field="depth" header="Depth" sortable :style="{ width: '5%' }" />

            <Column header="Действия" :style="{ width: '15%' }">
                <template #body="{ data }">
                    <div class="action-buttons">
                        <Button type="button" icon="pi pi-cog" class="p-button-rounded p-button-info" @click="$router.push(`/site/${data.id}`)" title="Просмотр" />
                        <Button v-if="isAdmin" type="button" icon="pi pi-trash" class="p-button-rounded p-button-danger ml-2" @click="deleteSite(data.id)" title="Удалить" />
                    </div>
                </template>
            </Column>
        </DataTable>
    </div>
</template>

<style scoped>
.sites-list {
    padding: 20px;
}

.sites-list h1 {
    margin-bottom: 20px;
}
</style>
