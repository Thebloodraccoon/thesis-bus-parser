<script setup>
import { FilterMatchMode } from '@primevue/core/api';
import { ref } from 'vue';
import { formatDate } from '@/service/dateUtils';

defineProps({
    users: {
        type: Array,
        required: true
    },
    roleOptions: {
        type: Array,
        required: true
    },
    disabledRoles: {
        type: Array,
        required: true
    }
});
const filterTable = ref({
    global: { value: null, matchMode: FilterMatchMode.CONTAINS }
});

defineEmits(['open-invite-dialog', 'update-role', 'open-delete-dialog']);
</script>

<template>
    <div class="card">
        <DataTable
            ref="tableRef"
            :value="users"
            paginator
            :rows="10"
            showCurrentPageReport
            paginatorTemplate="CurrentPageReport FirstPageLink PrevPageLink PageLinks NextPageLink LastPageLink RowsPerPageDropdown"
            currentPageReportTemplate="Showing {first} to {last} of {totalRecords} entries"
            :rowsPerPageOptions="[10, 25, 50]"
            :globalFilterFields="['email', 'role']"
            v-model:filters="filterTable"
        >
            <template #header>
                <div class="flex flex-wrap gap-2 items-center justify-between">
                    <IconField class="w-full sm:w-80 order-1 sm:order-none">
                        <InputIcon class="pi pi-search" />
                        <InputText v-model="filterTable.global.value" placeholder="Global Search" class="w-full" />
                    </IconField>
                    <Button type="button" icon="pi pi-user-plus" label="Invite User" class="w-full sm:w-auto order-none sm:order-1" outlined @click="$emit('open-invite-dialog')" />
                </div>
            </template>
            <Column field="id" header="ID" sortable :style="{ width: '5%' }">
                <template #body="{ data }">
                    {{ data.id }}
                </template>
            </Column>
            <Column field="email" header="Email" sortable :style="{ width: '10%' }">
                <template #body="{ data }">
                    {{ data.email }}
                </template>
            </Column>
            <Column field="role" header="Role" :style="{ width: '10%' }">
                <template #body="{ data }">
                    <Dropdown v-model="data.role" :options="roleOptions" optionLabel="label" optionValue="value" :disabled="disabledRoles.includes(data.email)" @change="$emit('update-role', data, data.role)" />
                </template>
            </Column>
            <Column field="created_at" header="Creation Date" sortable :style="{ width: '15%' }">
                <template #body="{ data }">
                    {{ formatDate(data.created_at) }}
                </template>
            </Column>
            <Column field="created_at" header="Last Login" sortable :style="{ width: '15%' }">
                <template #body="{ data }">
                    {{ formatDate(data.last_login) }}
                </template>
            </Column>
            <Column field="action" header="Actions" :style="{ width: '10%' }">
                <template #body="{ data }">
                    <Button type="button" icon="pi pi-trash" class="p-button-danger" :disabled="data.email === 'admin@admin.com'" @click="$emit('open-delete-dialog', data.id)" />
                </template>
            </Column>
        </DataTable>
    </div>
</template>
