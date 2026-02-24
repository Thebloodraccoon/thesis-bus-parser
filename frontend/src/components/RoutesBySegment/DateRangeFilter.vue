<script setup>
import { ref, watch } from 'vue';

const props = defineProps({
  loading: Boolean,
  modelValue: Array
});

const emit = defineEmits(['update:modelValue']);

// Установка даты от сегодня до +7 по умолчанию, если modelValue пустой
const today = new Date();
const in7days = new Date();
in7days.setDate(today.getDate() + 7);

const range = ref(
  props.modelValue?.length === 2 ? [...props.modelValue] : [today, in7days]
);

watch(() => props.modelValue, (val) => {
  if (val?.length === 2) {
    range.value = [...val];
  }
});

function getRange() {
  return [...range.value];
}

defineExpose({ getRange });

</script>

<template>
  <div class="flex flex-col gap-1">
    <label class="text-sm font-medium mb-1">Выберите диапазон дат</label>
    <Calendar
      :disabled="props.loading"
      v-model="range"
      selectionMode="range"
      :manualInput="false"
      showIcon
      dateFormat="dd.mm.yy"
      placeholder="Выберите даты"
      class="w-64"
      :showOtherMonths="true"
      :selectOtherMonths="true"
    />
  </div>
</template>
