import { ref } from 'vue';
import apiClient from '@/api/axios';
import { useToast } from 'primevue/usetoast';

export function useTaskDialog() {
    const isDialogVisible = ref(false);
    const taskData = ref(null);
    const loading = ref(false);
    const error = ref(null);
    const saving = ref(false);
    const toast = useToast();

    const openDialog = async (taskId) => {
        isDialogVisible.value = true;
        loading.value = true;
        error.value = null;
        try {
            const response = await apiClient.get(`/celery/schedule/${taskId}`);
            taskData.value = response.data;
        } catch (err) {
            error.value = 'Ошибка загрузки данных';
            console.error('Ошибка загрузки задачи:', err);
        } finally {
            loading.value = false;
        }
    };

    // Закрытие диалога
    const closeDialog = () => {
        isDialogVisible.value = false;
        taskData.value = null;
        error.value = null;
    };

    // Обновление расписания
    const updateSchedule = async (updatedData) => {
        if (!updatedData?.id) return;

        saving.value = true;
        error.value = null;

        try {
            await apiClient.put(`/celery/schedule/${updatedData.id}`, updatedData);
            toast.add({
                severity: 'success',
                summary: 'Успех',
                detail: 'Schedule Successfully Updated',
                life: 3000
            });
            closeDialog();
        } catch (err) {
            error.value = 'Schedule update error';
            toast.add({
                severity: 'error',
                summary: 'Ошибка',
                detail: 'Schedule update error',
                life: 5000
            });
            closeDialog();
        } finally {
            saving.value = false;
        }
    };

    return { isDialogVisible, taskData, loading, saving, error, openDialog, closeDialog, updateSchedule };
}
