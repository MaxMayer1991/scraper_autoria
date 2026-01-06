import os
import sys
import subprocess
from datetime import datetime
from apscheduler.schedulers.blocking import BlockingScheduler
from dotenv import load_dotenv
load_dotenv()


# Визначаємо шляхи
if os.path.exists('/.dockerenv') or os.getenv('DOCKER_ENV') == 'true':
    BASE_DIR = '/app'
else:
    BASE_DIR = os.getcwd()

# Налаштування
SPIDER_TIME = os.getenv('SPIDER_TIME')
DUMP_TIME = os.getenv('DUMP_TIME')
DUMP_DIR = os.path.join(BASE_DIR, 'dumps')
LOG_DIR = os.path.join(BASE_DIR, 'logs')
# Створюємо папку для дампів, якщо немає
os.makedirs(DUMP_DIR, exist_ok=True)


def run_spider():
    """Запуск Scrapy павука"""

    print(f"[{datetime.now()}] 🕷️ Launching Scrapy spider...")
    # Використовуємо subprocess, щоб Scrapy запускався в окремому процесі
    # Це уникає помилки 'ReactorNotRestartable'
    original_dir = os.getcwd()
    try:
        os.chdir(LOG_DIR)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_file = f"{LOG_DIR}/spider_{timestamp}.log"
        cmd = [sys.executable, '-m', 'scrapy', 'crawl', 'autoria',
               '-s','LOG_LEVEL=INFO', '-s', f'LOG_FILE={log_file}']
        subprocess.run(cmd, check=True, capture_output=True, text=True)
    except Exception as e:
        print(f"❌ Error spider: {e}")
    finally:
        os.chdir(original_dir)


def dump_db():
    """Створення бекапу бази даних PostgreSQL"""
    print(f"[{datetime.now()}] 💾 Creating database dump...")

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"dump_{timestamp}.sql"
    filepath = os.path.join(DUMP_DIR, filename)

    # Отримуємо дані з ENV
    db_host = os.getenv('POSTGRES_HOST', 'postgres')
    db_user = os.getenv('POSTGRES_USER', 'postgres')
    db_name = os.getenv('POSTGRES_DB', 'cars_data')
    db_password = os.getenv('POSTGRES_PASSWORD')

    # Формуємо команду pg_dump (вона має бути встановлена в Dockerfile)
    # PGPASSWORD передаємо як змінну оточення перед командою
    env = os.environ.copy()
    env['PGPASSWORD'] = db_password

    cmd = [
        'pg_dump',
        '-h', db_host,
        '-U', db_user,
        '-d', db_name,
        '-f', filepath
    ]

    try:
        subprocess.run(cmd, env=env, check=True)
        print(f"✅ Dump saved to: {filepath}")
    except subprocess.CalledProcessError as e:
        print(f"❌ Dump failed: {e}")


def main():
    scheduler = BlockingScheduler()

    # Розбиваємо час HH:MM
    s_hour, s_minute = SPIDER_TIME.split(':')
    d_hour, d_minute = DUMP_TIME.split(':')

    # Додаємо задачі
    scheduler.add_job(run_spider, 'cron', hour=s_hour, minute=s_minute)
    scheduler.add_job(dump_db, 'cron', hour=d_hour, minute=d_minute)

    print(f"⏰ Scheduler started. Spider at {SPIDER_TIME}, Dump at {DUMP_TIME}")

    # Якщо треба запустити одразу (для тесту)
    if os.getenv('RUN_SPIDER_NOW', 'false').lower() == 'true':
        run_spider()

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        pass


if __name__ == '__main__':
    main()