# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html
from itemloaders.processors import TakeFirst, MapCompose, Compose
from . import loaders as l
import scrapy

class ScraperAutoriaItem(scrapy.Item):
    url = scrapy.Field(output_processor=TakeFirst())
    title = scrapy.Field(output_processor=TakeFirst())
    price_usd = scrapy.Field(
        input_processor=Compose(
            MapCompose(str.strip),  # remove spaces
            lambda vals: vals,  # put everyone on the list
            l.choose_price,  # select the line with $
            l.clean_price  # convert to int
        ),
        output_processor=TakeFirst()  # take the single number
    )

    odometer = scrapy.Field(
        input_processor=MapCompose(l.clean_odometer),
        output_processor=TakeFirst()
    )
    username = scrapy.Field(
        input_processor=MapCompose(l.clean_value),
        output_processor=TakeFirst()
    )
    phone_number = scrapy.Field(
        input_processor=MapCompose(l.clean_phone_list)
    )
    image_url = scrapy.Field()  # Leave it as a list
    image_count = scrapy.Field(
        input_processor=MapCompose(l.clean_image_count),
        output_processor=l.TakeSecond
    )
    car_number = scrapy.Field(
        input_processor=MapCompose(l.clean_value)
    )
    car_vin = scrapy.Field(
        input_processor=MapCompose(l.clean_value)
    )