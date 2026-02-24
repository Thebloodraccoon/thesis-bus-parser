# 📊 Дашборды Grafana для мониторинга парсеров

## Обзор

В этой директории находятся дашборды Grafana для мониторинга системы парсеров. Дашборды автоматически загружаются при запуске Grafana.

## 🎯 Доступные дашборды

### 1. Мониторинг парсеров (`parser-monitoring-dashboard.json`)
**UID:** `parser-monitoring`

Основной дашборд для мониторинга работы парсеров в реальном времени.

**Панели:**
- Обработанные маршруты по парсерам
- Успешно обработанные маршруты
- Ошибочные маршруты
- Найденные в LikeBus
- Не найденные в LikeBus
- Размер ответов (байты)
- Процент успешных маршрутов
- Среднее время выполнения (5м)
- Статус активности парсеров
- Количество активных парсеров

**Обновление:** каждые 5 секунд
**Временной диапазон:** последний час

### 2. Аналитика парсеров (`parser-analytics-dashboard.json`)
**UID:** `parser-analytics`

Дашборд для детальной аналитики и трендов парсеров.

**Панели:**
- Общее количество обработанных маршрутов (за час)
- Успешно обработанные маршруты (за час)
- Ошибочные маршруты (за час)
- Найденные в LikeBus (за час)
- 95-й процентиль времени выполнения
- 95-й процентиль размера ответов (байты)
- Скорость обработки маршрутов (запросов/сек)
- Процент найденных в LikeBus (за час)

**Обновление:** каждые 30 секунд
**Временной диапазон:** последние 6 часов

## 🚀 Доступ к дашбордам

1. Откройте Grafana: http://localhost:3000
2. Логин: `admin`
3. Пароль: `admin123`
4. Перейдите в раздел "Dashboards"
5. Найдите дашборды по названию или UID

## 📈 Метрики

### Детальные метрики в реальном времени
```promql
# Текущий прогресс
parser_detailed_routes_processed{parser_name="infobus"}

# Успешность
parser_detailed_successful_routes{parser_name="infobus"}
parser_detailed_error_routes{parser_name="infobus"}

# LikeBus интеграция
parser_detailed_likebus_found{parser_name="infobus"}
parser_detailed_likebus_not_found{parser_name="infobus"}

# Производительность
parser_response_size_kb{parser_name="infobus"}
parser_is_active{parser_name="infobus"}
```

### Метрики завершения парсера
```promql
# Накопительные счетчики
parser_completion_total_routes{parser_name="infobus"}
parser_completion_successful_routes{parser_name="infobus"}
parser_completion_error_routes{parser_name="infobus"}

# Время выполнения
parser_completion_duration_seconds{parser_name="infobus"}
```

## 🔔 Алерты

Настроены следующие алерты в Prometheus:

1. **HighParserErrorRate** - высокий процент ошибок (>10%)
2. **ParserTimeout** - превышение времени выполнения (>1 часа)
3. **ParserInactive** - неактивность парсера (>10 минут)
4. **LowLikeBusFoundRate** - низкий процент найденных в LikeBus (<30%)
5. **HighResponseSize** - большой размер ответов (>1000KB)
6. **LowProcessingRate** - низкая скорость обработки (<0.1 req/s)
7. **High95thPercentileDuration** - высокий 95-й процентиль времени (>5 минут)
8. **ParserMetricsMissing** - отсутствие метрик парсеров

## 🛠️ Настройка

### Добавление нового дашборда

1. Создайте JSON файл дашборда в директории `dashboards/`
2. Убедитесь, что файл имеет правильную структуру JSON
3. Перезапустите контейнер Grafana:
   ```bash
   docker-compose restart grafana
   ```

### Изменение существующего дашборда

1. Отредактируйте JSON файл дашборда
2. Перезапустите контейнер Grafana
3. Или используйте UI Grafana для редактирования

### Настройка алертов

1. Отредактируйте файл `../prometheus/alerts/parser-alerts.yml`
2. Перезапустите контейнер Prometheus:
   ```bash
   docker-compose restart prometheus
   ```

## 📊 Полезные запросы PromQL

### Процент успешных маршрутов
```promql
(parser_detailed_successful_routes / parser_detailed_routes_processed) * 100
```

### Скорость обработки
```promql
rate(parser_completion_total_routes[5m])
```

### Среднее время выполнения
```promql
rate(parser_completion_duration_seconds_sum[5m]) / rate(parser_completion_duration_seconds_count[5m])
```

### Активные парсеры
```promql
sum(parser_is_active) by (parser_name)
```

## 🔧 Устранение неполадок

### Дашборд не загружается
1. Проверьте синтаксис JSON файла
2. Убедитесь, что файл находится в правильной директории
3. Проверьте логи Grafana: `docker-compose logs grafana`

### Метрики не отображаются
1. Проверьте, что Prometheus собирает метрики
2. Убедитесь, что Pushgateway работает
3. Проверьте конфигурацию источника данных в Grafana

### Алерты не срабатывают
1. Проверьте конфигурацию алертов в Prometheus
2. Убедитесь, что файл алертов подключен
3. Проверьте логи Prometheus: `docker-compose logs prometheus`

## 📝 Логи

Полезные команды для просмотра логов:

```bash
# Логи Grafana
docker-compose logs grafana

# Логи Prometheus
docker-compose logs prometheus

# Логи Pushgateway
docker-compose logs pushgateway
```

## 🎯 Рекомендации

1. **Регулярно проверяйте** дашборды для мониторинга здоровья системы
2. **Настройте уведомления** для критических алертов
3. **Анализируйте тренды** с помощью аналитического дашборда
4. **Оптимизируйте производительность** на основе метрик времени выполнения
5. **Мониторьте качество данных** через процент найденных в LikeBus 