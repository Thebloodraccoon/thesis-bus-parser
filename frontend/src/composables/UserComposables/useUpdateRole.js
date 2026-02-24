import { UserService } from '@/service/UserService';
import { useToast } from 'primevue/usetoast';

export function useUpdateRole() {
    const toast = useToast();

    const updateRole = async (user, newRole) => {
        try {
            await UserService.updateUserRole(user.id, newRole);
            toast.add({
                severity: 'success',
                summary: 'Успех',
                detail: 'Роль пользователя успешно изменена',
                life: 3000
            });
        } catch (error) {
            toast.add({
                severity: 'error',
                summary: 'Ошибка',
                detail: error.message,
                life: 5000
            });
            throw error;
        }
    };

    return { updateRole };
}
