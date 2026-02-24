# Project Structure Documentation

This document provides a comprehensive overview of the transport scraping project's directory structure, database schema, and architecture.

## Root Directory

The root directory contains essential configuration files and directories:

- `.env` — Environment variable configuration file (not included in the repository)
- `.env_example` — Example environment configuration file
- `.gitignore` — Git ignore file to exclude unnecessary files from version control
- `alembic.ini` — Configuration file for Alembic database migrations
- `docker-compose.yml` — Docker Compose configuration for managing services
- `Dockerfile` — Docker configuration file to build the application image
- `main.py` — The entry point of the application
- `pytest.ini` — Configuration file for Pytest testing framework
- `requirements.txt` — The list of Python dependencies for the project
- `README.md` — Project documentation
- `tox.ini` — Configuration file for tox testing environments

## `app/` Directory

The `app/` directory contains the main source code for the application, organized into multiple subdirectories:

### 1. `db/`
Contains database interaction files for different entities:
- CRUD operations for cities, routes, trips, stations
- Database connection utilities and session management
- Migration utilities and database maintenance functions

### 2. `models/`
SQLAlchemy models for database tables:
- `city_model.py` — City information model
- `route_model.py` — Route between cities model
- `trip_model.py` — Trip details model
- `trip_history_model.py` — Historical trip data with pricing
- `station_model.py` — Bus station information model
- `site_model.py` — Website configuration model
- `site_host_model.py` — Website host configurations
- `proxy_server_model.py` — Proxy server configuration model
- `currency_model.py` — Currency exchange rates model
- `parser_stat_model.py` — Parser statistics model
- `base.py` — Base model with timestamp mixins

### 3. `parsers/`
Contains parsing logic for different transportation websites:
- `base_parser.py` — Abstract base classes for all parsers
- Site-specific parsers for various transportation websites
- Browser automation and request-based parsing implementations
- Utility functions for parsing data and handling responses

### 4. `schemas/`
Pydantic models for data validation and serialization:
- Input/output data validation schemas
- API request and response models
- Database entity schemas
- Migration and metrics schemas

### 5. `managers/`
Business logic managers organized by functionality:

#### Browser Management
- `browser/` — Browser automation management for web scraping

#### Elasticsearch Integration
- `elastic/` — Elasticsearch integration for data storage and search
  - `es_manager.py` — Elasticsearch operations
  - `es_migration_manager.py` — Data migration from PostgreSQL to Elasticsearch

#### HTTP Client Management
- `http/` — HTTP request handling and proxy management

#### Monitoring & Metrics
- `monitoring/` — System and application monitoring
  - `metrics.py` — Metrics collection and reporting
  - `system_metrics.py` — System resource monitoring

#### Notification System
- `notification/` — Notification management for alerts and reports
  - `notification_manager.py` — Notification handling
  - `notification_utils.py` — Telegram integration utilities

#### Parser Management
- `parser/` — Parser coordination and management
  - `parser_manager.py` — Main parser orchestration
  - Statistics and metrics utilities

#### Route Processing
- `route/` — Route data processing and management

#### Task Management
- `task/` — Celery task management and scheduling
  - `maintenance_task_manager.py` — Maintenance tasks (city updates, migrations)
  - `parser_task_manager.py` — Parser execution tasks
  - `system_monitoring_manager.py` — System monitoring tasks
  - `service_health_manager.py` — Service health monitoring

### 6. `settings/`
Application configuration and utilities:
- `conf.py` — Database connection settings and application configuration
- `constants.py` — Environment variables and settings using Pydantic
- `logger.py` — Logging configuration with Loguru
- `exceptions.py` — Custom exception definitions

### 7. `utils/`
Utility functions and helper classes:
- City name normalization and matching utilities
- Data processing helpers
- Common utility functions used across the application

### 8. `tasks/`
Celery task definitions:
- Background job scheduling with APScheduler
- Periodic parsing tasks
- Data maintenance and cleanup tasks
- System monitoring tasks

---

## `tests/` Directory

The `tests/` directory contains all test files for the project, ensuring application functionality and reliability.

## `logs/` Directory

Runtime logs directory (auto-created):
- Application logs with rotation and compression
- Site-specific parsing logs
- Error and debug information

## Example of Directory Structure:

```text
scraper/
│
├── app/
│   ├── db/
│   │   ├── city_db.py
│   │   ├── route_db.py
│   │   ├── trip_db.py
│   │   ├── trip_history_db.py
│   │   └── ...
│   ├── models/
│   │   ├── city_model.py
│   │   ├── route_model.py
│   │   ├── trip_model.py
│   │   ├── trip_history_model.py
│   │   ├── site_model.py
│   │   ├── site_host_model.py
│   │   └── ...
│   ├── parsers/
│   │   ├── base_parser.py
│   │   ├── site_parsers/
│   │   └── utils/
│   ├── schemas/
│   │   ├── city_schema.py
│   │   ├── trip_schema.py
│   │   ├── elasticsearch_schemas.py
│   │   └── ...
│   ├── managers/
│   │   ├── browser/
│   │   ├── elastic/
│   │   ├── http/
│   │   ├── monitoring/
│   │   ├── notification/
│   │   ├── parser/
│   │   ├── route/
│   │   └── task/
│   ├── settings/
│   │   ├── conf.py
│   │   ├── constants.py
│   │   ├── logger.py
│   │   └── exceptions.py
│   ├── tasks/
│   └── utils/
│
├── tests/
├── logs/
│
├── .env_example
├── .gitignore
├── alembic.ini
├── docker-compose.yml
├── Dockerfile
├── main.py
├── pytest.ini
├── requirements.txt
├── tox.ini
└── README.md
```

---

# Database Schema Documentation

The database schema consists of several interconnected tables designed to store comprehensive transportation data.

## Core Tables

### 1. **CityModel** (`cities`)
Stores city information from various transportation APIs.

| Field        | Type     | Description                                    |
|--------------|----------|------------------------------------------------|
| `id`         | Integer  | Primary key, unique identifier                 |
| `like_bus_id`| Integer  | LikeBus API city identifier                    |
| `name_ru`    | String   | City name in Russian                           |
| `name_ua`    | String   | City name in Ukrainian                         |
| `name_en`    | String   | City name in English                           |
| `infobus_id` | Integer  | Infobus API city identifier (optional)         |
| `ukrpas_id`  | Integer  | Ukrpas API city identifier (optional)          |

### 2. **StationModel** (`stations`)
Bus station information linked to cities.

| Field        | Type     | Description                                    |
|--------------|----------|------------------------------------------------|
| `id`         | Integer  | Primary key, unique identifier                 |
| `city_id`    | Integer  | Foreign key to cities.id                       |
| `like_bus_id`| Integer  | LikeBus API station identifier                 |
| `name_ru`    | String   | Station name in Russian                        |
| `name_ua`    | String   | Station name in Ukrainian                      |
| `name_en`    | String   | Station name in English                        |

### 3. **RouteModel** (`routes`)
Routes between cities with parsing metadata.

| Field           | Type     | Description                                    |
|-----------------|----------|------------------------------------------------|
| `id`            | Integer  | Primary key, unique identifier                 |
| `from_city_id`  | Integer  | Foreign key to departure city                  |
| `to_city_id`    | Integer  | Foreign key to destination city                |
| `departure_date`| Date     | Route departure date                           |
| `site_id`       | Integer  | Foreign key to source website                  |
| `parsed_at`     | DateTime | Timestamp of data parsing                      |

### 4. **TripModel** (`trips`)
Individual trip details for each route.

| Field           | Type      | Description                                   |
|-----------------|-----------|-----------------------------------------------|
| `id`            | Integer   | Primary key, unique identifier                |
| `route_id`      | Integer   | Foreign key to routes.id                      |
| `from_station`  | String    | Departure station name (optional)             |
| `to_station`    | String    | Arrival station name (optional)               |
| `departure_time`| Time      | Trip departure time                           |
| `arrival_time`  | Time      | Trip arrival time (optional)                  |
| `arrival_date`  | Date      | Trip arrival date (optional)                  |
| `carrier_name`  | String    | Transportation carrier name                   |
| `duration`      | Interval  | Trip duration (optional)                      |
| `is_transfer`   | Boolean   | Indicates if trip requires transfers          |

### 5. **TripHistoryModel** (`trip_history`)
Historical pricing and availability data for trips.

| Field            | Type     | Description                                   |
|------------------|----------|-----------------------------------------------|
| `id`             | Integer  | Primary key, unique identifier                |
| `trip_id`        | Integer  | Foreign key to trips.id                       |
| `price`          | Numeric  | Trip price                                    |
| `currency`       | String   | Price currency code                           |
| `available_seats`| Integer  | Number of available seats (optional)          |
| `created_at`     | DateTime | Record creation timestamp                     |

## Configuration Tables

### 6. **SiteModel** (`sites`)
Website configuration for data sources.

| Field         | Type      | Description                                   |
|---------------|-----------|-----------------------------------------------|
| `id`          | Integer   | Primary key, unique identifier                |
| `name`        | String    | Website name                                  |
| `url`         | String    | Website URL                                   |
| `last_parsed` | DateTime  | Last successful parsing timestamp             |
| `is_active`   | Boolean   | Site parsing status                           |
| `api_key`     | String    | API authentication key (optional)            |
| `is_aggregator`| Boolean  | Indicates if site is an aggregator            |

### 7. **SiteHostModel** (`site_hosts`)
Additional host configurations for websites.

| Field      | Type    | Description                                     |
|------------|---------|------------------------------------------------|
| `id`       | Integer | Primary key, unique identifier                 |
| `site_id`  | Integer | Foreign key to sites.id                        |
| `host_url` | String  | Alternative host URL                           |
| `api_key`  | String  | Host-specific API key (optional)               |

### 8. **ProxyServerModel** (`proxy_servers`)
Proxy server configurations for web scraping.

| Field       | Type      | Description                                   |
|-------------|-----------|-----------------------------------------------|
| `id`        | Integer   | Primary key, unique identifier                |
| `ip_address`| String    | Proxy server IP address                       |
| `port`      | Integer   | Proxy server port                             |
| `username`  | String    | Proxy authentication username (optional)      |
| `password`  | String    | Proxy authentication password (optional)      |
| `is_active` | Boolean   | Proxy availability status                     |
| `last_used` | DateTime  | Last usage timestamp                          |

## Utility Tables

### 9. **CurrencyModel** (`currencies`)
Exchange rate information for price conversions.

| Field        | Type     | Description                                    |
|--------------|----------|------------------------------------------------|
| `id`         | Integer  | Primary key, unique identifier                 |
| `code`       | String   | Currency code (e.g., 'USD', 'EUR')            |
| `rate`       | Numeric  | Exchange rate relative to base currency       |
| `updated_at` | DateTime | Last rate update timestamp                     |

### 10. **ParserStatModel** (`parser_stats`)
Parser performance and statistics tracking.

| Field              | Type     | Description                                |
|--------------------|----------|--------------------------------------------|
| `id`               | Integer  | Primary key, unique identifier             |
| `site_id`          | Integer  | Foreign key to sites.id                    |
| `routes_processed` | Integer  | Number of routes processed                 |
| `successful_routes`| Integer  | Number of successfully parsed routes       |
| `error_routes`     | Integer  | Number of routes with parsing errors       |
| `execution_time`   | Interval | Parser execution duration                  |
| `created_at`       | DateTime | Statistics record timestamp                |

---

# Architecture Overview

## Key Components

### **Data Pipeline**
1. **Parsing Layer** — Extracts data from transportation websites
2. **Processing Layer** — Validates and normalizes collected data  
3. **Storage Layer** — PostgreSQL for operational data, Elasticsearch for search
4. **Monitoring Layer** — Tracks system performance and data quality

### **Task Management**
- **Celery** with Redis for distributed task processing
- **APScheduler** for periodic data collection
- **Queue Management** with priority-based task routing

### **Monitoring & Alerting**
- **Prometheus Metrics** for performance monitoring
- **System Resource Tracking** (CPU, Memory, Disk usage)
- **Telegram Notifications** for alerts and reports
- **Health Checks** for service availability

### **Data Storage**
- **PostgreSQL** — Primary database for structured data
- **Elasticsearch** — Search and analytics for large datasets
- **Redis** — Caching and task queue backend

This architecture provides a robust, scalable solution for collecting, processing, and analyzing transportation data from multiple sources while maintaining data quality and system reliability.