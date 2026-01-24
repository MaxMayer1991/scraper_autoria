from typing import Any, Self

from playwright.async_api import Page, expect
from scrapy.crawler import Crawler
from scrapy.loader import ItemLoader
from ..items import ScraperAutoriaItem
import scrapy, os, re, redis, psycopg2
from scrapy.selector import Selector
from scrapy import signals
from twisted.internet.error import DNSLookupError, TCPTimedOutError
from scrapy.spidermiddlewares.httperror import HttpError

class AutoriaSpider(scrapy.Spider):
    name = "autoria"
    allowed_domains = ["auto.ria.com"]
    start_urls = ["https://auto.ria.com/uk/car/used/"] # Беру стартову сторінку
                  # "https://auto.ria.com/uk/search/?indexName=auto"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.loop = None
        self.redis_available = True  # Assume Redis is available by default
        try:
            self.r = redis.Redis(host=os.getenv('REDIS_HOST', "localhost"), port=6379, db=0, decode_responses=True, socket_connect_timeout=5)
        except Exception as e:
            self.r = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True, socket_connect_timeout=5)
    @classmethod
    def from_crawler(cls, crawler: Crawler, *args: Any, **kwargs: Any) -> Self:
        spider = super(AutoriaSpider, cls).from_crawler(crawler,*args,**kwargs)
        crawler.signals.connect(spider.spider_opened, signal=signals.spider_opened)
        return spider

    def spider_opened(self, spider):
        self.logger.info("Sync Redis with PostgreSQL...")
        try:
            conn = psycopg2.connect(os.getenv("DATABASE_URL"))
            cur = conn.cursor()
            cur.execute("SELECT url FROM car_products")
            pipe = self.r.pipeline()
            for row in cur:
                pipe.sadd("scraped_urls", row[0])
            pipe.execute()
            self.logger.info("Sync completed successfully!!!")
        except redis.ConnectionError as e:
            self.logger.error(f"Failed to connect to Redis {e}")
            self.redis_available = False
        except Exception as e:
            self.logger.error(f"Error during Redis sync: {e}")
            self.redis_available = False
        finally:
            try:
                cur.close()
                conn.close()
            except:
                pass

    async def start(self):
        for url in self.start_urls:
            yield scrapy.Request( # запит на сайт
                url,
                callback=self.parse,
                meta={'playwright': True, 'playwright_include_page': True}
            )

    def parse(self, response, **kwargs):
        cars = response.css('section.ticket-item')
        for car in cars: # прохід по сторінкам оголошень
            car_url = car.css('a.m-link-ticket::attr(href), a.address::attr(href)').get()
            if car_url and not car_url.strip().startswith(('javascript', '#')):
                if 'newauto' in car_url.lower():
                    continue


                try:
                    if self.r.sismember("scraped_urls", car_url):
                        self.logger.info(f"Skipping {car_url}, already in DB")
                        continue
                except redis.RedisError as e:
                    self.logger.error(f"Redis error: {e}. Continuing without URL deduplication.")
                    self.redis_available = False

                yield response.follow(
                    car_url,
                    callback=self.parse_car_page, # запуск методу для збирання даних
                    meta={
                        'playwright': True,
                        'playwright_include_page': True,
                        'playwright_context': 'new',
                        'playwright_page_goto_kwargs': {
                            'wait_until': 'load',  # Changed: Waits for more JS to run
                            'timeout': 60000,  # Increased: Gives page more time to settle
                        },
                    }
                )
        # Pagination (unchanged)
        next_page = response.css('a.js-next.page-link::attr(href), a.page-link.js-next::attr(href)').get()
        # page_num = 1
        # next_page = response.url + "&page=" + str(page_num)
        if next_page:
            self.logger.info(f"Moving to next page: {next_page}")
            yield response.follow(next_page, callback=self.parse, meta={"playwright":True}) # перехід на наступну сторінку через отримання посилання з кнопки
        else:
            self.logger.info(f"HTTP STATUS (trying to reach next page): {response.status}")
            self.logger.info(f"HEADERS: {response.headers.to_unicode_dict()}")
            # page_num += 1

    async def parse_car_page(self, response, **kwargs):
        page: Page = response.meta.get('playwright_page')
        if not page:
            return

        try:
            # Set default timeout (lower slightly for overall speed)
            page.set_default_timeout(20000)

            # Handle cookie banner (using expect)
            cookie_selector = "button.fc-cta-do-not-consent"
            cookie_locator = page.locator(cookie_selector)
            try:
                await expect(cookie_locator).to_be_visible(timeout=3000)
                await cookie_locator.click(force=True, timeout=5000)
                self.logger.info("✅ Cookie banner closed")
            except AssertionError:
                self.logger.debug("No cookie banner visible")

            # Explicit wait for phone button section to settle
            await page.wait_for_selector("div#sellerInfo", state='visible', timeout=10000)

            # Extract phone (calls updated method)
            phone_number = await self._extract_phone_number(page)
            if phone_number:
                self.logger.info(f"✅ Phone extracted: {phone_number}")
            else:
                self.logger.warning("⚠️ Could not extract phone number")

            # Get content and selector (unchanged)
            content = await page.content()
            sel = Selector(text=content)

            # Loader (unchanged)
            loader = ItemLoader(item=ScraperAutoriaItem(), selector=sel)
            loader.add_value('url', response.url)
            loader.add_css('title', 'div#basicInfoTitle h1::text, div#sideTitleTitle span::text')
            loader.add_css('price_usd', 'div#basicInfoPrice strong::text, div#sidePrice strong::text')
            loader.add_css('odometer', 'div#basicInfoTableMainInfo0 span::text')
            loader.add_css('username', 'div#sellerInfoUserName span::text')
            if phone_number:
                loader.add_value('phone_number', phone_number)
            loader.add_css('image_url', 'img::attr(data-src)')
            loader.add_css('image_count', 'span.common-badge.alpha.medium span::text')
            loader.add_css('car_number', 'div.car-number span::text')
            loader.add_css('car_vin', 'span#badgesVin span::text')

            yield loader.load_item()

        except Exception as e:
            self.logger.error(f"Error processing {response.url}: {str(e)}")
            self.logger.info(f"HTTP STATUS (error scrape car page): {response.status}")
            self.logger.info(f"HEADERS: {response.headers.to_unicode_dict()}")
        finally:
            if not page.is_closed():
                await page.close()

    async def _extract_phone_number(self, page: Page) -> str:
        if page.is_closed():
            return ""

        phone_btn_selector = "button.size-large.conversion[data-action='showBottomPopUp']"
        phone_text_selector = "div.popup-inner button.size-large.conversion span"

        try:
            btn = page.locator(phone_btn_selector).first
            await expect(btn).to_be_visible(timeout=5000)
            await expect(btn).to_be_enabled(timeout=3000)
            await btn.scroll_into_view_if_needed()

            # Click with force and fallback
            try:
                await btn.click(force=True, timeout=5000)
                self.logger.info("✅ Phone button clicked")
            except Exception as e:
                self.logger.warning(f"⚠️ Standard click failed: {str(e)} - Trying JS fallback")
                await page.evaluate(f'document.querySelector("{phone_btn_selector}").click()')

            # Short delay for JS to initiate load
            await page.wait_for_timeout(1000)

            # Wait for digits with longer timeout
            try:
                await page.wait_for_function("""
                    () => {
                        const text = document.querySelector('div.popup-inner button.size-large.conversion span')?.innerText || '';
                        return /\d/.test(text);  // Any digit – less strict
                    }
                """, timeout=10000)  # Increased for slow API
            except Exception as wait_e:
                self.logger.warning(f"⚠️ Wait timed out: {str(wait_e)} - Attempting fallback extraction")

            # Always try to extract text (fallback if wait failed)
            phone_elem = page.locator(phone_text_selector).first
            try:
                await expect(phone_elem).to_be_visible(timeout=3000)
                phone_text = await phone_elem.inner_text()
                if phone_text and re.search(r'\d', phone_text):# Quick check in Python
                    return phone_text.strip()
                else:
                    self.logger.debug("Fallback text found but no digits")
            except Exception:
                pass

        except Exception as e:
            self.logger.warning(f"⚠️ Phone extract error: {str(e)}")

        return ""