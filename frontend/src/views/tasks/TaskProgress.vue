<script setup>
import {ref, onMounted, onBeforeUnmount, computed} from 'vue';
import apiClient from '@/api/axios';
import {useToast} from 'primevue/usetoast';
import {useAggregators} from '@/composables/RoutesByDate/useAggregators';
import {formatDate} from "@/service/dateUtils";

const toast = useToast();
const stats = ref([]);
const loading = ref(false);
const siteId = ref(null);
const isActive = ref(true); // ✅ "Все" по умолчанию

const {aggregators, aggregatorsData, allAggregators, fetchAggregators} = useAggregators();

const isActiveOptions = [
  {label: 'Все', value: null},
  {label: 'Активные', value: true},
  {label: 'Завершённые', value: false}
];

const fetchStats = async () => {
  loading.value = true;
  try {
    const params = {};
    if (siteId.value !== null) params.site_id = siteId.value;
    if (isActive.value !== null) params.is_active = isActive.value;

    const {data} = await apiClient.get('/scraper/parser-stats/', {params});
    stats.value = data.map(item => ({
      ...item,
      date_progress: getDateProgress(item),
      route_progress: getRouteProgress(item)
    }));
  } catch (err) {
    toast.add({
      severity: 'error',
      summary: 'Ошибка',
      detail: err.response?.data?.detail || 'Не удалось загрузить данные',
      life: 3000
    });
  } finally {
    loading.value = false;
  }
};

const getDateProgress = (data) => {
  const start = new Date(data.start_date);
  const end = new Date(data.end_date);
  const current = new Date(data.current_date);
  const total = end - start;
  const passed = current - start;
  return Math.min(100, Math.max(0, Math.round((passed / total) * 100)));
};

const getRouteProgress = (data) => {
  if (!data.total_count) return 0;
  return Math.round(((data.success_count + data.error_count) / data.total_count) * 100);
};


const refreshInterval = 300; // 5 минут в секундах
const secondsLeft = ref(refreshInterval);

let intervalId;

const startCountdown = () => {
  intervalId = setInterval(() => {
    secondsLeft.value--;
    if (secondsLeft.value <= 0) {
      fetchStats();
      secondsLeft.value = refreshInterval;
    }
  }, 1000);
};

const showMetricsDialog = ref(false);
const selectedParser = ref(null);

// Функция для открытия попапа с метриками
const openMetricsDialog = (parserData) => {
  selectedParser.value = parserData;
  showMetricsDialog.value = true;
};

const parserMetrics = computed(() => {
  if (!selectedParser.value) return null;

  const parser = selectedParser.value;
  const aggregator = aggregatorsData.value[parser.site_id];
  const threads = aggregator?.threads || 1;

  const startDate = new Date(parser.created_at);
  const currentDate = new Date();
  let elapsedSeconds;
  let hoursPassed;

  if (parser.is_active) {
    const elapsedMs = currentDate - startDate;
    elapsedSeconds = elapsedMs / 1000;
    hoursPassed = elapsedSeconds / 3600;
  } else {
    hoursPassed = 24;
    elapsedSeconds = 24 * 3600; // фиксируем тоже 24 часа в секундах
  }
  const daysPassed = hoursPassed / 24;


  const parsedDays = (new Date(parser.current_date) - new Date(parser.start_date)) / (1000 * 60 * 60 * 24);
  const totalDays = (new Date(parser.end_date) - new Date(parser.start_date)) / (1000 * 60 * 60 * 24);
  const remainingDays = totalDays - parsedDays;

  const requestsPerHour = parser.success_count / hoursPassed;
  const requestsPerDay = parser.success_count / daysPassed;
  const requestsPerHourSingleThread = requestsPerHour / threads;
  const requestsPerDaySingleThread = requestsPerDay / threads;

  const avgDayParsingTime = hoursPassed / Math.max(1, parsedDays);

  // Среднее время на один запрос (по всей системе)
  const avgTimePerRequestSeconds = elapsedSeconds / Math.max(1, parser.success_count);

  // Среднее время на один запрос, если пересчитать на один поток
  const avgTimePerRequestPerThreadSeconds = avgTimePerRequestSeconds * threads;

  const progressPercentage = (parsedDays / totalDays) * 100;

  const successRate = (parser.success_count / parser.total_count * 100).toFixed(1);
  const errorRate = (parser.error_count / parser.total_count * 100).toFixed(1);
  const likebusFoundRate = (parser.likebus_found / parser.success_count * 100).toFixed(1);

  // Новый расчёт оставшегося времени
  const estimatedRemainingHours = avgDayParsingTime * remainingDays;
  const estimatedRemainingDays = estimatedRemainingHours / 24;
  const totalEstimatedHours = avgDayParsingTime * totalDays;
  const speedCoefficient = totalEstimatedHours > 0 ? (24 / totalEstimatedHours).toFixed(2) : 'N/A';
  const requiredThreads = speedCoefficient < 1 ? Math.ceil(threads / speedCoefficient) : threads;

  return {
    threads,
    startDate: formatDate(parser.created_at),
    currentDate: formatDate(currentDate),
    totalRequests: parser.success_count,
    hoursPassed: hoursPassed.toFixed(1),
    daysPassed: daysPassed.toFixed(1),
    parsedDays: parsedDays.toFixed(1),
    requestsPerHour: requestsPerHour.toFixed(1),
    requestsPerDay: requestsPerDay.toFixed(1),
    requestsPerHourSingleThread: requestsPerHourSingleThread.toFixed(1),
    requestsPerDaySingleThread: requestsPerDaySingleThread.toFixed(1),
    avgDayParsingTime: avgDayParsingTime.toFixed(1),
    avgTimePerRequestSeconds: avgTimePerRequestSeconds.toFixed(4),
    avgTimePerRequestPerThreadSeconds: avgTimePerRequestPerThreadSeconds.toFixed(4),
    progressPercentage: progressPercentage.toFixed(1),
    remainingDays: remainingDays.toFixed(1),
    successRate,
    errorRate,
    likebusFoundRate,
    estimatedRemainingHours: estimatedRemainingHours.toFixed(1),
    estimatedRemainingDays: estimatedRemainingDays.toFixed(1),
    speedCoefficient,
    requiredThreads,

  };
});

const getSpeedCoefficient = (data) => {
  if (!data.created_at || !data.start_date || !data.end_date) return 0;

  const startDate = new Date(data.created_at);
  let elapsedHours;
  if (data.is_active) {
    const currentDate = new Date();
    elapsedHours = (currentDate - startDate) / (1000 * 60 * 60);
  } else {
    elapsedHours = 24; // фиксируем как 24 часа для завершённых
  }

  const totalDays = (new Date(data.end_date) - new Date(data.start_date)) / (1000 * 60 * 60 * 24);
  const parsedDays = (new Date(data.current_date) - new Date(data.start_date)) / (1000 * 60 * 60 * 24);

  if (parsedDays <= 0) return 0;

  const avgDayParsingTime = elapsedHours / parsedDays;
  const totalEstimatedHours = avgDayParsingTime * totalDays;

  return totalEstimatedHours > 0 ? (24 / totalEstimatedHours) : 0;
};
const getSpeedometerStyle = (data) => {
  const coefficient = getSpeedCoefficient(data);
  const percentage = coefficient * 100; // 1.0 = 100%
  return {
    '--fill-width': `${percentage}%`,
    '--fill-color': coefficient >= 1 ? '#4CAF50' : '#F44336'
  };
};

const getSpeedCoefficientClass = (data) => {
  const coefficient = getSpeedCoefficient(data);
  return {
    'text-green-500': coefficient >= 1,
    'text-red-500': coefficient < 1,
    'font-bold': true
  };
};

function formatSize(kb) {
  if (kb >= 1024 * 1024) {
    return (kb / (1024 * 1024)).toFixed(2) + ' GB';
  } else if (kb >= 1024) {
    return (kb / 1024).toFixed(2) + ' MB';
  } else {
    return kb.toFixed(2) + ' KB';
  }
}


onMounted(async () => {
  await fetchAggregators(false);
  await fetchStats();
  startCountdown();
});

onBeforeUnmount(() => {
  clearInterval(intervalId);
});

</script>

<template>
  <div>
    <!-- Фильтры -->
    <div class="flex gap-4 mb-4 items-end">
      <Dropdown
          v-model="siteId"
          :options="[{ label: 'Все', value: null }, ...allAggregators]"
          optionLabel="label"
          optionValue="value"
          placeholder="Агент"
          class="w-64"
      />
      <Dropdown v-model="isActive" :options="isActiveOptions" optionLabel="label" optionValue="value"
                placeholder="Статус задачи" class="w-64"/>
      <Button
        :label="`Обновить (${secondsLeft}s)`"
        icon="pi pi-refresh"
        @click="() => { fetchStats(); secondsLeft = refreshInterval }"
        :loading="loading"
      />
    </div>

    <!-- Таблица -->
    <DataTable :value="stats" :loading="loading" scrollable stripedRows >
      <Column header="Агент">
        <template #body="{ data }">
          {{ aggregators[data.site_id] || `ID ${data.site_id}` }}
        </template>
      </Column>

      <Column header="Скорость">
        <template #body="{ data }">
          <div class="flex items-center gap-1">
            <div class="speedometer" :style="getSpeedometerStyle(data)">
              <div class="speedometer-fill"></div>
            </div>
            <span :class="getSpeedCoefficientClass(data)">
              {{ getSpeedCoefficient(data).toFixed(2) }}
            </span>
          </div>
        </template>
      </Column>

  <Column header="Потоки">
    <template #body="{ data }">
      <Tag v-if="aggregatorsData[data.site_id]?.threads" :value="aggregatorsData[data.site_id].threads" severity="info" />
      <span v-else class="text-gray-400">—</span>
    </template>
  </Column>

  <Column header="Дата" :sortable="true" sortField="date_progress">
    <template #body="{ data }">
      <div class="flex flex-col gap-1">
        <ProgressBar :value="getDateProgress(data)" :showValue="false" style="height: 10px;" />
        <div class="flex justify-between text-xs text-gray-400">
          <span>{{ formatDate(data.start_date, { showTime: false }) }}</span>
          <span class="font-semibold">{{ getDateProgress(data) }}%</span>
          <span>{{ formatDate(data.end_date, { showTime: false }) }}</span>
        </div>
      </div>
    </template>
  </Column>

  <Column header="Маршр." :sortable="true" sortField="route_progress">
    <template #body="{ data }">
      <div class="flex flex-col gap-1">
        <ProgressBar :value="getRouteProgress(data)" :showValue="false" style="height: 10px;" />
        <div class="flex justify-between text-xs text-gray-400">
          <span>{{ formatDate(data.current_date, { showTime: false }) }}</span>
          <span class="font-semibold">{{ getRouteProgress(data) }}%</span>
          <span>{{ data.daily_success_count + data.daily_error_count }}/{{ data.daily_total_count }}</span>
        </div>
      </div>
    </template>
  </Column>

  <Column header="✔">
    <template #body="{ data }">
      <i :class="['pi', data.is_active ? 'pi-check-circle text-green-500' : 'pi-times-circle text-red-500']" />
    </template>
  </Column>

  <Column header="Усп." :sortable="true" sortField="success_count">
    <template #body="{ data }">
      {{ data.success_count }}
    </template>
  </Column>

  <Column header="Ошиб." :sortable="true" sortField="error_count">
    <template #body="{ data }">
      {{ data.error_count }}
    </template>
  </Column>

  <Column header="LB +"  :sortable="true" sortField="likebus_found">
    <template #body="{ data }">
      {{ data.likebus_found }}
    </template>
  </Column>

  <Column header="LB −"  :sortable="true" sortField="likebus_not_found">
    <template #body="{ data }">
      {{ data.likebus_not_found }}
    </template>
  </Column>

  <Column header="Размер" :sortable="true" sortField="total_response_size_kb">
    <template #body="{ data }">
      {{ formatSize(data.total_response_size_kb) }}
    </template>
  </Column>


  <Column header="">
    <template #body="{ data }">
      <Button icon="pi pi-chart-line" @click="openMetricsDialog(data)" class="p-button-sm p-button-text" />
    </template>
  </Column>
</DataTable>

    <Dialog v-model:visible="showMetricsDialog" header="Детальная статистика парсера" :modal="true" :style="{ width: '700px' }">
  <div v-if="parserMetrics" class="flex flex-col gap-6 p-2">

    <!-- Основная информация -->
    <section>
      <h2 class="text-xl font-bold mb-2">{{ aggregators[selectedParser.site_id] || `ID ${selectedParser.site_id}` }}</h2>
      <div class="grid grid-cols-2 gap-2 text-sm">
        <div>
          <p><span class="font-semibold">Потоки:</span> {{ parserMetrics.threads }}</p>
          <p><span class="font-semibold">Начало:</span> {{ parserMetrics.startDate }}</p>
        </div>
        <div>
          <p><span class="font-semibold">Прошло времени:</span> {{ parserMetrics.daysPassed }} дн ({{ parserMetrics.hoursPassed }} ч)</p>
        </div>
      </div>
    </section>

    <Divider />

    <!-- Коэффициент скорости -->
    <section>
      <h3 class="text-lg font-semibold mb-2">Коэффициент скорости</h3>
      <p class="text-sm mb-1">
        <span class="font-semibold">Коэффициент:</span>
        <span :class="{'text-green-500': parserMetrics.speedCoefficient >= 1, 'text-red-500': parserMetrics.speedCoefficient < 1}">
          {{ parserMetrics.speedCoefficient }}
        </span>
      </p>
      <p class="text-xs text-gray-500 mb-1">(≥1 — укладывается за сутки; &lt;1 — требуется ускорение)</p>
      <p v-if="parserMetrics.speedCoefficient < 1" class="text-sm">
        <span class="font-semibold">Рекомендуемое количество потоков:</span> {{ parserMetrics.requiredThreads }}
      </p>
    </section>

    <Divider />

    <!-- Прогресс -->
    <section>
      <h3 class="text-lg font-semibold mb-2">Прогресс парсинга</h3>
      <div class="grid grid-cols-2 gap-2 text-sm">
        <div>
          <p class="font-semibold mb-1">Среднее время на запрос:</p>
          <p>Общее: {{ parserMetrics.avgTimePerRequestSeconds }} сек</p>
          <p>На один поток: {{ parserMetrics.avgTimePerRequestPerThreadSeconds }} сек</p>
        </div>
        <div>
          <p class="font-semibold mb-1">Среднее время парсинга дня:</p>
          <p>{{ parserMetrics.avgDayParsingTime }} ч</p>
        </div>
      </div>
    </section>

    <Divider />

    <!-- Производительность -->
    <section>
      <h3 class="text-lg font-semibold mb-2">Производительность</h3>
      <div class="grid grid-cols-2 gap-2 text-sm">
        <div>
          <p><span class="font-semibold">Запросов в час (все потоки):</span> {{ parserMetrics.requestsPerHour }}</p>
          <p><span class="font-semibold">Запросов в день (все потоки):</span> {{ parserMetrics.requestsPerDay }}</p>
        </div>
        <div>
          <p><span class="font-semibold">Запросов в час (1 поток):</span> {{ parserMetrics.requestsPerHourSingleThread }}</p>
          <p><span class="font-semibold">Запросов в день (1 поток):</span> {{ parserMetrics.requestsPerDaySingleThread }}</p>
        </div>
      </div>
    </section>

    <Divider />

    <!-- Прогноз завершения -->
    <section v-if="selectedParser.is_active">
      <h3 class="text-lg font-semibold mb-2">Прогноз завершения</h3>
      <p class="text-sm">
        При текущей скорости парсинг завершится примерно через
        <span class="font-semibold">{{ parserMetrics.estimatedRemainingHours }} ч</span>
        (<span class="font-semibold">{{ parserMetrics.estimatedRemainingDays }} дн</span>)
      </p>
    </section>
  </div>
</Dialog>

  </div>
</template>

<style scoped>
.speedometer {
  width: 80px;
  height: 12px;
  background-color: #2d3748;
  border-radius: 6px;
  overflow: hidden;
  position: relative;
}

.speedometer-fill {
  position: absolute;
  left: 0;
  top: 0;
  height: 100%;
  width: var(--fill-width);
  background-color: var(--fill-color);
  transition: width 0.3s ease;
}
</style>