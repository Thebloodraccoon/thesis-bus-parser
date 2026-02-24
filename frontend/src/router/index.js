import AppLayout from '@/layout/AppLayout.vue';
import {createRouter, createWebHistory} from 'vue-router';
import {useUserStore} from '@/stores/useUserStore';

const routes = [
    {
        path: '/documentation',
        name: 'documentation',
        component: () => import('@/views/utilities/Documentation.vue')
    },

    {
        path: '/',
        component: AppLayout,
        children: [
            {
                path: '/',
                name: 'Сегмент по дате',
                meta: {
                    breadcrumb: ['Сегмент по дате'],
                    requiresAuth: true
                },
                component: () => import('@/views/dashboards/RouteByDatePage.vue')
            },
            {
                path: '/route',
                name: 'RouteBySegmentPage',
                meta: {
                    breadcrumb: ['Сегмент в диапазоне дат'],
                    requiresAuth: true
                },
                component: () => import('@/views/dashboards/RouteBySegmentPage.vue'),
            },
            {
                path: '/users',
                name: 'users',
                meta: {
                    breadcrumb: ['Users', 'Users List'],
                    requiresAuth: true,
                    requiresAdmin: true
                },
                component: () => import('@/views/user-management/UserPage.vue')
            },
            {
                path: '/task',
                meta: {
                    breadcrumb: ['Tasks', 'Task List'],
                    requiresAuth: true,
                    requiresAdmin: true
                },
                children: [
                    {
                        path: '',
                        name: 'task list',
                        component: () => import('@/views/tasks/TaskPage.vue')

                    },
                    {
                        path: 'progress',
                        name: 'Task Progress',
                        component: () => import('@/views/tasks/TaskProgress.vue')
                    }
                ]
            },
            {
                path: '/site',
                meta: {
                    requiresAuth: true
                },
                children: [
                    {
                        path: 'list',
                        name: 'SitesList',
                        component: () => import('@/views/sites/SiteList.vue')
                    },
                    {
                        path: 'create',
                        name: 'CreateSite',
                        component: () => import('@/views/sites/CreateSite.vue'),
                        meta: {
                            requiresAdmin: true
                        }
                    },
                    {
                        path: ':id',
                        name: 'SiteDetail',
                        component: () => import('@/views/sites/SiteDetail.vue')
                    }
                ]
            },
            {
                path: '/city',
                name: 'city',
                meta: {
                    requiresAuth: true
                },
                children: [
                    {
                        path: 'list',
                        name: 'Cities List',
                        component: () => import('@/views/cities/CitiesList.vue')
                    }
                ]
            }
        ]
    },
    {
        path: '/auth/login',
        name: 'login',
        component: () => import('@/views/pages/auth/Login.vue')
    },
    {
        path: '/:pathMatch(.*)*',
        name: 'notfound',
        component: () => import('@/views/pages/NotFound.vue')
    }
];

// Create Vue Router instance
const router = createRouter({
    history: createWebHistory(),
    routes,
    scrollBehavior() {
        return {left: 0, top: 0};
    }
});

router.beforeEach(async (to, from, next) => {
    const token = localStorage.getItem('access_token');
    const isAuthenticated = !!token;
    const {user, isAdmin, fetchCurrentUser} = useUserStore();

    if (to.path.startsWith('/auth')) {
        next();
        return;
    }

    if (to.meta.requiresAuth) {
        if (isAuthenticated) {
            try {
                if (!user.value) {
                    await fetchCurrentUser();
                }

                if (to.meta.requiresAdmin && !isAdmin.value) {
                    next('/');
                    return;
                }

                next();
            } catch (error) {
                localStorage.removeItem('access_token');
                localStorage.setItem('redirectPath', to.fullPath);
                next('/auth/login');
            }
        } else {
            localStorage.setItem('redirectPath', to.fullPath);
            next('/auth/login');
        }
    } else {
        next();
    }
});
export default router;
