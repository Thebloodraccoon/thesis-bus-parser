import { UserService } from '@/service/UserService';
import { useToast } from 'primevue/usetoast';

export function useDeleteUser(deleteUserDialogRef) {
    const toast = useToast();

    const openDeleteDialog = (userId) => {
        deleteUserDialogRef.value?.openDialog(userId);
    };

    const handleDeleteUser = async (userId, onSuccess) => {
        try {
            await UserService.deleteUser(userId);
            toast.add({
                severity: 'success',
                summary: 'Успех',
                detail: 'User successfully deleted',
                life: 3000
            });
            deleteUserDialogRef.value?.closeDialog();
            onSuccess?.();
        } catch (error) {
            toast.add({
                severity: 'error',
                summary: 'Error',
                detail: error.message,
                life: 5000
            });
            throw error;
        }
    };

    return { openDeleteDialog, handleDeleteUser };
}
