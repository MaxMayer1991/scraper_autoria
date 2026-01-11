import json
from re import I
from scrapy import signals

# useful for handling different item types with a single interface


class CarscraperSpiderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the spider middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        # Called for each response that goes through the spider
        # middleware and into the spider.

        # Should return None or raise an exception.
        return None

    def process_spider_output(self, response, result, spider):
        # Called with the results returned from the Spider, after
        # it has processed the response.

        # Must return an iterable of Request, or item objects.
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        # Called when a spider or process_spider_input() method
        # (from other spider middleware) raises an exception.

        # Should return either None or an iterable of Request or item objects.
        pass

    def process_start_requests(self, start_requests, spider):
        # Called with the start requests of the spider, and works
        # similarly to the process_spider_output() method, except
        # that it doesn’t have a response associated.

        # Must return only requests (not items).
        for r in start_requests:
            yield r

    def spider_opened(self, spider):
        spider.logger.info("Spider opened: %s" % spider.name)


class CarscraperDownloaderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the downloader middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, request, spider):
        # Called for each request that goes through the downloader
        # middleware.

        # Must either:
        # - return None: continue processing this request
        # - or return a Response object
        # - or return a Request object
        # - or raise IgnoreRequest: process_exception() methods of
        #   installed downloader middleware will be called
        return None

    def process_response(self, request, response, spider):
        # Called with the response returned from the downloader.

        # Must either;
        # - return a Response object
        # - return a Request object
        # - or raise IgnoreRequest
        return response

    def process_exception(self, request, exception, spider):
        # Called when a download handler or a process_request()
        # (from other downloader middleware) raises an exception.

        # Must either:
        # - return None: continue processing this exception
        # - return a Response object: stops process_exception() chain
        # - return a Request object: stops process_exception() chain
        pass

    def spider_opened(self, spider):
        spider.logger.info("Spider opened: %s" % spider.name)

from urllib.parse import urlencode
from random import randint
import requests


# middlewares.py

class ScrapeOpsFakeUserAgentMiddleware:
    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler.settings)

    def __init__(self, settings):
        self.scrapeops_api_key = settings.get('SCRAPEOPS_API_KEY')
        self.scrapeops_endpoint = settings.get('SCRAPEOPS_FAKE_USER_AGENT_ENDPOINT',
                                               'https://headers.scrapeops.io/v1/user-agents')
        self.scrapeops_fake_user_agents_active = settings.get('SCRAPEOPS_FAKE_USER_AGENT_ENABLED', False)
        self.scrapeops_num_results = settings.get('SCRAPEOPS_NUM_RESULTS')
        self.headers_list = []
        self._get_user_agent_list()
        self._scrapeops_fake_user_agents_enabled()

    def _get_user_agent_list(self):
        # Додаємо фільтри, щоб отримувати ТІЛЬКИ Chrome для Desktop
        payload = {
            'api_key': self.scrapeops_api_key,
            'num_results': self.scrapeops_num_results,
            'browsers': 'firefox',
            'device_types': 'desktop',  # Ніяких мобільних версій
            'os': 'windows,macos,linux'  # Тільки десктопні ОС
        }

        try:
            response = requests.get(self.scrapeops_endpoint, params=urlencode(payload))
            if response.status_code == 200:
                json_response = response.json()
                self.user_agents_list = json_response.get('result', [])
                print(f"✅ Loaded {len(self.user_agents_list)} Desktop Chrome User-Agents")
            else:
                print(f"❌ ScrapeOps Error: {response.text}")
                self.user_agents_list = []
        except Exception as e:
            print(f"❌ Error getting UAs: {e}")
            self.user_agents_list = []

    def _get_random_user_agent(self):
        if not self.user_agents_list:
            # Fallback, якщо список пустий
            return "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        random_index = randint(0, len(self.user_agents_list) - 1)
        return self.user_agents_list[random_index]

    def _scrapeops_fake_user_agents_enabled(self):
        if self.scrapeops_api_key is not None and self.scrapeops_api_key != '' or self.scrapeops_fake_user_agents_active == False:
            self.scrapeops_fake_user_agents_active = False
        else:
            self.scrapeops_fake_user_agents_active = True

    def process_request(self, request, spider=None):
        # Scrapy все ще може передавати spider як kwarg в старих версіях, тому spider=None безпечніше,
        # але для нових версій аргумент треба прибрати взагалі.
        # Найкращий варіант для сумісності зараз:
        random_user_agent = self._get_random_user_agent()
        request.headers['User-Agent'] = random_user_agent


class ScrapeOpsFakeBrowserHeaderAgentMiddleware:
    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler.settings)

    def __init__(self, settings):
        self.scrapeops_api_key = settings.get('SCRAPEOPS_API_KEY')
        self.scrapeops_endpoint = settings.get('SCRAPEOPS_FAKE_BROWSER_HEADER_ENDPOINT',
                                               'https://headers.scrapeops.io/v1/browser-headers')
        self.scrapeops_fake_browser_headers_active = settings.get('SCRAPEOPS_FAKE_BROWSER_HEADER_ENABLED', True)
        self.scrapeops_num_results = settings.get('SCRAPEOPS_NUM_RESULTS')
        self.headers_list = []
        self._get_headers_list()
        self._scrapeops_fake_browser_headers_enabled()

    def _get_headers_list(self):
        payload = {
            'api_key': self.scrapeops_api_key,
            'num_results': self.scrapeops_num_results,
            'browsers': 'firefox',
            'device_types': 'desktop',  # Тільки Desktop
            'os': 'windows,macos,linux'  # Тільки десктопні ОС
        }
        try:
            response = requests.get(self.scrapeops_endpoint, params=urlencode(payload))
            if response.status_code == 200:
                json_response = response.json()
                # ВАЖЛИВО: Зберігаємо результат у змінну класу
                self.headers_list = json_response.get('result', [])
                print(f"✅ Loaded {len(self.headers_list)} Desktop Firefox Headers")
            else:
                print(f"❌ ScrapeOps Headers Error: {response.text}")
                self.headers_list = []
        except Exception as e:
            print(f"❌ Error getting Headers: {e}")
            self.headers_list = []

    def _get_random_browser_header(self):
        # ВАЖЛИВО: Перевірка на порожній список, щоб уникнути ValueError
        if not self.headers_list:
            # Fallback заголовки, якщо API не відповіло
            return {
                'upgrade-insecure-requests': '1',
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"Windows"'
            }

        random_index = randint(0, len(self.headers_list) - 1)
        return self.headers_list[random_index]

    def _scrapeops_fake_browser_headers_enabled(self):
        if self.scrapeops_api_key is None or self.scrapeops_api_key == '' or self.scrapeops_fake_browser_headers_active == False:
            self.scrapeops_fake_browser_headers_active = False
        else:
            self.scrapeops_fake_browser_headers_active = True

    def process_request(self, request, spider=None):
        random_browser_header = self._get_random_browser_header()

        # Безпечне додавання заголовків
        headers_mapping = {
            'accept-language': 'Accept-Language',
            'sec-fetch-user': 'Sec-Fetch-User',
            'sec-fetch-mod': 'Sec-Fetch-Mod',
            'sec-fetch-site': 'Sec-Fetch-Site',
            'sec-ch-ua-platform': 'Sec-Ch-Ua-Platform',
            'sec-ch-ua-mobile': 'Sec-Ch-Ua-Mobile',
            'sec-ch-ua': 'Sec-Ch-Ua',
            'accept': 'Accept',
            'user-agent': 'User-Agent',
            'upgrade-insecure-requests': 'Upgrade-Insecure-Requests'
        }

        for key, header_name in headers_mapping.items():
            value = random_browser_header.get(key)
            if value:
                request.headers[header_name] = value

        # print("***************** NEW HEADER ATTACHED *********************")
        # print(request.headers)
class ProxyMiddleware:
    @classmethod
    def from_crawler(cls, crawler):
        url  = crawler.settings.get('PROXY_URL')
        return cls(url)
    def __init__(self, proxy_url):
        self.proxy_url  = proxy_url

    def process_request(self, request, spider):
        if self.proxy_url:
            request.meta['proxy'] = self.proxy_url

class PlaywrightContextMiddleware:
    """
    Цей middleware бере User-Agent, який згенерував ScrapeOps (або інший middleware),
    і передає його в налаштування браузера Playwright.
    """

    def process_request(self, request, spider):
        # Працюємо тільки якщо це Playwright-запит
        if not request.meta.get('playwright'):
            return

        # 1. Синхронізація User-Agent
        # ScrapeOps встановлює UA в headers. Ми беремо його звідти.
        ua = request.headers.get('User-Agent')
        if ua:
            # Декодуємо bytes в str
            ua_str = ua.decode('utf-8')

            # Ініціалізуємо словник kwargs, якщо його немає
            request.meta.setdefault('playwright_context_kwargs', {})

            # Встановлюємо UA на рівні браузера (це змінює navigator.userAgent в JS)
            request.meta['playwright_context_kwargs']['user_agent'] = ua_str

            spider.logger.debug(f"🕷️ Playwright Context UA set to: {ua_str}")

        # 2. Проксі обробляється автоматично через request.meta['proxy'],
        # який встановлює ваш існуючий ProxyMiddleware.
        # Додаткових дій тут не потрібно.

        return None