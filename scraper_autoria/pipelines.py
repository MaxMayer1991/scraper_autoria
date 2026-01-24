import os
import logging
from datetime import datetime

import psycopg2
from psycopg2.extras import execute_values
from itemadapter import ItemAdapter
from scrapy.exceptions import DropItem


class PostgreSQLPipeline:
    """
    Зберігає Item-и у таблицю cars.
    • бере параметри підключення із змінної `DATABASE_URL`
      (автоматично проксіюється docker-compose’ом).
    • INSERT нових оголошень.
    • UPDATE, якщо оголошення з таким url уже є.
    • fallback-створення таблиці, якщо init.sql не спрацював.
    """

    TABLE_NAME = "car_products"

    def __init__(self, database_url: str, crawler=None):
        self.database_url = os.getenv("DATABASE_URL")
        self.conn = None
        self.cur = None
        self.crawler = crawler
        self.spider = crawler.spider if crawler else None  # Store spider reference
    # --------------------------------------------------------------------- #
    # Scrapy hooks
    # --------------------------------------------------------------------- #
    @classmethod
    def from_crawler(cls,crawler):
        db_url = crawler.settings.get("DATABASE_URL") or os.getenv("DATABASE_URL")
        return cls(db_url, crawler)

    def open_spider(self,spider):
        # No need to check for spider parameter since we store it in __init__
        self.conn = psycopg2.connect(self.database_url)
        self.cur = self.conn.cursor()
        self._ensure_table(self.spider)

    def close_spider(self,spider):  # Keep for interface compatibility
        if self.conn:
            self.cur.close()
            self.conn.close()

    # --------------------------------------------------------------------- #
    # Item processing
    # --------------------------------------------------------------------- #
    def process_item(self, item,spider):
        ad = ItemAdapter(item)
        url = ad.get("url")

        if not url:
            raise DropItem("Missing url")
        try:
            # 1. Чи існує оголошення?
            self.cur.execute(f"SELECT id FROM {self.TABLE_NAME} WHERE url = %s", (url,))
            row = self.cur.fetchone()

            if row:
                self._update_item(ad, row[0])
                # Додайте ID в лог, щоб бачити, що оновлюється саме старий запис
                self.spider.logger.info(f"📝 Updated [ID:{row[0]}]: {url}")
            else:
                self._insert_item(ad)
                self.spider.logger.info(f"✅ Inserted [NEW]: {url}")

            self.conn.commit()
            return item
        except psycopg2.Error as e:
            self.conn.rollback()  # ← ВАЖЛИВО!
            self.spider.logger.error(f"Database error: {e}")
            raise DropItem(f"Database error: {e}")

        except Exception as e:
            self.conn.rollback()  # ← ВАЖЛИВО!
            self.spider.logger.error(f"General error: {e}")
            raise DropItem(f"Error: {e}")

    # ------------------------------------------------------------------ #
    # SQL helpers
    # ------------------------------------------------------------------ #
    def _insert_item(self, ad):
        cols = (
            "url",
            "title",
            "price_usd",
            "odometer",
            "username",
            "phone_number",
            "image_url",
            "image_count",
            "car_number",
            "car_vin",
            "datetime_found",
        )
        values = (
            ad.get("url"),
            ad.get("title"),
            ad.get("price_usd"),
            ad.get("odometer"),
            ad.get("username"),
            # self._norm_phone(ad.get("phone_number")),
            ad.get("phone_number"),
            ad.get("image_url"),
            ad.get("image_count"),
            ad.get("car_number"),
            ad.get("car_vin"),
            datetime.now(),
        )
        placeholders = ", ".join(["%s"] * len(cols))
        self.cur.execute(
            f"INSERT INTO {self.TABLE_NAME} ({', '.join(cols)}) VALUES ({placeholders})",
            values,
        )

    def _update_item(self, ad, item_id):
        self.cur.execute(
            f"""
            UPDATE {self.TABLE_NAME}
            SET title          = %s,
                price_usd      = %s,
                odometer       = %s,
                username       = %s,
                phone_number   = %s,
                image_url      = %s,
                image_count    = %s,
                car_number     = %s,
                car_vin        = %s,
                datetime_updated     = %s
            WHERE id = %s
            """,
            (
                ad.get("title"),
                ad.get("price_usd"),
                ad.get("odometer"),
                ad.get("username"),
                ad.get("phone_number"),
                ad.get("image_url"),
                ad.get("image_count"),
                ad.get("car_number"),
                ad.get("car_vin"),
                datetime.now(),
                item_id,
            ),
        )

    # ------------------------------------------------------------------ #
    # Utility
    # ------------------------------------------------------------------ #
    def _ensure_table(self, spider):
        """
        Таблиця має з’явитись із init.sql.
        Якщо ні — створюємо мінімальну схему (fallback),
        щоби скрапінг не впав.
        """
        self.cur.execute(
            """
            SELECT EXISTS (
              SELECT FROM information_schema.tables
              WHERE  table_name = %s
            )
            """,
            (self.TABLE_NAME,),
        )
        exists = self.cur.fetchone()[0]
        if exists:
            spider.logger.info("✅ Table cars існує (init.sql відпрацював)")
            return

        spider.logger.warning("⚠️  Table cars не знайдено – створюю fallback-схему")
        self.cur.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {self.TABLE_NAME} (
              id              SERIAL PRIMARY KEY,
              url             TEXT UNIQUE NOT NULL,
              title           TEXT,
              price_usd       INTEGER,
              odometer        INTEGER,
              username        TEXT,
              phone_number    BIGINT[],
              image_url       TEXT[],
              image_count     INTEGER,
              car_number      TEXT,
              car_vin         TEXT,
              datetime_found  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
              datetime_updated      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
        self.conn.commit()