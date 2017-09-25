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

def extract_basename(video_link):
  basename = ''
  l = re.findall('.*/(\d*).mp4.*', video_link)
  if len(l) > 0:
    basename = l[0]
  return basename


class SummitSpiderPipeline(object):
  _PROXY = {'host': '127.0.0.1', 'port': '8780', 'usr': 'pico', 'pwd': 'pico2009server'}
  def open_spider(self, spider):
    fp = webdriver.FirefoxProfile()

    fp.set_preference('network.proxy.type', 1)
    fp.set_preference('network.proxy.http', self._PROXY['host'])
    fp.set_preference('network.proxy.http_port', int(self._PROXY['port']))
    fp.set_preference('network.proxy.ssl', self._PROXY['host'])
    fp.set_preference('network.proxy.ssl_port', int(self._PROXY['port']))
    fp.set_preference('network.proxy.socks', self._PROXY['host'])
    fp.set_preference('network.proxy.socks_port', int(self._PROXY['port']))
    fp.set_preference('network.proxy.no_proxies_on', 'localhost, 127.0.0.1')
    credentials = '{usr}:{pwd}'.format(**self._PROXY)
    credentials = b64encode(credentials.encode('ascii')).decode('utf-8')
    fp.set_preference('extensions.closeproxyauth.authtoken', credentials)
    self._driver = webdriver.Firefox(firefox_profile=fp)

  def process_item(self, item, spider):
    src_link = item['video']['src_link']
    if src_link:
      self._driver.get("https://en.savefrom.net")
      # submit video url
      inputElement = WebDriverWait(self._driver, 30).until(EC.presence_of_element_located((By.ID, "sf_url")))
      inputElement.clear()
      inputElement.send_keys(src_link)
      inputElement.submit()

      # fetch video download link
      linkDiv = WebDriverWait(self._driver, 30).until(EC.presence_of_element_located((By.CLASS_NAME, "def-btn-box")))
      link = linkDiv.find_elements_by_xpath(".//a")
      if link:
        dl_link = link[0].get_attribute("href")
        # TODO: Do not store video download link here
        item['video']['dl_link'] = '' 
        item['base_fname'] = extract_basename(dl_link)

    return item

  def close_spider(self, spider):
    self._driver.quit()
