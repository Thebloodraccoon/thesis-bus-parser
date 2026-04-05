<script setup>
import { ref, watch, computed } from 'vue';
import Dialog from 'primevue/dialog';
import apiClient from '@/api/axios';
import { useToast } from 'primevue/usetoast';
import { formatDate } from '@/service/dateUtils';
import { currencySymbol, formatPrice } from '@/service/currencyUtils';

const props = defineProps({
  visible: Boolean,
  routeId: Number,
  departureTimeFrom: String,
  departureTimeTo: String,
  arrivalTimeFrom: String,
  arrivalTimeTo: String,
  isTransfer: Boolean,
  aggregatorName: String,
  CitiesName: String,
  selectedDate: [Date, String]
});

const emit = defineEmits(['update:visible']);

const toast = useToast();
const loading = ref(false);
const tripsData = ref({ total_segments_count: 0, trips: [] });

const chartType = ref('bar');
const chartTypeOptions = [
  { label: 'Bar',   value: 'bar' },
  { label: 'Linear', value: 'line' },
];

const trips = computed(() => tripsData.value.trips || []);
const currency = computed(() => trips.value[0]?.currency || '');

const prices = computed(() =>
  trips.value.map(t => t.price).filter(p => p != null).sort((a, b) => a - b)
);

const stats = computed(() => {
  const arr = prices.value;
  if (!arr.length) return { min: 0, max: 0, median: 0 };
  const mid = Math.floor(arr.length / 2);
  const median = arr.length % 2 !== 0 ? arr[mid] : (arr[mid - 1] + arr[mid]) / 2;
  return { min: arr[0], max: arr[arr.length - 1], median };
});

const chartData = computed(() => {
  const sorted = [...trips.value]
    .filter(t => t.departure_time && t.price != null)
    .sort((a, b) => a.departure_time.localeCompare(b.departure_time));

  if (!sorted.length) return null;

  const labels = sorted.map(t => t.departure_time.slice(0, 5));
  const data   = sorted.map(t => t.price);
  const min    = stats.value.min;
  const max    = stats.value.max;

  const colorFor = (p) => {
    if (p === min) return { bg: 'rgba(59,130,246,0.75)',  border: 'rgb(59,130,246)' };
    if (p === max) return { bg: 'rgba(239,68,68,0.75)',   border: 'rgb(239,68,68)' };
    return          { bg: 'rgba(251,146,60,0.75)',  border: 'rgb(251,146,60)' };
  };

  return {
    labels,
    datasets: [{
      label: 'Price',
      data,
      backgroundColor: data.map(p => colorFor(p).bg),
      borderColor:     data.map(p => colorFor(p).border),
      borderWidth: 2,
      tension: 0.35,
      pointBackgroundColor: data.map(p => colorFor(p).border),
      pointRadius: 5,
      pointHoverRadius: 7,
    }]
  };
});

const chartOptions = computed(() => ({
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { display: false },
    tooltip: {
      callbacks: {
        title: (ctx) => `Departure: ${ctx[0].label}`,
        label: (ctx) => `Price: ${formatPrice(ctx.parsed.y, currency.value)}`
      }
    }
  },
  scales: {
    y: {
      ticks: { callback: (v) => formatPrice(v, currency.value) },
      grid:  { color: 'rgba(255,255,255,0.06)' }
    },
    x: { grid: { display: false } }
  }
}));

const exporting = ref(false);

const exportToCSV = async () => {
  if (!props.routeId) return;
  exporting.value = true;
  try {
    const p = new URLSearchParams({ route_id: props.routeId });
    if (props.departureTimeFrom) p.set('departure_time_from', props.departureTimeFrom);
    if (props.departureTimeTo)   p.set('departure_time_to',   props.departureTimeTo);
    if (props.arrivalTimeFrom)   p.set('arrival_time_from',   props.arrivalTimeFrom);
    if (props.arrivalTimeTo)     p.set('arrival_time_to',     props.arrivalTimeTo);
    if (props.isTransfer != null) p.set('is_transfer', props.isTransfer);

    const response = await apiClient.get(`/routes/export-trips?${p.toString()}`, {
      responseType: 'blob',
    });

    const disposition = response.headers['content-disposition'] || '';
    const match = disposition.match(/filename="?([^"]+)"?/);
    const filename = match ? match[1] : `trips_route_${props.routeId}.csv`;

    const url = URL.createObjectURL(new Blob([response.data], { type: 'text/csv' }));
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  } catch {
    toast.add({ severity: 'error', summary: 'Export failed', detail: 'Could not download CSV', life: 3000 });
  } finally {
    exporting.value = false;
  }
};

const fetchTrips = async () => {
  if (!props.routeId) return;
  loading.value = true;
  tripsData.value = { total_segments_count: 0, trips: [] };
  try {
    const params = { route_id: props.routeId };
    if (props.departureTimeFrom) params.departure_time_from = props.departureTimeFrom;
    if (props.departureTimeTo)   params.departure_time_to   = props.departureTimeTo;
    if (props.arrivalTimeFrom)   params.arrival_time_from   = props.arrivalTimeFrom;
    if (props.arrivalTimeTo)     params.arrival_time_to     = props.arrivalTimeTo;
    if (props.isTransfer)        params.is_transfer         = true;

    const { data } = await apiClient.get('/routes/trips/', {
      params,
      paramsSerializer: (p) => {
        const s = new URLSearchParams();
        Object.keys(p).forEach(k => s.append(k, p[k]));
        return s.toString();
      }
    });
    tripsData.value = data;
  } catch {
    toast.add({ severity: 'error', summary: 'FAILED', detail: 'Segments could not load', life: 3000 });
  } finally {
    loading.value = false;
  }
};

watch(() => props.visible, (val) => { if (val) fetchTrips(); });

const fmt = (dateStr, timeStr) => {
  if (!dateStr || !timeStr) return { date: '—', time: '—' };
  const [, month, day] = dateStr.split('-');
  const [h, m]         = timeStr.split(':');
  return { date: `${day}.${month}`, time: `${h}:${m}` };
};
</script>

<template>
  <Dialog
    :draggable="false"
    :visible="props.visible"
    @update:visible="emit('update:visible', $event)"
    modal
    :style="{ width: '70vw', maxHeight: '100vh' }"
  >
    <template #header>
      <div class="flex items-start justify-between w-full gap-4">
        <div class="flex flex-col gap-1 leading-tight">
          <span class="font-bold text-base">{{ props.CitiesName }}</span>
          <div class="flex flex-wrap gap-x-4 gap-y-1 text-xs text-surface-400">
            <span>{{ formatDate(props.selectedDate, { showTime: false, showSeconds: false }) }}</span>
            <span>{{ props.aggregatorName }}</span>
            <span v-if="props.departureTimeFrom">🕐 {{ props.departureTimeFrom }} — {{ props.departureTimeTo }}</span>
            <span v-if="props.arrivalTimeFrom">🕑 arrival: {{ props.arrivalTimeFrom }} — {{ props.arrivalTimeTo }}</span>
            <span v-if="props.isTransfer !== null && props.isTransfer !== undefined">
              {{ props.isTransfer ? 'transfer' : 'direct' }}
            </span>
          </div>
        </div>

        <Button
          icon="pi pi-download"
          label="CSV"
          severity="secondary"
          size="small"
          :loading="exporting"
          :disabled="loading || trips.length === 0"
          @click="exportToCSV"
          class="shrink-0"
        />
      </div>
    </template>

    <div v-if="loading" class="flex flex-col gap-4">
      <div class="grid grid-cols-3 gap-3">
        <Skeleton height="80px" v-for="n in 3" :key="n" />
      </div>
      <Skeleton height="210px" />
      <Skeleton height="260px" />
    </div>

    <div v-else class="flex flex-col gap-5 pb-2">
      <div class="grid grid-cols-3 gap-3">

        <div class="rounded-xl border border-surface p-4 text-center">
          <div class="text-xs font-semibold text-surface-400 uppercase tracking-wide mb-1">Min</div>
          <div class="text-2xl font-bold text-blue-500">
            {{ formatPrice(stats.min, currency) }}
          </div>
        </div>

        <div class="rounded-xl border border-surface p-4 text-center">
          <div class="text-xs font-semibold text-surface-400 uppercase tracking-wide mb-1">Median</div>
          <div class="text-2xl font-bold text-orange-400">
            {{ formatPrice(stats.median, currency) }}
          </div>
        </div>

        <div class="rounded-xl border border-surface p-4 text-center">
          <div class="text-xs font-semibold text-surface-400 uppercase tracking-wide mb-1">Max</div>
          <div class="text-2xl font-bold text-red-500">
            {{ formatPrice(stats.max, currency) }}
          </div>
        </div>

      </div>

      <div class="rounded-xl border border-surface p-4" v-if="chartData">

        <!-- Toolbar -->
        <div class="flex items-center justify-between mb-3">
          <div class="flex items-center gap-4 text-sm">
            <span class="font-semibold">📊 Price of places</span>
            <!-- Color legend -->
            <span class="flex items-center gap-1 text-xs text-surface-400">
              <span class="w-2.5 h-2.5 rounded-full bg-blue-500 inline-block"></span> min
            </span>
            <span class="flex items-center gap-1 text-xs text-surface-400">
              <span class="w-2.5 h-2.5 rounded-full bg-orange-400 inline-block"></span> other
            </span>
            <span class="flex items-center gap-1 text-xs text-surface-400">
              <span class="w-2.5 h-2.5 rounded-full bg-red-500 inline-block"></span> max
            </span>
          </div>

          <SelectButton
            v-model="chartType"
            :options="chartTypeOptions"
            optionLabel="label"
            optionValue="value"
            :allowEmpty="false"
            size="small"
          />
        </div>

        <div style="height: 200px">
          <Chart :type="chartType" :data="chartData" :options="chartOptions" />
        </div>
      </div>

      <div v-else class="rounded-xl border border-surface p-4 text-center text-surface-400 text-sm italic">
        Not enough data for the graph
      </div>

      <div>
        <div class="font-semibold mb-2 text-sm">
          🚌 Segments
          <span class="text-surface-400 font-normal ml-1">({{ tripsData.total_segments_count }})</span>
        </div>

        <DataTable
          v-if="trips.length"
          :value="trips"
          scrollable
          scrollHeight="38vh"
          :rowClass="(row) =>
            row.price === stats.min ? 'trip-min' :
            row.price === stats.max ? 'trip-max' : ''"
        >

          <Column header="Departure" sortable sortField="departure_time" style="min-width:90px">
            <template #body="{ data }">
              <div class="leading-tight">
                <div class="text-xs text-surface-400">{{ fmt(data.departure_date, data.departure_time).date }}</div>
                <strong>{{ fmt(data.departure_date, data.departure_time).time }}</strong>
              </div>
            </template>
          </Column>

          <Column header="Arrival" sortable sortField="arrival_time" style="min-width:90px">
            <template #body="{ data }">
              <div class="leading-tight">
                <div class="text-xs text-surface-400">{{ fmt(data.arrival_date, data.arrival_time).date }}</div>
                <strong>{{ fmt(data.arrival_date, data.arrival_time).time }}</strong>
              </div>
            </template>
          </Column>

          <Column header="Duration" style="min-width:65px">
            <template #body="{ data }">
              <span class="text-xs text-surface-400">{{ data.duration?.slice(0,5) ?? '—' }}</span>
            </template>
          </Column>

          <Column field="from_station" header="From station" style="min-width:150px">
            <template #body="{ data }">
              <span class="text-xs">{{ data.from_station }}</span>
            </template>
          </Column>

          <Column field="to_station" header="To station" style="min-width:150px">
            <template #body="{ data }">
              <span class="text-xs">{{ data.to_station }}</span>
            </template>
          </Column>

          <Column field="carrier_name" header="Carrier" style="min-width:120px">
            <template #body="{ data }">
              <span class="text-sm font-medium">{{ data.carrier_name }}</span>
            </template>
          </Column>

          <Column header="Price" sortable sortField="price" style="min-width:110px">
            <template #body="{ data }">
              <span
                class="font-bold text-base whitespace-nowrap"
                :class="{
                  'text-blue-500':   data.price === stats.min,
                  'text-red-500':    data.price === stats.max,
                  'text-orange-400': data.price !== stats.min && data.price !== stats.max
                }"
              >
                {{ formatPrice(data.price, currencySymbol(data.currency)) }}
              </span>
            </template>
          </Column>

          <Column header="Type" style="min-width:75px">
            <template #body="{ data }">
              <span v-if="data.is_transfer" class="text-xs text-orange-400">Transfer</span>
              <span v-else class="text-xs text-green-400">Direct</span>
            </template>
          </Column>

          <Column header="Places" sortable sortField="available_seats" style="min-width:65px">
            <template #body="{ data }">
              <span class="text-sm">{{ data.available_seats ?? '—' }}</span>
            </template>
          </Column>

          <Column header="Actualized" style="min-width:90px">
            <template #body="{ data }">
              <span class="text-xs text-surface-400">
                {{ formatDate(data.price_updated_at, { showSeconds: false, showYear: false }) }}
              </span>
            </template>
          </Column>

        </DataTable>

        <div v-else class="text-surface-400 italic text-sm text-center py-8">
          No data
        </div>
      </div>

    </div>
  </Dialog>
</template>

<style scoped>
:deep(.trip-min) td { background: rgba(59, 130, 246, 0.06) !important; }
:deep(.trip-max) td { background: rgba(239, 68, 68, 0.06)  !important; }
</style>