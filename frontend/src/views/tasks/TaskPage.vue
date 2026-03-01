<script setup>
import { ref, computed, onMounted, nextTick } from 'vue';
import apiClient from '@/api/axios';
import { useToast } from 'primevue/usetoast';

const tasks = ref([]);
const sites = ref([]);
const loading = ref(false);
const toast = useToast();
const formErrors = ref([]);
const selectedSite = ref(null);
const selectedEnabled = ref(null);
const sortField = ref(null);
const sortOrder = ref(null);

const taskDialog = ref(false);
const editingId = ref(null);
const taskNameInput = ref(null);

const form = ref({ task_name: '', minute: '*', hour: '*', site_id: null, weekdays: [], start_date: 0, end_date: 0, enabled: true });

const weekdayOptions = [
  { label: 'Monday', value: 0 },
  { label: 'Tuesday', value: 1 },
  { label: 'Wednesday', value: 2 },
  { label: 'Thursday', value: 3 },
  { label: 'Friday', value: 4 },
  { label: 'Saturday', value: 5 },
  { label: 'Sunday', value: 6 }
];

const siteFilterOptions = computed(() => [{ label: 'Все', value: null }, ...sites.value]);
const enabledFilterOptions = [
  { label: 'All', value: null },
  { label: 'On', value: true },
  { label: 'Off', value: false }
];

const filteredTasks = computed(() => {
  return tasks.value.filter(t => (selectedSite.value === null || t.site_id === selectedSite.value) && (selectedEnabled.value === null || t.enabled === selectedEnabled.value));
});

const weekdayMap = { 0: 'Mon', 1: 'Tue', 2: 'Wed', 3: 'Thu', 4: 'Fri', 5: 'Sat', 6: 'Sun' };
const formatWeekdays = (weekdays) => Array.isArray(weekdays) ? weekdays.map(d => weekdayMap[d]).join(', ') : '';
const getSiteNameById = (siteId) => sites.value.find(s => s.value === siteId)?.label || '—';

const onSort = (event) => {
  sortField.value = event.sortField;
  sortOrder.value = event.sortOrder;
};

const validateForm = () => {
  formErrors.value = [];
  if (!form.value.task_name?.trim()) formErrors.value.push('The name of the task is required');
  if (!form.value.minute?.trim()) formErrors.value.push('Minutes (Cron) are required');
  if (!form.value.hour?.trim()) formErrors.value.push('Clocks (Cron) are mandatory');
  if (form.value.site_id == null) formErrors.value.push('Website is required');
  if (!Array.isArray(form.value.weekdays) || form.value.weekdays.length === 0) formErrors.value.push('Choose at least one day of the week');
  if (typeof form.value.start_date !== 'number' || form.value.start_date < 0) formErrors.value.push('Start date must be non-negative');
  if (typeof form.value.end_date !== 'number' || form.value.end_date < form.value.start_date) formErrors.value.push('The end date must be ≥ start date');
  if (typeof form.value.threads !== 'number' || form.value.threads < 1) formErrors.value.push('Threads must be ≥ 1');
  if (typeof form.value.max_duration_seconds !== 'number' || form.value.max_duration_seconds < 60) formErrors.value.push('The maximum duration must be ≥ 60 seconds');

  return formErrors.value.length === 0;
};

const fetchSites = async () => {
  try {
    const { data } = await apiClient.get('/sites/');
    sites.value = data.map(site => ({ label: site.name, value: site.id }));
  } catch (err) {
    toast.add({ severity: 'error', summary: 'Failed loading sites', detail: err.message, life: 3000 });
  }
};

const loadTasks = async () => {
  loading.value = true;
  try {
    const { data } = await apiClient.get('/celery/task/');
    tasks.value = data;
  } finally {
    loading.value = false;
  }
};

const openCreateDialog = () => {
  editingId.value = null;
  form.value = {
    task_name: '',
    minute: '*',
    hour: '*',
    site_id: null,
    weekdays: [],
    start_date: 0,
    end_date: 0,
    enabled: true,
    threads: 5,
    max_duration_seconds: 86400
  };
  formErrors.value = [];
  taskDialog.value = true;
  nextTick(() => setTimeout(() => taskNameInput.value?.focus(), 100));
};

const closeDialog = () => { taskDialog.value = false; };

const editTask = async (task) => {
  if (!sites.value.length) await fetchSites();
  form.value = {
    task_name: task.name || '',
    minute: task.minute || '*',
    hour: task.hour || '*',
    site_id: task.site_id ?? null,
    weekdays: Array.isArray(task.weekdays) ? task.weekdays : [],
    start_date: typeof task.start_date === 'number' ? task.start_date : 0,
    end_date: typeof task.end_date === 'number' ? task.end_date : 0,
    enabled: task.enabled ?? true,
    threads: task.threads ?? 5,
    max_duration_seconds: task.max_duration_seconds ?? 86400
  };
  editingId.value = task.id;
  formErrors.value = [];
  taskDialog.value = true;
  await nextTick(() => setTimeout(() => taskNameInput.value?.focus(), 100));
};

const saveTask = async () => {
  if (!validateForm()) return;
  const site = sites.value.find(s => s.value === form.value.site_id);
  const payload = { ...form.value, site_name: site ? site.label : '' };
  try {
    if (editingId.value) {
      await apiClient.patch(`/celery/task/${editingId.value}`, payload);
    } else {
      await apiClient.post('/celery/task/', payload);
    }
    toast.add({ severity: 'success', summary: 'Successfully', detail: 'Task saved', life: 3000 });
    taskDialog.value = false;
    await loadTasks();
  } catch (err) {
    toast.add({ severity: 'error', summary: 'Error', detail: err.message, life: 4000 });
  }
};

const deleteTask = async (id) => {
  try {
    await apiClient.delete('/celery/task/', { params: { task_id: id } });
    toast.add({ severity: 'success', summary: 'Deleted', detail: `Task ${id} removed`, life: 3000 });
    await loadTasks();
  } catch (err) {
    toast.add({ severity: 'error', summary: 'Uninstall error', detail: err.message, life: 4000 });
  }
};

const maxDurationStr = computed({
  get() {
    const seconds = form.value.max_duration_seconds || 0;
    const hours = String(Math.floor(seconds / 3600)).padStart(2, '0');
    const minutes = String(Math.floor((seconds % 3600) / 60)).padStart(2, '0');
    return `${hours}:${minutes}`;
  },
  set(val) {
    const match = val.match(/^(\d{1,2}):(\d{2})$/);
    if (!match) return;
    const hours = parseInt(match[1], 10);
    const minutes = parseInt(match[2], 10);
    form.value.max_duration_seconds = hours * 3600 + minutes * 60;
  }
});

const onMaxDurationInput = (e) => {
  let value = e.target.value.replace(/\D/g, '');
  if (value.length >= 3) value = value.slice(0, 2) + ':' + value.slice(2, 4);
  e.target.value = value.slice(0, 5);
  maxDurationStr.value = e.target.value;
};


onMounted(() => {
  loadTasks();
  fetchSites();
});
</script>

<template>
  <div class="p-4">
    <h2 class="text-xl font-bold mb-5">Celery Task Management</h2>

    <div class="flex gap-4 mb-5">
      <Dropdown v-model="selectedSite" :options="siteFilterOptions" optionLabel="label" optionValue="value" placeholder="Filter by agent" class="w-64" />
      <Dropdown v-model="selectedEnabled" :options="enabledFilterOptions" optionLabel="label" optionValue="value" placeholder="Filter by Status" class="w-64" />
      <Button label="Create a task" icon="pi pi-plus" @click="openCreateDialog" />
    </div>

    <DataTable :value="filteredTasks" :loading="loading" responsiveLayout="scroll" :sortField="sortField" :sortOrder="sortOrder" @sort="onSort" stripedRows>
      <Column field="id" header="ID" sortable />
      <Column field="name" header="Task Name" sortable />
      <Column header="Time (Hours : Minutes)">
        <template #body="{ data }">
          <span class="font-mono text-sm bg-gray-800 px-2 py-1 rounded">{{ data.hour }} : {{ data.minute }}</span>
        </template>
      </Column>
      <Column field="threads" header="Threads" sortable>
        <template #body="{ data }">
          <span>{{ data.threads }}</span>
        </template>
      </Column>
      <Column field="max_duration_seconds" header="Max. Duration. (sec)"/>
      <Column field="weekdays" header="Days of the week">
        <template #body="{ data }">
          <span>{{ formatWeekdays(data.weekdays) }}</span>
        </template>
      </Column>
      <Column field="site_id" header="Agent" sortable>
        <template #body="{ data }">
          <span>{{ getSiteNameById(data.site_id) }}</span>
        </template>
      </Column>
      <Column field="enabled" header="Active" sortable>
        <template #body="{ data }">
          <span>{{ data.enabled ? 'Yes' : 'No' }}</span>
        </template>
      </Column>
      <Column field="total_run_count" header="Runs" sortable />
      <Column header="Actions">
        <template #body="{ data }">
          <div class="flex gap-2">
            <Button icon="pi pi-pencil" @click="editTask(data)" />
            <Button icon="pi pi-trash" severity="danger" @click="deleteTask(data.id)" />
          </div>
        </template>
      </Column>
    </DataTable>

    <Dialog v-model:visible="taskDialog" modal header="Task" :style="{ width: '500px' }">
      <div class="field">
        <label>Task name</label>
        <input ref="taskNameInput" v-model="form.task_name" type="text" class="w-full bg-dark-background border-dark-border rounded-md px-3 py-2" />
      </div>

      <div class="field flex gap-4">
        <div class="w-1/2">
          <label>Hours (Cron)</label>
          <input v-model="form.hour" type="text" placeholder="*, 9,21, 1-5" class="flex h-10 w-full rounded-md border px-3 py-2 bg-dark-background border-dark-border mt-1" />
        </div>
        <div class="w-1/2">
          <label>Minutes (Cron)</label>
          <input v-model="form.minute" type="text" placeholder="*, */5, 15,30" class="flex h-10 w-full rounded-md border px-3 py-2 bg-dark-background border-dark-border mt-1" />
        </div>
      </div>
      <div class="field">
        <label>Site</label>
        <Dropdown v-model="form.site_id" :options="sites" optionLabel="label" optionValue="value" placeholder="Choose a website" class="w-full bg-dark-background border-dark-border" />
      </div>

      <div class="field">
        <label>Days of the week</label>
        <MultiSelect v-model="form.weekdays" :options="weekdayOptions" optionLabel="label" optionValue="value" class="w-full" />
      </div>

      <div class="field">
        <label>Start date (days from today)</label>
        <InputNumber v-model="form.start_date" :min="0" class="w-full" />
      </div>

      <div class="field">
        <label>End date (days from today)</label>
        <InputNumber v-model="form.end_date" :min="form.start_date" class="w-full" />
      </div>

      <div class="field flex items-center gap-2">
        <label>Active task</label>
        <InputSwitch v-model="form.enabled" />
      </div>

      <div class="field">
        <label>Streams</label>
        <InputNumber v-model="form.threads" :min="1" class="w-full" />
      </div>

      <div class="field">
        <label>Max. Duration</label>
        <input
          v-model="maxDurationStr"
          type="text"
          placeholder="__:__"
          class="flex h-10 w-full rounded-md border px-3 py-2"
          maxlength="5"
          @input="onMaxDurationInput"
        />
      </div>


      <div v-if="formErrors.length" class="text-sm text-red-400 mb-2">
        <ul class="list-disc pl-5">
          <li v-for="(err, index) in formErrors" :key="index">{{ err }}</li>
        </ul>
      </div>

      <div class="flex justify-end gap-2 mt-4">
        <Button label="Cansel" icon="pi pi-times" severity="secondary" @click="closeDialog" />
        <Button label="Save" icon="pi pi-check" @click="saveTask" />
      </div>
    </Dialog>
  </div>
</template>

<style scoped>
.field { margin-bottom: 1rem; }
</style>
