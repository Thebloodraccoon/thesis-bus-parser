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
  <div v-if="showDate" class="flex flex-col">
    <label class="block text-sm font-medium mb-1">Select date</label>
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

  <div v-if="showTransfer" class="flex flex-col">
    <label class="text-sm font-medium mb-1">Route type</label>
    <Dropdown
        :disabled="props.loading"
        :modelValue="props.isTransfer"
        @update:modelValue="emit('update:isTransfer', $event)"
        :options="[
        { label: 'ALL', value: null },
        { label: 'With a transfer', value: true },
        { label: 'No Transfer', value: false }
      ]"
        optionLabel="label"
        optionValue="value"
        placeholder="ALL"
        class="w-32"
    />
  </div>

</template>

