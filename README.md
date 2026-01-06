# Autoria.ua Car Scraper

A Scrapy-based web scraper for extracting car listings from autoria.ua with data storage in PostgreSQL and monitoring via pgAdmin.

## 🚀 Features

- Scrapes car listings from autoria.ua
- Stores data in PostgreSQL
- Web interface via pgAdmin
- Scheduled scraping
- Logging to `/app/logs`

## 🛠 Prerequisites

- Docker
- Docker Compose
- Python 3.13
- Minimum 2GB RAM (for Scrapy and PostgreSQL)
- 3 GB free disk space
- Internet connection for scraping
- Own proxy provider
## 🚀 Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/MaxMayer1991/scraper_autoria
   cd scraper_autoria
   ```
2. **Set up environment variables Create a .env file**
    ```bash
    cp .env.example .env
    Edit the .env file with your credentials.
    ```
3. **Build and start containers**
    ```bash
    # Start all services (PostgreSQL + PGAdmin + Scheduler)
    docker-compose up --build -d
    ```
## 🐳 Running the Scraper

Option 1: **Run via Docker Compose**
   ```bash
   # Start all services
   docker compose up -d
   # Run the scraper manually
   docker compose exec scrapy_app python3 scheduler.py
   # Or with environment variable
   docker compose exec -e RUN_SPIDER_NOW=true scrapy_app python3 scheduler.py
   ```
Option 2: **Access the container and run**
   ```bash
   # Access the container
   docker compose exec scrapy_app bash
   # Inside container
   python3 scheduler.py
   # or
   RUN_SPIDER_NOW=true python3 scheduler.py
   ```
## 📊 **Accessing the Database**
**Using psql**
   ```bash
   # One-time test run
   docker compose exec scrapy_app bash -c "RUN_SPIDER_NOW=true python3 scheduler.py"
   ```
**Using pgAdmin**
1. Open http://localhost:5050 in your browser
2. Login with credentials from .env (PGADMIN_EMAIL and PGADMIN_PASSWORD)
3. Add a new server:
   * Name: autoria_db
   * Host: postgres
   * Port: 5432
   * Username: postgres (or from your .env)
   * Password: (from your .env)


## 📂 Project Structure

    scraper_autoria/
    ├── .env.example           # Example environment variables
    ├── docker-compose.yml     # Docker Compose configuration
    ├── Dockerfile             # Scrapy app Dockerfile
    ├── requirements.txt       # Python dependencies
    ├── scheduler.py          # Scrapy scheduler
    └── logs/                 # Logs directory

## 🔍 Viewing Logs

Logs are stored in the container at /app/logs/. To view them:
The scraper runs on schedule according to settings in the .env file:

   ```bash
   # View logs from the host
   docker compose logs -f scrapy_app
   
   # Or access the container and view log files
   docker compose exec scrapy_app bash
   ls -la /app/logs/
   ```


## 🔧 Additional Commands
Monitoring
   ```bash
   # Real-time logs for scheduler
   docker logs -f autoria_scrapy
   # Real-time logs for scrapy
   # List files in the logs directory
   docker exec autoria_scrapy ls -la /app/logs/
   # View log files
   docker exec autoria_scrapy cat /app/logs/spider_*.log
   # Also you can view logs from your local directory scraper_autoria/logs
   
   # Status of all containers
   docker-compose ps 
   # Resource usage
   docker stats
   ```
Manual Control
   ```bash
   # Run spider without scheduler
   docker exec autoria_scrapy scrapy crawl autoria
   # Create database dump
   docker exec autoria_postgres pg_dump -U postgres cars_data > "backup_$(Get-Date -Format 'yyyyMMdd').sql"
   # Clear table
   docker exec autoria_postgres psql -U postgres -d cars_data -c "TRUNCATE car_products;"
  ```
Stopping and Cleanup
   ```bash
   # Stop all containers
   docker-compose down
   # Complete cleanup (WARNING: database data loss!)
   docker-compose down -v
   ```
#### Changing Schedule

edit the .env file
   ```text
   SPIDER_TIME=12:00    # Daily spider run at 12:00
   DUMP_TIME=13:00      # Database dump creation at 13:00
   ```
Restart containers:
   ```bash 
   docker-compose down && docker-compose up -d
   ```
#### Change number of requests per minute

edit the settings.py file
1. 4GB RAM:
```python
PLAYWRIGHT_MAX_CONTEXTS = 2
PLAYWRIGHT_MAX_PAGES_PER_CONTEXT = 2
CONCURRENT_REQUESTS = 8 # up to 16
CONCURRENT_REQUESTS_PER_DOMAIN = 4 # up to 8
```
2. 8GB RAM:
```python
PLAYWRIGHT_MAX_CONTEXTS = 4
PLAYWRIGHT_MAX_PAGES_PER_CONTEXT = 4
CONCURRENT_REQUESTS = 16 # up to 32
CONCURRENT_REQUESTS_PER_DOMAIN = 8 # up to 16
```
3. 16GB+ RAM:
```python
PLAYWRIGHT_MAX_CONTEXTS = 8
PLAYWRIGHT_MAX_PAGES_PER_CONTEXT = 8
CONCURRENT_REQUESTS = 32 # up to 64
CONCURRENT_REQUESTS_PER_DOMAIN = 16 # up to 32
```

## 🛠 Troubleshooting
If PostgreSQL is not starting:
   ```bash
   # Check PostgreSQL logs
   docker logs autoria_postgres
   
   # Check if the volume exists
   docker volume ls --filter name="scraper_autoria_postgres_data"
   
   # Recreate the volume if needed
   docker compose down -v
   docker compose up -d
   ```
If pgAdmin is not accessible:
1. Check if the container is running
   ```bash
   docker ps --filter "name=autoria_pgadmin"
   ```
2. Check logs
   ```bash
   docker logs autoria_pgadmin
   ```
3. Make sure port 5050 is not in use:
   ```bash
   netstat -ano | findstr ":5050 \|:5050$"
   ```


🔒 Security Configuration

The .env file contains demonstration passwords. For production use:

Change passwords and api keys in .env:

text
    
    POSTGRES_PASSWORD=your_secure_password
    PGADMIN_PASSWORD=your_admin_password
    PROXY_URL=your_proxy_url
    SCRAPEOPS_API_KEY=your_scrapeops_api_key # free key from scrapeops.io
    Add .env to .gitignore if planning a public repository
## 👤 Author

**Maksym Plakushko**

GitHub: @MaxMayer1991

Email: mplakushko@gmail.com

## 📝 License
This project is licensed under the MIT License - see the LICENSE file for details.
### Key Points to Note:
1. **Database Access**: The error you're seeing suggests the PostgreSQL service might not be running or accessible. The README includes troubleshooting steps for this.
2. **Running the Scraper**: The correct command to run the scraper is:
   ```bash
   docker compose exec scrapy_app python3 scheduler.py
   ```
Or with the environment variable:
   ```bash
   docker compose exec -e RUN_SPIDER_NOW=true scrapy_app python3 scheduler.py
   ```
3. pgAdmin Access: The README includes instructions for accessing pgAdmin at http://localhost:5050 with the credentials from your .env file.
4. Logs: The README shows how to view logs both from the host and inside the container.