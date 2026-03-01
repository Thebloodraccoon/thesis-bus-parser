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
                detail: 'User role changed successfully',
                life: 3000
            });
        } catch (error) {
            toast.add({
                severity: 'error',
                summary: 'An error occurred',
                detail: error.message,
                life: 5000
            });
            throw error;
        }
    };

    return { updateRole };
}
