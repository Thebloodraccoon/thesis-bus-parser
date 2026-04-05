import { ref } from 'vue';
import apiClient from '@/api/axios';

export function useExport({
  selectedDate,
  fromCityIds,
  toCityIds,
  departureTimeFrom,
  departureTimeTo,
  arrivalTimeFrom,
  arrivalTimeTo,
  isTransfer,
  selectedSites,
}) {
  const exporting = ref(false);

  /**
   * Форматирует Date → 'YYYY-MM-DD'
   */
  function formatDate(d) {
    if (!d) return '';
    const dt = d instanceof Date ? d : new Date(d);
    return dt.toLocaleDateString('sv-SE'); // sv-SE всегда даёт YYYY-MM-DD
  }

  async function exportToCSV() {
    exporting.value = true;
    try {
      const params = new URLSearchParams();

      params.set('departure_date', formatDate(selectedDate.value));

      (fromCityIds.value || []).forEach((id) => params.append('from_city_ids', id));
      (toCityIds.value || []).forEach((id) => params.append('to_city_ids', id));

      if (departureTimeFrom.value && departureTimeFrom.value !== '00:00')
        params.set('departure_time_from', departureTimeFrom.value);
      if (departureTimeTo.value && departureTimeTo.value !== '23:59')
        params.set('departure_time_to', departureTimeTo.value);
      if (arrivalTimeFrom.value && arrivalTimeFrom.value !== '00:00')
        params.set('arrival_time_from', arrivalTimeFrom.value);
      if (arrivalTimeTo.value && arrivalTimeTo.value !== '23:59')
        params.set('arrival_time_to', arrivalTimeTo.value);
      if (isTransfer.value !== null && isTransfer.value !== undefined)
        params.set('is_transfer', isTransfer.value);
      (selectedSites.value || []).forEach((id) => params.append('sites', id));

      const response = await apiClient.get(`/routes/export?${params.toString()}`, {
        responseType: 'blob',
      });

      // Определяем имя файла из заголовка или генерируем сами
      const disposition = response.headers['content-disposition'] || '';
      const match = disposition.match(/filename="?([^"]+)"?/);
      const filename = match ? match[1] : `routes_${formatDate(selectedDate.value)}.csv`;

      // Скачиваем файл
      const url = URL.createObjectURL(new Blob([response.data], { type: 'text/csv' }));
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Export failed:', err);
    } finally {
      exporting.value = false;
    }
  }

  return { exportToCSV, exporting };
}