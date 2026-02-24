<script setup>
import { ref, watch } from 'vue';

const props = defineProps({
    modelValue: String,
    placeholder: String,
    loading: Boolean
});
const emit = defineEmits(['update:modelValue']);

const internalValue = ref(props.modelValue ?? '');
const showDropdown = ref(false);
const isInvalid = ref(false);

const hours = ref('');
const minutes = ref('');

// Проверка формата времени: HH:mm (24ч)
const isValidTime = (val) => {
    const regex = /^([01]\d|2[0-3]):([0-5]\d)$/;
    return regex.test(val);
};

watch(
    () => props.modelValue,
    (val) => {
        internalValue.value = val || '';
        const [h, m] = (val || '').split(':');
        hours.value = h || '';
        minutes.value = m || '';
        isInvalid.value = !!val && !isValidTime(val);
    }
);

watch([hours, minutes], () => {
    if (hours.value && minutes.value) {
        const formatted = `${hours.value.padStart(2, '0')}:${minutes.value.padStart(2, '0')}`;
        internalValue.value = formatted;
        emit('update:modelValue', formatted);
        isInvalid.value = !isValidTime(formatted);
    }
});

watch(internalValue, (val) => {
    const numeric = val.replace(/\D/g, '').slice(0, 4); // только цифры, макс 4

    let formatted = '';
    if (numeric.length <= 2) {
        formatted = numeric;
    } else {
        formatted = `${numeric.slice(0, 2)}:${numeric.slice(2)}`;
    }

    if (formatted !== internalValue.value) {
        internalValue.value = formatted;
    }

    // Валидация только если пользователь ввел 5 символов (HH:mm)
    if (formatted.length === 5 && formatted.includes(':')) {
        emit('update:modelValue', formatted);
        isInvalid.value = !isValidTime(formatted); // показываем ошибку, если формат неверный
    } else {
        isInvalid.value = false; // не показываем ошибку в процессе ввода
    }
});

const hourOptions = Array.from({ length: 24 }, (_, i) => String(i).padStart(2, '0'));
const minuteOptions = Array.from({ length: 60 }, (_, i) => String(i).padStart(2, '0'));

const selectHour = (val) => {
    hours.value = val;
    showDropdown.value = true;
};
const selectMinute = (val) => {
    minutes.value = val;
    showDropdown.value = true;
};

const hideDropdown = () => {
    setTimeout(() => {
        showDropdown.value = false;
    }, 100);
};

const onInput = (e) => {
    const raw = e.target.value.replace(/\D/g, '').slice(0, 4); // только цифры, макс 4 символа

    let formatted = '';
    if (raw.length <= 2) {
        formatted = raw;
    } else {
        formatted = `${raw.slice(0, 2)}:${raw.slice(2)}`;
    }

    internalValue.value = formatted;

    if (formatted.length === 5 && isValidTime(formatted)) {
        emit('update:modelValue', formatted);
        isInvalid.value = false;
    } else {
        isInvalid.value = true;
    }
};
</script>

<template>
  <div class="relative w-[120px]">
    <InputText
      :disabled="props.loading"
      :value="internalValue"
      :placeholder="placeholder"
      :class="['w-full border rounded-md px-3 py-2 text-sm shadow-sm focus:outline-none focus:ring-2', isInvalid ? 'border-red-500 focus:ring-red-500' : 'focus:ring-primary-500 focus:border-primary-500']"
      @input="onInput"
      @focus="showDropdown = true"
      @blur="hideDropdown"
    />
    <!-- Сообщение об ошибке -->
    <p v-if="isInvalid" class="text-red-500 text-xs mt-1">Введите время в формате HH:mm</p>

    <div v-if="showDropdown" class="absolute z-10 mt-1 w-full grid grid-cols-2 gap-2 rounded-md bg-surface-0 border border-surface-200 dark:border-surface-700 shadow-md text-sm p-2 dark:bg-surface-800">
      <div class="overflow-y-auto max-h-48">
        <div v-for="h in hourOptions" :key="h" @mousedown.prevent="selectHour(h)" :class="['cursor-pointer px-2 py-1 rounded', h === hours ? 'bg-primary-500 text-white' : 'hover:bg-surface-100 dark:hover:bg-surface-600']">
          {{ h }}
        </div>
      </div>
      <div class="overflow-y-auto max-h-48">
        <div v-for="m in minuteOptions" :key="m" @mousedown.prevent="selectMinute(m)" :class="['cursor-pointer px-2 py-1 rounded', m === minutes ? 'bg-primary-500 text-white' : 'hover:bg-surface-100 dark:hover:bg-surface-600']">
          {{ m }}
        </div>
      </div>
    </div>
  </div>
</template>