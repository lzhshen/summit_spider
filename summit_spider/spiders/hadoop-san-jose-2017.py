import scrapy
from scrapy.http import Request
from scrapy.loader import ItemLoader
from summit_spider.items import *
from summit_spider.utils import *
import logging

logger = logging.getLogger(__name__)

class HadoopSpider(scrapy.Spider):
  name = "hadoop-san-jose-2017"
  start_urls = [
    'file:///home/shen/mydev/summit_spider/summit_spider/html/hadoop-san-jose-2017.html',
  ]

  def parse(self, response):
    # extract keynote section
    for session in response.xpath("//div[@class='agenda-session']"):
      tag = session.xpath(".//div[@class='track-name']/text()").extract_first().strip()
      if tag in ["Crash Course", "Birds of a Feather"] :
        continue

      summit = SummitItem()
      summit['desc'] = ''
      summit['title'] = session.xpath(".//div[@class='title']/text()").extract_first().strip()
      summit['base_fname'] = gen_base_fname(summit['title'])
      summit['tag'] = session.xpath(".//div[@class='track-name']/text()").extract_first().strip()
      summit['speakers'] = []
      speaker_str_list = session.xpath(".//div[@class='speaker']/text()").extract()
      for speaker_str in speaker_str_list:
        speaker = SpeakerItem()
        (speaker['name'], speaker['corp']) = extract_speaker_info(speaker_str)
        speaker['bio'] = ''
        summit['speakers'].append(speaker)

      # Initialize video and slide section
      video = VideoItem()
      slide = SlideItem()
      video['src_link'] = ''
      video['dl_link'] = ''
      slide['src_link'] = ''
      slide['dl_link'] = ''
      media_links = session.xpath(".//a[@class='content-link']/@href").extract()
      for link in media_links:
        if "youtu.be" in link:
          video['src_link'] = link 
        elif "slideshare.net" in link:
          slide['src_link'] = link 
        else:
          logger.warning("unrecognized media link:%s" % (link))

      summit['video'] = video
      summit['slide'] = slide

      desc_link = session.xpath(".//a[@class='no-highlight']/@href").extract_first()
      if desc_link:
        # send request to description page
        request = Request(url=desc_link, 
                          meta={'summit': summit},
                          callback=self.parse_description_page)
        yield request

  def parse_description_page(self, response):
    summit = response.request.meta['summit']
    l = ItemLoader(summit=SummitItem(), response=response)

    desc_list = response.xpath("//article//p/text()").extract()
    summit['desc'] = "\n".join(desc_list)
    yield summit
