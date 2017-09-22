# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class SummitItem(scrapy.Item):
  # define the fields for your item here like:
  # name = scrapy.Field()
  title = scrapy.Field()
  speakers = scrapy.Field()
  category = scrapy.Field()
  desc = scrapy.Field()
  video_link = scrapy.Field()
  video_dl_link = scrapy.Field()
  slide_link = scrapy.Field()

  pass
