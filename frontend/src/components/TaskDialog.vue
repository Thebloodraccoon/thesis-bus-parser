<script setup>
import { defineProps, defineEmits, ref, watch } from 'vue';

const props = defineProps({
    visible: Boolean,
    taskData: Object,
    loading: Boolean,
    error: String,
    saving: Boolean
});

const emit = defineEmits(['update:visible', 'save']);

const localTaskData = ref({});

watch(
    () => props.taskData,
    (newTaskData) => {
        if (newTaskData) {
            localTaskData.value = { ...newTaskData };
        }
    },
    { deep: true }
);

const closeDialog = () => {
    emit('update:visible', false);
};

const saveChanges = () => {
    emit('save', localTaskData.value);
};
</script>

<template>
    <Dialog
        :visible="visible"
        modal
        header="Редактирование задачи"
        :style="{ width: '700px' }"
        class="custom-dialog"
        @update:visible="(value) => emit('update:visible', value)"
    >
        <div v-if="loading" class="flex justify-center">
            <ProgressSpinner />
        </div>
        <div v-else-if="error" class="text-red-500 text-center">
            {{ error }}
        </div>
        <div v-else-if="taskData" class="dialog-content">
            <!-- Карточка со справкой по Cron -->
            <Card class="cron-info">
                <template #title>Синтаксис Cron Celery</template>
                <template #content>
                    <p><strong>Минуты:</strong> (0-59)</p>
                    <p><strong>Часы:</strong> (0-23)</p>
                    <p><strong>Дни месяца:</strong> (1-31)</p>
                    <p><strong>Месяцы:</strong> (1-12)</p>
                    <p><strong>Дни недели:</strong> (0-6, где 0 — воскресенье)</p>

                    <hr class="divider" />

                    <p><strong>Специальные символы:</strong></p>
                    <ul class="syntax-list">
                        <li><code>*</code> — любое значение</li>
                        <li><code>-</code> — диапазон значений (например, <code>1-5</code> означает 1, 2, 3, 4, 5)</li>
                        <li><code>/</code> — шаг значений (например, <code>*/5</code> — каждые 5 единиц)</li>
                        <li><code>,</code> — список значений (например, <code>1,3,5</code> означает 1, 3 и 5)</li>
                    </ul>

                    <hr class="divider" />

                    <p class="example"><strong>Пример:</strong> <code>0 12 * * 1</code> — каждую **неделю по понедельникам в 12:00**</p>
                </template>
            </Card>

            <!-- Форма редактирования -->
            <div class="task-edit-form flex flex-col gap-4 w-full">
                <div class="flex flex-col">
                    <label class="font-semibold mb-1">Минуты</label>
                    <InputText v-model="localTaskData.minute" class="p-inputtext w-full" />
                </div>

                <div class="flex flex-col">
                    <label class="font-semibold mb-1">Часы</label>
                    <InputText v-model="localTaskData.hour" class="p-inputtext w-full" />
                </div>

                <div class="flex flex-col">
                    <label class="font-semibold mb-1">День недели</label>
                    <InputText v-model="localTaskData.day_of_week" class="p-inputtext w-full" />
                </div>

                <div class="flex flex-col">
                    <label class="font-semibold mb-1">День месяца</label>
                    <InputText v-model="localTaskData.day_of_month" class="p-inputtext w-full" />
                </div>

                <div class="flex flex-col">
                    <label class="font-semibold mb-1">Месяц</label>
                    <InputText v-model="localTaskData.month_of_year" class="p-inputtext w-full" />
                </div>
            </div>
        </div>

        <template #footer>
            <div class="flex justify-end gap-2">
                <Button
                    label="Сохранить"
                    icon="pi pi-check"
                    class="p-button-success"
                    @click="saveChanges"
                    :loading="saving"
                />
                <Button label="Отмена" icon="pi pi-times" class="p-button-secondary" @click="closeDialog" />
            </div>
        </template>
    </Dialog>
</template>

<style scoped>
/* Контейнер внутри диалогового окна */
.dialog-content {
    display: flex;
}
</style>
<style scoped>

/* Список специальных символов */
.syntax-list {
    list-style: none;
    padding-left: 10px;
}

.syntax-list li {
    font-size: 13px;
    margin-bottom: 4px;
}

.syntax-list code {
    font-weight: bold;
    color: #2563eb;
}

/* Разделительная линия */
.divider {
    border: none;
    border-top: 1px solid #d1d5db;
    margin: 8px 0;
}

/* Стиль для диалогового окна */
.custom-dialog {
    text-align: left;
    max-width: 700px;
}

</style>