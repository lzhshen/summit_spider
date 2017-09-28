# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait # available since 2.4.0
from selenium.webdriver.support import expected_conditions as EC # available since 2.26.0
from selenium.webdriver.common.proxy import *
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
from base64 import b64encode
import re
import logging

logger = logging.getLogger(__name__)

def extract_basename(video_link):
  basename = ''
  l = re.findall('.*/(\d*).mp4.*', video_link)
  if len(l) > 0:
    basename = l[0]
  return basename


class SummitSpiderPipeline(object):
  _PROXY = {'host': '127.0.0.1', 'port': '8780', 'usr': 'pico', 'pwd': 'pico2009server'}
  _regex_youtube = r'.*(youtube\.com|youtu\.be).*'
  _regex_vimeo = r'.*player\.vimeo\.com.*'
  def open_spider(self, spider):
    fp = webdriver.FirefoxProfile()

    fp.set_preference('network.proxy.type', 1)
    fp.set_preference('network.proxy.http', self._PROXY['host'])
    fp.set_preference('network.proxy.http_port', int(self._PROXY['port']))
    fp.set_preference('network.proxy.ssl', self._PROXY['host'])
    fp.set_preference('network.proxy.ssl_port', int(self._PROXY['port']))
    fp.set_preference('network.proxy.socks', self._PROXY['host'])
    fp.set_preference('network.proxy.socks_port', int(self._PROXY['port']))
    fp.set_preference('network.proxy.ftp', self._PROXY['host'])
    fp.set_preference('network.proxy.ftp_port', int(self._PROXY['port']))
    fp.set_preference('network.proxy.no_proxies_on', 'localhost, 127.0.0.1')
    credentials = '{usr}:{pwd}'.format(**self._PROXY)
    credentials = b64encode(credentials.encode('ascii')).decode('utf-8')
    fp.set_preference('extensions.closeproxyauth.authtoken', credentials)
    self._driver = webdriver.Firefox(firefox_profile=fp)

  def process_item(self, item, spider):
    ## get base namefor the item ##

    self._driver.get("https://en.savefrom.net")
    # submit video url
    src_link = item['video']['src_link']
    inputElement = WebDriverWait(self._driver, 30).until(EC.presence_of_element_located((By.ID, "sf_url")))
    inputElement.clear()
    inputElement.send_keys(src_link)
    inputElement.submit()

    # fetch video download link
    linkDiv = WebDriverWait(self._driver, 30).until(EC.presence_of_element_located((By.CLASS_NAME, "def-btn-box")))
    link = linkDiv.find_elements_by_xpath(".//a")

    # store video download link and get item's base name
    if link:
      dl_link = link[0].get_attribute("href")
      if re.match(self._regex_vimeo, src_link):
          item['video']['dl_link'] = dl_link
          # update base_fname for video from vimeo
          item['base_fname'] = extract_basename(dl_link)
      elif re.match(self._regex_youtube, src_link):
        video_title_str = "%s%s" % ("&title=", item['base_fname'])
        item['video']['dl_link'] = re.sub(r'&title=.*$', video_title_str, dl_link) 
      else:
        logger.warning("The item's base name is empty as the video is neither from youtube not from vimeo!")
        pass
    else:
      logger.warning("Cannot fetch video download link")

    return item

  def close_spider(self, spider):
    self._driver.quit()
