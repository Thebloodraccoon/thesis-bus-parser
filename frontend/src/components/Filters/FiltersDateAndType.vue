<script setup>
const props = defineProps({
  selectedDate: Date,
  isTransfer: [Boolean, null],
  showDate: {type: Boolean, default: true},
  showTransfer: {type: Boolean, default: true},
  loading: Boolean
})
const emit = defineEmits([
  'update:selectedDate',
  'update:isTransfer',
  'reset'
]);
</script>

<template>
  <!-- Фильтр по дате -->
  <div v-if="showDate" class="flex flex-col">
    <label class="block text-sm font-medium mb-1">Выберите дату</label>
    <Calendar
        :disabled="props.loading"
        :modelValue="props.selectedDate"
        @update:modelValue="emit('update:selectedDate', $event)"
        showIcon
        dateFormat="dd.mm.yy"
        class="w-64"
        :showOtherMonths="true"
        :selectOtherMonths="true"
    />

  </div>

  <!-- Фильтр по пересадке -->
  <div v-if="showTransfer" class="flex flex-col">
    <label class="text-sm font-medium mb-1">Тип маршрута</label>
    <Dropdown
        :disabled="props.loading"
        :modelValue="props.isTransfer"
        @update:modelValue="emit('update:isTransfer', $event)"
        :options="[
        { label: 'Все', value: null },
        { label: 'С пересадкой', value: true },
        { label: 'Без пересадки', value: false }
      ]"
        optionLabel="label"
        optionValue="value"
        placeholder="Все"
        class="w-32"
    />
  </div>

</template>

