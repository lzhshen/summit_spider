import scrapy
from scrapy.http import Request
from scrapy.loader import ItemLoader
from summit_spider.items import *
from summit_spider.utils import *
import logging
import re

logger = logging.getLogger(__name__)

class SparkSpider(scrapy.Spider):
  name = "spark-eu-2017"
  start_urls = [
    'file:///home/shen/mydev/summit_spider/summit_spider/html/spark-eu-2017.html',
  ]

  def parse(self, response):
    # there are three sections:
    #   24 Oct - Training Day
    #   25 Oct - Developer Day
    #   26 Oct - Enterprise Day
    # and we ignore "24 Oct - Training Day" section as there is no meaningful information
    for section in response.xpath("//div[@class='schedule-day']"):
      section_name = section.xpath("./h2/text()").extract_first().strip()
      if section_name == '24 Oct - Training Day': # ignore Training Sessions
        continue
      i = 0
      for e in section.xpath(".//div[@class='event-info']"):
        i += 1
        summit = SummitItem()
        detail_link = e.xpath(".//a/@href").extract_first()

        title_str = e.xpath(".//a/text()").extract_first()
        if (not title_str):
          continue 
        logger.info("counter: %d" % (i))
        logger.info(title_str)
        summit['title']= title_str
        summit['base_fname'] = gen_base_fname(summit['title'])
        summit['desc'] = ''
        # tag
        summit['tag'] = 'keynote'
        tag = e.xpath("./div[@class='event-track']/text()").extract_first()
        if tag:
          summit['tag'] = tag.strip()
        # speakers
        summit['speakers'] = [] 
        speakers = e.xpath(".//div[@class='event-speaker']")
        logger.info("speakers: %s" % (speakers))
        for s in speakers:
          speaker = SpeakerItem()
          speaker['name'] = ''
          speaker['corp'] = ''
          logger.info("speaker: %s" % (s))
          speaker_name_str = s.xpath(".//text()").extract_first()
          if speaker_name_str: speaker['name'] = speaker_name_str.strip()
          speaker_corp_str = s.xpath(".//span[@class='speaker.company']/text()").extract_first()
          if speaker_corp_str: speaker['corp'] = re.sub(r'[(|)]', '', speaker_corp_str.strip())
          summit['speakers'].append(speaker)

        # video and slide link
        video = VideoItem()
        slide = SlideItem()
        video['src_link'] = ''
        video['dl_link'] = ''
        slide['src_link'] = ''
        slide['dl_link'] = ''

        spans = e.xpath("./div[@class='event-links']/span")
        for span in spans:
          t = span.xpath(".//text()").extract_first()
          link = span.xpath("./a/@href").extract_first()
          if t and link and (t.strip() == "Video"):
            video['src_link'] = link.strip()
          elif t and link and (t.strip() == "Slides"):
            slide['src_link'] = link.strip()

        summit['video'] = video
        summit['slide'] = slide

        # send request to detail page to fetch description
        if detail_link:
          request = Request(url=detail_link, 
                            meta={'summit': summit},
                            callback=self.fetch_description)
          yield request
        else:
          yield summit

  def fetch_description(self, response):
    summit = response.request.meta['summit']
    l = ItemLoader(summit=SummitItem(), response=response)

    p_list = response.xpath("//div[@class='event-description']/p")
    for p in p_list:
      if p.xpath("./a").extract():
        pass
      else:
        summit['desc'] = p.xpath("./text()").extract_first().strip()

    yield summit
