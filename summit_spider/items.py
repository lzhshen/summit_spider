# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class SummitItem(scrapy.Item):
  # define the fields for your item here like:
  # name = scrapy.Field()
  base_fname = scrapy.Field()
  title = scrapy.Field()
  speakers = scrapy.Field()
  tag = scrapy.Field()
  desc = scrapy.Field()
  video = scrapy.Field()
  slide = scrapy.Field()

class SpeakerItem(scrapy.Item):
  name = scrapy.Field()
  corp = scrapy.Field()
  bio = scrapy.Field()

class VideoItem(scrapy.Item):
  src_link = scrapy.Field()
  dl_link = scrapy.Field()
 
class SlideItem(scrapy.Item):
  src_link = scrapy.Field()
  dl_link = scrapy.Field()

