🚀 Quick Setup (5 minutes)

Step 1: Download Project

bash

    # Clone repository
    git clone https://github.com/MaxMayer1991/python-projects.git
    
    # Navigate to the project folder
    cd python-projects/PythonScraping/carscraper

OR download ZIP file:

    Go to https://github.com/MaxMayer1991/python-projects/tree/main/PythonScraping/carscraper

    Click the green "Code" button → Download ZIP

    Extract and navigate to the carscraper folder

Step 2: Run Docker Containers

bash

    # Start all services (PostgreSQL + Scrapy + Scheduler)
    docker-compose up --build -d
    
    # Check that containers are running
    docker-compose ps

Expected output:
    
    text
    SERVICE              STATUS                 PORTS                                       NAMES              
    autoria_postgres     Up (healthy)           0.0.0.0:5432->5432/tcp                      autoria_postgres   
    autoria_pgadmin      Up                     0.0.0.0:8080->8080/tcp                      autoria_pgadmin    
    autoria_scrapy       Up                     0.0.0.0:2222->22/tcp, [::]:2222->22/tcp     autoria_scrapy     

Step 3: Run Scraper

bash

    # One-time test run
    docker compose exec scrapy_app bash -c "RUN_SPIDER_NOW=true python3 scheduler.py"

Step 4: Check Results

bash

    # View data in PostgreSQL
    docker compose exec postgres psql -U postgres -d cars_data -c "SELECT COUNT(*) FROM car_products;"
    
    # View CSV files
    docker compose exec scrapy_app ls /app/data/
    
    # View logs
    docker compose exec scrapy_app ls /app/logs/

📊 Data Viewing via Web Interface
Launch PgAdmin

bash
    
    # Start PgAdmin web interface
    docker-compose --profile admin up -d pgadmin

Database Connection

    Open http://localhost:8080 in your browser

    Login with credentials:

        Email: your_email

        Password: your_password

    Add database server:

        Host: postgres

        Port: 5432

        Database: cars_data

        Username: postgres

        Password: your_password

⏰ Automatic Mode

The scraper runs on schedule according to settings in the .env file:

text

    SPIDER_TIME=12:00    # Daily spider run at 12:00
    DUMP_TIME=13:00      # Database dump creation at 13:00

Changing Schedule

    Edit the .env file

    Restart containers:

bash
    
    docker-compose down && docker-compose up -d

📁 Data Structure
PostgreSQL Table: car_products

    sql
    CREATE TABLE car_products (
        id SERIAL PRIMARY KEY,
        url TEXT UNIQUE NOT NULL,     -- Advertisement link
        title TEXT,                   -- Car title
        price_usd INTEGER,            -- Price in USD
        odometer INTEGER,             -- Mileage in km
        username TEXT,                -- Seller name
        phone_number BIGINT[],        -- Phone numbers (array)
        image_url TEXT[],             -- Image URLs (array)
        image_count INTEGER,          -- Photo count
        car_number TEXT,              -- License plate
        car_vin TEXT,                 -- VIN code
        datetime_found TIMESTAMP,     -- Discovery time
        updated_at TIMESTAMP          -- Update time
    );

CSV Files

    Exported to the data/ folder with names like cars_20250828_120000.csv
    🔧 Additional Commands
    Monitoring

bash

    # Real-time logs for scheduler and scrapy
    docker-compose logs -f scrapy_app
    
    # Status of all containers
    docker-compose ps
    
    # Resource usage
    docker stats

Manual Control

bash

    # Run spider without scheduler
    docker compose exec scrapy_app scrapy crawl carspider
    
    # Create database dump
    docker compose exec postgres pg_dump -U postgres cars_data > backup_$(date +%Y%m%d).sql
    
    # Clear table
    docker compose exec postgres psql -U postgres -d cars_data -c "TRUNCATE car_products;"

Stopping and Cleanup

bash

    # Stop all containers
    docker-compose down
    
    # Complete cleanup (WARNING: database data loss!)
    docker-compose down -v

🐛 Troubleshooting
Problem: Containers won't start

Solution:

bash

    # Clean and rebuild
    docker-compose down -v
    docker-compose build --no-cache
    docker-compose up -d

Problem: "Port 5432 is already in use"

Solution: Change port in docker-compose.yml:

text
    postgres:
      ports:
        - "5433:5432"  # Use port 5433 instead of 5432

Problem: Scrapy finds no data

Solution: Check logs:

bash

    docker compose exec scrapy_app tail -f /app/logs/spider_*.log

Problem: Database empty after scraping

Solution: Check connection:

bash

    docker compose exec scrapy_app python3 -c "
    import psycopg2, os
    conn = psycopg2.connect(os.getenv('DATABASE_URL'))
    print('✅ Database connected')
    "

📋 System Requirements

    Docker Desktop or Docker Engine + Docker Compose

    Minimum 2GB RAM (for Chrome and PostgreSQL)

    1GB free disk space

    Internet connection for scraping

🔒 Security Configuration

The .env file contains demonstration passwords. For production use:

    Change passwords in .env:

text
    
    POSTGRES_PASSWORD=your_secure_password
    PGADMIN_PASSWORD=your_admin_password

    Add .env to .gitignore if planning a public repository

📞 Support

If you encounter issues:

    Check logs: docker-compose logs scrapy_app

    Check status: docker-compose ps

    Create Issue on GitHub: https://github.com/MaxMayer1991/python-projects/issues

👤 Author

Maksym Plakushko

    GitHub: @MaxMayer1991

    Email: mplakushko@gmail.com

📄 License

MIT License - see LICENSE file for details
🔍 Project Architecture

This project implements a hybrid web scraping architecture combining:

    Scrapy Framework - High-performance asynchronous web crawling

    Selenium WebDriver - Dynamic JavaScript content extraction

    PostgreSQL Database - Reliable data storage with UPSERT operations

    Docker Containerization - Consistent deployment across environments

    APScheduler - Automated task scheduling

    Anti-detection Mechanisms - User-agent rotation, proxy support, request throttling

The system is designed for production-ready deployment with comprehensive error handling, logging, and data validation capabilities.