import scrapy
from scrapy.http import Request
from scrapy.loader import ItemLoader
from summit_spider.items import *

def gen_cookie_map(cstr):
  cmap = {}
  for pair in cstr.split(';'):
    (key, value) = pair.split('=', 1)
    cmap[key.strip()] = value.strip()
  return cmap

def extract_speaker_info(speaker_str):
  (name, corp) = speaker_str.rsplit(',', 1)
  return (name.strip(), corp.strip())

class KafkaSpider(scrapy.Spider):
  name = "kafka-summit-sf17"
  start_urls = [
    'file:///home/shen/mydev/summit_spider/summit_spider/html/kafka-summit-sf17.html',
  ]
  confluent_cookie_str = "__atuvc=2%7C47; __lc.visitor_id.7950501=S1487168434.fe4d62bb33; __hstc=165858785.bed41108038406d514d1be21f9a56214.1480056839886.1493088572462.1493093705403.6; hubspotutk=bed41108038406d514d1be21f9a56214; printfriendly-font-class=pf-15; kafka_summit_sf=yes; _mkto_trk=id:582-QHX-262&token:_mch-www.confluent.io-1505978200408-56477; popup_form_thank_you=null; _vwo_uuid_v2=CC4A3BA15954A517E3FDEA59007E4268|92891eab52a41c14bf1796087f69bbb7; _ga=GA1.2.1019333526.1505978203; _gid=GA1.2.599540853.1505978203; _hjIncludedInSample=1; lc_window_state=minimized; autoinvite_callback=true; autoinvite_callback=true"
  sections = [
              "systems-track",
              "streams-track",
              "pipeline-track",
              "use-case-track",
             ]

  def parse(self, response):
    # extract keynote section
    for topic in response.xpath("//div[@class='featured_kafka_summit']/ul/li"):
      (speaker_str, title_str) = topic.xpath(".//text()").extract_first().split(" - ")
      summit = SummitItem()
      summit['title'] = title_str.strip()
      summit['desc'] = ''
      summit['tag'] = 'keynote'
      speaker = SpeakerItem()
      (speaker['name'], speaker['corp']) = extract_speaker_info(speaker_str)
      speaker['bio'] = ''
      summit['speakers'] = []
      summit['speakers'].append(speaker)
      video_link = topic.xpath("./a/@href").extract_first().strip()
      # send request to video page
      request = Request(url=video_link, 
                        meta={'summit': summit},
                        cookies=gen_cookie_map(self.confluent_cookie_str), 
                        callback=self.parse_video_page)
      yield request
      

#    # extract other sections
#    for s in self.sections:
#      for topic in response.xpath("//section[@id=$sectionId]/div/ul/li", sectionId=s):
#        summit = SummitItem()
#        li = topic.xpath("div[@class='resource_description']/div//text() | div[@class='resource_description']//text()").extract()
#        desc = ''.join(li).strip()
#        video_link = topic.xpath("div[@class='right']/a/@href").extract_first().strip()
#        summit['title'] = topic.xpath(".//div/a/p/text()").extract_first().strip()
#        summit['desc'] = desc
#        summit['tag'] = s
#        summit['speakers'] = []
#        speakers_str = topic.xpath("div/p/text()").extract_first()
#        for speaker_str in speakers_str.split(';'):
#          speaker = SpeakerItem()
#          (speaker['name'], speaker['corp']) = extract_speaker_info(speaker_str)
#          speaker['bio'] = ''
#          summit['speakers'].append(speaker)
#
#        # send request to video page
#        request = Request(url=video_link, 
#                          meta={'summit': summit},
#                          cookies=gen_cookie_map(self.confluent_cookie_str), 
#                          callback=self.parse_video_page)
#        yield request

  def parse_video_page(self, response):
    summit = response.request.meta['summit']
    l = ItemLoader(summit=SummitItem(), response=response)

    link_list = response.xpath("//div[@class='generic_content']/div/div//iframe/@src").extract()
    (video_link, slide_link) = ('', '')
    if link_list:
      (video_link, slide_link) = link_list

    video = VideoItem()
    video['src_link'] = video_link
    video['dl_link'] = ''
    slide = SlideItem()
    slide['src_link'] = slide_link
    slide['dl_link'] = ''
    summit['video'] = video
    summit['slide'] = slide
    summit['base_fname'] = ''
    yield summit


      


