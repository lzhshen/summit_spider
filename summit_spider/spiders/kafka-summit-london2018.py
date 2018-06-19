import scrapy
from scrapy.http import Request
from scrapy.loader import ItemLoader
from summit_spider.items import *
from summit_spider.utils import *
import logging

logger = logging.getLogger(__name__)

class KafkaSpider(scrapy.Spider):
  name = "kafka-summit-london2018"
  start_urls = [
    'file:///home/shen/mydev/summit_spider/summit_spider/html/kafka-summit-london2018.html',
  ]
  #confluent_cookie_str = "__atuvc=2%7C47; __lc.visitor_id.7950501=S1487168434.fe4d62bb33; __hstc=165858785.bed41108038406d514d1be21f9a56214.1480056839886.1493088572462.1493093705403.6; hubspotutk=bed41108038406d514d1be21f9a56214; printfriendly-font-class=pf-15; kafka_summit_sf=yes; _mkto_trk=id:582-QHX-262&token:_mch-www.confluent.io-1505978200408-56477; popup_form_thank_you=null; _vwo_uuid_v2=CC4A3BA15954A517E3FDEA59007E4268|92891eab52a41c14bf1796087f69bbb7; _ga=GA1.2.1019333526.1505978203; _gid=GA1.2.599540853.1505978203; _hjIncludedInSample=1; lc_window_state=minimized; autoinvite_callback=true; autoinvite_callback=true"
  confluent_cookie_str = "_mkto_trk=id:582-QHX-262&token:_mch-www.confluent.io-1523171119025-74361; _vwo_uuid_v2=D2FF53860DED66684285D7BE9D4697673|dc82129ddd7fda93632190a17334850c; _ga=GA1.2.463089422.1523171122; confluent_cookies=on; check=true; AMCVS_822F3D5B5A45F32D0A495C11%40AdobeOrg=1; AMCV_822F3D5B5A45F32D0A495C11%40AdobeOrg=-330454231%7CMCIDTS%7C17694%7CMCMID%7C42375875565807038653283962277288649349%7CMCAAMLH-1529286124%7C3%7CMCAAMB-1529286124%7CRKhpRz8krg2tLO6pguXWp5olkAcUniQYPHaMWWgdJ3xzPWQmdj0y%7CMCOPTOUT-1528688525s%7CNONE%7CMCSYNCSOP%7C411-17695%7CvVersion%7C3.1.2; popup_form_thank_you=null; mbox=PC#4027695db19149cf82ae384be1c8b05c.22_31#1586415922|session#c8e16e98c2f345b38d288615a588d9f7#1528683187; _gid=GA1.2.34784319.1528681327; _hjIncludedInSample=1"
  #confluent_cookie_str = """bcookie="v=2&ac97e4d3-c5d1-4724-8de7-521b6f94e1c5"; tos_update_banner_shows=3; _uv_id=99088041; __utmv=186399478.|1=member_type=FREE=1; lms_notice_shown=true; __utmz=186399478.1524145345.17.7.utmcsr=ssslideview|utmccn=profiletracking|utmcmd=sssite; __utma=186399478.1350108088.1513259940.1526176471.1528275946.20; language=**; SERVERID=sldsng1|Wx41D|Wx41C"""
  sections = [ "stream-processing", 
               "streaming-data-pipelines",
               "internals" ]
  xpath_template = "//article[@class='schedule-item track-all track-%s-track style-block']"

  def parse(self, response):
    cookies_map = gen_cookie_map(self.confluent_cookie_str)
    logger.info("cookie_map:%s" % cookies_map)
    # extract other sections
    for s in self.sections:
      xpath_str = self.xpath_template % (s)
      for topic in response.xpath(xpath_str):
        summit = SummitItem()
        video_link = topic.xpath("./div/p[@class='schedule-item-authors'][1]/a/@href").extract_first().strip()
        summit['title'] = topic.xpath("./h1/a/text()").extract_first().strip()
        summit['base_fname'] = gen_base_fname(summit['title'])
        summit['desc'] = ''
        summit['tag'] = s
        summit['speakers'] = []
#        speakers_selector = topic.xpath("./div/p[@class='schedule-item-authors'][last()]/a")
#        for speaker_selector in speakers_selector:
#          speaker = SpeakerItem()
#          (speaker['name'], speaker['corp']) = extract_speaker_info(speaker_selector.xpath("./text()").extract_first())
#          speaker['bio'] = ''
#          summit['speakers'].append(speaker)

        # send request to video page
        request = Request(url=video_link, 
                          meta={'summit': summit},
                          cookies=gen_cookie_map(self.confluent_cookie_str), 
                          callback=self.parse_video_page)
        yield request
        break
      break

  def parse_video_page(self, response):
    summit = response.request.meta['summit']
    l = ItemLoader(summit=SummitItem(), response=response)

    link_list = response.xpath("//div[@class='generic_content']//iframe/@src").extract()
    (video_link, slide_link) = ('', '')
    logger.info("---- links:%s" % (link_list))
    if len(link_list) == 2:
      (video_link, slide_link) = link_list
    elif len(link_list) == 1:
      slide_link = link_list[0]
    else:
      logger.warning("invalid video/slide link: %s", link_list)

    video = VideoItem()
    video['src_link'] = video_link
    video['dl_link'] = ''
    slide = SlideItem()
    slide['src_link'] = slide_link
    slide['dl_link'] = ''
    summit['video'] = video
    summit['slide'] = slide
    yield summit
