<script setup>
import {ref, onMounted, computed, watch} from 'vue';
import apiClient from '@/api/axios';
import {useToast} from "primevue/usetoast";

const props = defineProps({
  selectedSites: Array,
  fromCityIds: Array,
  toCityIds: Array,
  departureTimeFrom: String,
  departureTimeTo: String,
  arrivalTimeFrom: String,
  arrivalTimeTo: String,
  isTransfer: [Boolean, null],
  selectedPresetId: [String, null],
  loading: Boolean
});

const emit = defineEmits([
  'update:fromCityIds',
  'update:toCityIds',
  'update:selectedSites',
  'update:departureTimeFrom',
  'update:departureTimeTo',
  'update:arrivalTimeFrom',
  'update:arrivalTimeTo',
  'update:isTransfer',
  'update:selectedPresetId',
  'reset'
]);

const presets = ref([]);
const selectedPresetIdLocal = ref(props.selectedPresetId);

const saving = ref(false);
const deleting = ref(false);

watch(() => props.selectedPresetId, (val) => {
  selectedPresetIdLocal.value = val;
});

watch(selectedPresetIdLocal, (val) => {
  emit('update:selectedPresetId', val);
});

const selectedPreset = computed(() =>
  presets.value.find(p => p.id === selectedPresetIdLocal.value)
);

const fetchPresets = async () => {
  const { data } = await apiClient.get('/presets/');
  presets.value = data;
};

onMounted(fetchPresets);

const applyPreset = () => {
  if (selectedPresetIdLocal.value === null) {
    emit('reset'); // 👉 вызов глобального сброса
    return;
  }
  const p = selectedPreset.value;
  if (!p) return;

  emit('update:fromCityIds', p.from_cities || []);
  emit('update:toCityIds', p.to_cities || []);
  emit('update:selectedSites', p.sites || []);
  emit('update:departureTimeFrom', p.departure_from_time?.slice(0, 5) || '00:00');
  emit('update:departureTimeTo', p.departure_to_time?.slice(0, 5) || '23:59');
  emit('update:arrivalTimeFrom', p.arrival_from_time?.slice(0, 5) || '00:00');
  emit('update:arrivalTimeTo', p.arrival_to_time?.slice(0, 5) || '23:59');
  emit('update:isTransfer', p.is_transfer);
};


const getCurrentFilters = () => ({
  from_cities: props.fromCityIds,
  to_cities: props.toCityIds,
  sites: props.selectedSites,
  departure_from_time: props.departureTimeFrom + ':00',
  departure_to_time: props.departureTimeTo + ':00',
  arrival_from_time: props.arrivalTimeFrom + ':00',
  arrival_to_time: props.arrivalTimeTo + ':00',
  is_transfer: props.isTransfer,
});

// Dialog
const showSaveDialog = ref(false);
const newPresetName = ref('');
const toast = useToast();

const savePreset = async () => {
  if (!newPresetName.value.trim()) {
    toast.add({ severity: 'warn', summary: 'Внимание', detail: 'Введите название шаблона', life: 3000 });
    return;
  }

  saving.value = true;

  try {
    const payload = {
      ...getCurrentFilters(),
      name: newPresetName.value.trim()
    };

    const { data } = await apiClient.post('/scraper/presets/', payload);
    presets.value.push(data);
    selectedPresetIdLocal.value = data.id;
    showSaveDialog.value = false;
    newPresetName.value = '';
  } catch (err) {
  const errorMessage = err.response?.data?.detail || 'Не удалось сохранить шаблон';
  toast.add({ severity: 'error', summary: 'Ошибка', detail: errorMessage, life: 3000 });
  } finally {
    saving.value = false;
  }
};


const showDeleteDialog = ref(false);
const deletePresetConfirmed = async () => {
  if (!selectedPreset.value) return;

  deleting.value = true;

  try {
    await apiClient.delete(`/scraper/presets/${selectedPreset.value.id}`);
    selectedPresetIdLocal.value = null;
    emit('reset');
    await fetchPresets();
    showDeleteDialog.value = false;
  } catch (err) {
  const errorMessage = err.response?.data?.detail || 'Не удалось удалить шаблон';
  toast.add({ severity: 'error', summary: 'Ошибка', detail: errorMessage, life: 3000 });
  } finally {
    deleting.value = false;
  }
};

</script>

<template>
  <div class="mb-4" style="display: flex; flex-direction: row; align-items: flex-start; gap: 0.75rem;">
    <!-- Label + Dropdown -->
    <div style="display: flex; flex-direction: column;">
      <label for="presetDropdown" class="text-sm font-medium mb-1">Шаблоны фильтров</label>
      <Dropdown
        :disabled="props.loading"
        id="presetDropdown"
        v-model="selectedPresetIdLocal"
        :options="[{ id: null, name: '➕ Новый шаблон' }, ...presets.map(p => ({ id: p.id, name: p.name }))]"
        optionLabel="name"
        optionValue="id"
        :modelValue="selectedPresetIdLocal"
        class="w-15rem"
        @change="applyPreset"
      >
        <template #value="slotProps">
          <span v-if="slotProps.value === null">➕ Новый шаблон</span>
          <span v-else>{{ presets.find(p => p.id === slotProps.value)?.name || '➕ Новый шаблон' }}</span>
        </template>
      </Dropdown>
    </div>

    <!-- Кнопки -->
    <div class="flex gap-2" style="margin-top: 1.625rem;">
       <Button
       :disabled="props.loading"
        v-if="selectedPresetIdLocal === null"
        icon="pi pi-save"
        class="p-button-sm p-button-icon-only"
        v-tooltip.top="'Сохранить как новый шаблон'"
        @click="showSaveDialog = true"
        style="height: 2.25rem"
      />
      <Button
        :disabled="props.loading"
        v-if="selectedPresetIdLocal !== null"
        icon="pi pi-trash"
        class="p-button-sm p-button-danger p-button-icon-only"
        v-tooltip.top="'Удалить выбранный шаблон'"
        @click="showDeleteDialog = true"
        style="height: 2.25rem"
      />
    </div>
  </div>

  <Dialog
  v-model:visible="showSaveDialog"
  modal
  header="Сохранить шаблон"
  :style="{ width: '30rem' }"
>
  <div class="mb-4">
    <label for="presetName" class="block text-sm font-medium mb-1">Название шаблона</label>
    <InputText
      id="presetName"
      v-model="newPresetName"
      class="w-full"
      placeholder="Введите название"
    />
  </div>

  <template #footer>
    <Button label="Отменить" icon="pi pi-times" class="p-button-text" @click="showSaveDialog = false" />
    <Button label="Сохранить" icon="pi pi-check" class="p-button-primary"
        :loading="saving"
        :disabled="saving"
        @click="savePreset" />
  </template>
</Dialog>
<Dialog
  v-model:visible="showDeleteDialog"
  modal
  :header="`Удалить шаблон`"
  :style="{ width: '30rem' }"
>
  <p class="mb-4">
    Вы точно хотите удалить шаблон:
    <strong>{{ selectedPreset?.name || 'Без названия' }}</strong>?
  </p>

  <template #footer>
    <Button label="Отменить" icon="pi pi-times" class="p-button-text" @click="showDeleteDialog = false" />
    <Button label="Подтвердить" icon="pi pi-check" class="p-button-danger"
        :loading="deleting"
        :disabled="deleting"
        @click="deletePresetConfirmed" />
  </template>
</Dialog>

</template>