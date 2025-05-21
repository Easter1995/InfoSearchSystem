import { createRouter, createWebHistory } from 'vue-router'

const routes = [
    {
        path: '/',
        redirect: '/search',
    },
    {
        path: '/search',
        name: 'search',
        component: () => import('../views/search.vue')
    }
]

const router = createRouter({
    history: createWebHistory("/"),
    routes,
})

export default router