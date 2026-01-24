import subprocess
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import List, Optional
from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI, HTTPException, BackgroundTasks
from scheduler import run_spider, dump_db
from fastapi.responses import  Response
import uvicorn, os, sys
from dotenv import load_dotenv
from pathlib import Path
import aiofiles
from urllib.parse import urlparse
# Create logs directory if it doesn't exist
logs_dir = Path("logs")
logs_dir.mkdir(exist_ok=True)

load_dotenv()
# --- Глобальні змінні ---
spider_process = None
scheduler = None
app = FastAPI()
def get_db_connection():
    return psycopg2.connect(os.getenv("DATABASE_URL"))

def start_scheduler():
    global scheduler
    if scheduler and scheduler.running:
        return "Scheduler is already running"
    scheduler = BackgroundScheduler()
    SPIDER_TIME = os.getenv('SPIDER_TIME')
    DUMP_TIME = os.getenv('DUMP_TIME')
    s_hour, s_minute = SPIDER_TIME.split(":")
    d_hour, d_minute = DUMP_TIME.split(":")
    scheduler.add_job(run_spider,'cron', hour=int(s_hour),minute=int(s_minute))
    scheduler.add_job(dump_db,'cron',hour=int(d_hour),minute=int(d_minute))
    scheduler.start()
    return "Scheduler started"
@app.get("/")
async def root():
    return {"message": "Welcome to the Cars API"}
@app.get("/stats")
def get_stats():
    cur = get_db_connection().cursor()
    cur.execute("SELECT COUNT(url) FROM car_products")
    cur.close()
    return {"Number of products in DB":cur.fetchall()}

@app.get("/items/", response_model=List[dict])
def get_last_items(last: int = 10, first: int | None = None):
    """Get last N items from the database"""
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                if last and first is None:
                    cur.execute("""
                        SELECT * 
                        FROM car_products 
                        ORDER BY id DESC 
                            LIMIT %s
                    """, (last,))
                elif first is not None:
                    cur.execute("""
                                SELECT *
                                FROM car_products
                                ORDER BY id ASC
                                    LIMIT %s
                                """, (first,))
                return cur.fetchall()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
@app.get("/start")
def start_scheduler_endpoint():
    """Start the scheduler"""
    start_scheduler()
    return {"msg":"OK"}
@app.get("/stop")
async def stop_scheduler():
    """Stop the scheduler"""
    global scheduler
    if scheduler and scheduler.running:
        scheduler.shutdown()
        return "Scheduler stopped"
    return "Scheduler is not running"
@app.get("/status")
async def get_status():
    """Get scheduler status"""
    global scheduler
    if scheduler and scheduler.running:
        jobs = scheduler.get_jobs()
        return {
            "status": "running",
            "next_run_time": str(jobs[0].next_run_time) if jobs else "No jobs scheduled"
        }
    return {"status":"stopped"}

def _run_spider_process():
    global spider_process
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = f"logs/spider_{timestamp}.log"
    cmd = [sys.executable, '-m', 'scrapy', 'crawl', 'autoria',
           '-s', 'LOG_LEVEL=INFO', '-s', f'LOG_FILE={log_file}']
    spider_process = subprocess.Popen(cmd)

@app.get("/spider/run")
async def start_spider(background_tasks: BackgroundTasks):
    """Run spider immediately"""
    global spider_process
    # Перевіряємо, чи він вже не запущений
    if spider_process is not None:
        if spider_process.poll() is None:  # poll() == None означає, що процес ще працює
            return {"status": "error", "message": "Spider is already running"}
        else:
            # Процес завершився (успішно або з помилкою), треба "обнулити" його
            spider_process = None
    # Запускаємо через BackgroundTasks, щоб не вішати API
    background_tasks.add_task(_run_spider_process)
    return {"status": "success", "message": "Spider started in background"}

@app.get("/spider/stop")
def stop_spider():
    global spider_process
    if spider_process and spider_process.poll() is None:
        # Надсилаємо сигнал SIGINT (Ctrl+C), щоб Scrapy закрився красиво
        spider_process.terminate()
        spider_process = None
        return {"status": "success", "message": "Stop signal sent to spider"}
    return {"status": "error", "message": "No spider is running"}
@app.get("/spider/status")
def get_status():
    if spider_process and spider_process.poll() is None:
        return {"status":"running","pid":spider_process.pid}
    # return {"status":"idle"}
@app.get('/favicon.ico', status_code=204)
async def ignore_favicon():
    return  # Empty response with 204 No Content
@app.get("/logs")
def get_logs():
    """List all log files"""
    try:
        if not os.path.exists("logs"):
            return []
        return os.listdir("logs")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/logs/{log_file}")
async def read_log(log_file: str):
    """Reads specified log file in web"""
    log_path = f"logs/{log_file}"
    try:
        async with aiofiles.open(log_path, mode="r", encoding="utf-8") as f:
            content = await f.read()
            return Response(content=content, media_type="text/plain")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Log file not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading log file: {str(e)}")
@app.get("/dump")
def dump():
    dump_db()
    return {f"✅ Dump saved to /app/dumps/"}

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("API:app", host="0.0.0.0", port=8000,reload=True)