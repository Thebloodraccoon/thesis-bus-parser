import { ref } from 'vue';
import { UserService } from '@/service/UserService';
import { useToast } from 'primevue/usetoast';

export function useInviteUser() {
    const toast = useToast();
    const inviteUserDialog = ref(null);
    const isLoading = ref(false);

    const openInviteDialog = () => {
        inviteUserDialog.value.openDialog();
    };

    const handleInviteUser = async (form) => {
        isLoading.value = true;
        try {
            const newUser = await UserService.inviteUser(form.email, form.role);
            toast.add({
                severity: 'success',
                summary: 'Успех',
                detail: 'User Successfully Invited',
                life: 3000
            });
            inviteUserDialog.value.closeDialog();
            return newUser;
        } catch (error) {
            toast.add({
                severity: 'error',
                summary: 'Error',
                detail: error.message,
                life: 5000
            });
            throw error;
        } finally {
            isLoading.value = false;
        }
    };

    return { inviteUserDialog, openInviteDialog, handleInviteUser, isLoading };
}
