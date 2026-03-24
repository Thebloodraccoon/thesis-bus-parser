<script setup>
import { ref, onMounted, onUnmounted } from 'vue';

const isVisible = ref(false);

const onScroll = () => {
  isVisible.value = window.scrollY > 500;
};

const scrollToTop = () => {
  window.scrollTo({ top: 0, behavior: 'smooth' });
};

onMounted(() => {
  window.addEventListener('scroll', onScroll);
});

onUnmounted(() => {
  window.removeEventListener('scroll', onScroll);
});
</script>


<template>
  <button
    v-show="isVisible"
    @click="scrollToTop"
    class="fixed bottom-6 right-6 bg-primary-600 hover:bg-primary-700 text-white px-5 py-3 rounded-lg transition-opacity z-50 flex items-center justify-center"
    aria-label="Scroll to top"
  >
    <i class="pi pi-arrow-up text-xl" />
  </button>
</template>
