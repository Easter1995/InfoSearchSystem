# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class ImdbItem(scrapy.Item):
    title = scrapy.Field() # 电影名
    rate = scrapy.Field() # 评分
    summary = scrapy.Field() # 电影简介
    director = scrapy.Field() # 导演
    writers = scrapy.Field() # 编剧
    stars = scrapy.Field() # 明星
    url = scrapy.Field() # 详情页链接
