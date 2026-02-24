# Система мониторинга LikeBus EMS DPS

## Обзор

Данная система мониторинга включает в себя:
- **Prometheus** - сбор и хранение метрик
- **Grafana** - визуализация метрик и логов
- **Loki** - сбор и хранение логов
- **Promtail** - агент для сбора логов из контейнеров
- **Pushgateway** - промежуточное хранилище для метрик

## Запуск системы мониторинга

### 1. Запуск всех сервисов мониторинга
```bash
docker-compose up -d pushgateway prometheus grafana loki promtail
```

### 2. Проверка доступности сервисов

После запуска проверьте доступность следующих сервисов:

- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000 (admin/admin123)
- **Pushgateway**: http://localhost:9091
- **Loki**: http://localhost:3100

### 3. Настройка Grafana

1. Откройте Grafana (http://localhost:3000)
2. Войдите с учетными данными:
   - Логин: `admin`
   - Пароль: `admin123`
3. Источники данных уже настроены автоматически:
   - Prometheus: http://prometheus:9090
   - Loki: http://loki:3100

## Интеграция с парсерами

### Настройка парсер репозитория

В `.env` файле парсер репозитория добавьте:

```env
PUSHGATEWAY_URL=http://localhost:9091
```

### Отправка метрик из парсеров

Парсеры должны отправлять метрики в Pushgateway. Основные метрики:

- `parser_progress_current` - текущее количество обработанных маршрутов
- `parser_progress_total` - общее количество маршрутов для обработки
- `parser_progress_percentage` - процент выполнения (0-100)
- `parser_likebus_found` - количество найденных LikeBus маршрутов
- `parser_likebus_not_found` - количество ненайденных LikeBus маршрутов
- `parser_requests_sent` - количество отправленных запросов

## Структура файлов

```
monitoring/
├── prometheus.yml              # Конфигурация Prometheus
├── loki-config.yaml           # Конфигурация Loki
├── promtail-config.yaml       # Конфигурация Promtail
├── grafana/
│   ├── provisioning/
│   │   ├── datasources/
│   │   │   └── datasources.yml    # Источники данных Grafana
│   │   └── dashboards/
│   │       └── dashboards.yml     # Конфигурация дашбордов
│   └── dashboards/
│       └── scraper-parser-dashboard.json # Дашборд для отслеживания прогресса парсеров
└── README.md
```

## Полезные команды

### Просмотр логов сервисов
```bash
# Логи Prometheus
docker-compose logs prometheus

# Логи Grafana
docker-compose logs grafana

# Логи Loki
docker-compose logs loki

# Логи Promtail
docker-compose logs promtail
```

### Остановка сервисов мониторинга
```bash
docker-compose stop pushgateway prometheus grafana loki promtail
```

### Перезапуск сервисов мониторинга
```bash
docker-compose restart pushgateway prometheus grafana loki promtail
```

## Мониторинг существующих сервисов

Система настроена для мониторинга:
- PostgreSQL (db, test_db)
- Elasticsearch
- Kibana
- PgAdmin

## Troubleshooting

### Prometheus не собирает метрики
1. Проверьте конфигурацию в `monitoring/prometheus.yml`
2. Убедитесь, что сервисы доступны по указанным адресам
3. Проверьте логи: `docker-compose logs prometheus`

### Grafana не подключается к источникам данных
1. Проверьте, что Prometheus и Loki запущены
2. Убедитесь, что сеть `infra_network` настроена правильно
3. Проверьте конфигурацию в `monitoring/grafana/provisioning/datasources/datasources.yml`

### Loki не собирает логи
1. Проверьте конфигурацию Promtail
2. Убедитесь, что Promtail имеет доступ к Docker socket
3. Проверьте логи: `docker-compose logs promtail` 