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
from summit_spider.utils import *
import glob
import requests

logger = logging.getLogger(__name__)

def getExcludeSet(dir, suffix):
    files = glob.glob(dir + "/*" + suffix)
    files = [os.path.basename(file) for file in files]
    exclude_set = set(files)
    return exclude_set


class SummitSpiderPipeline(object):
  _PROXY = {'host': '127.0.0.1', 'port': '8780', 'usr': 'pico', 'pwd': 'pico2009server'}


  def open_spider(self, spider):
    fp = webdriver.FirefoxProfile()
  
    # set proxy type
    proxy_type = 0
    if hasattr('spider', 'proxy_type'):
      proxy_type = int(spider.proxy_type) 
    fp.set_preference('network.proxy.type', proxy_type)

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

    self._video_dir = "%s/%s" % (spider.dst_dir, "videos")
    self._video_set = getExcludeSet(self._video_dir, ".mp4")

    self._slide_dir = "%s/%s" % (spider.dst_dir, "slides")
    self._slide_set = getExcludeSet(self._slide_dir, ".pdf")

  def process_item(self, item, spider):

    ### download video file ###
    video_name = "%s.mp4" % (item['base_fname'])
    video_link = item['video']['src_link']
    if video_link and (video_name not in self._video_set):
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

      # download video file
      if link:
        dl_link = link[0].get_attribute("href")
        fullname = "%s/%s" % (self._video_dir, video_name)
        self.dl_file(dl_link, fullname)
      else:
        logger.warning("Cannot fetch video download link for %s" % (video_name))
    else:
      logger.info("Video(%s.mp4) is either exist or has no video link.")

    # download pdf file
    slide_name = "%s.pdf" % (item['base_fname'])
    slide_link = item['slide']['src_link']
    if slide_link and (slide_name not in self._slide_set):
      link_list = PdfSlideDownloaderUtils.fetchImageUrlInfo(slide_link)
      i = 1
      for link in link_list:
        img_fname = "%03d.jpg" % (i)
        img_tmp_dir = "/tmp/pdfimg/%s" % (item['base_fname'])
        if not os.path.exists(img_tmp_dir): os.mkdir(img_tmp_dir)
        img_full_fname = "%s/%s" % (img_tmp_dir, img_fname)
        self.dl_file(link, img_full_fname)
        i += 1

      cmd_str = "convert %s/*.jpg* %s/%s" % (img_tmp_dir, self._slide_dir, slide_name)
      print "       %s" % (cmd_str)
      os.system(cmd_str)

    return item

  def dl_file(self, vlink, fname):
    import urllib2
    logger.debug(">>>> start to download file from %s and save to %s" % (vlink, fname))
    try:
      mp4file = urllib2.urlopen(vlink, timeout=30)
      if not mp4file:
        logger.error("----- Failed to invoke urlopen on %s as returned fd is None" % (vlink))
        return
      with open(fname,'wb') as output:
        output.write(mp4file.read())
      logger.debug("<<<< done!")
    except:
      logger.error("----- Failed to invoke urlopen on %s" % (vlink))
      return
    
  def close_spider(self, spider):
    self._driver.quit()

class PdfSlideDownloaderUtils():
    _RETRY_NUM = 5

    @staticmethod
    def fetchImageUrlInfo(url):
        for i in range(PdfSlideDownloaderUtils._RETRY_NUM):
            response = requests.get(url, timeout=30)
            #response = requests.get(url, timeout=30)
            if response.status_code == 200:
                break
            else:
                print "    fetch time out, ..."
        arvore = _parse.fromstring(response.content)
        slides = arvore.xpath('//img[@class="slide_image"]/@data-full')
        return slides

    @staticmethod
    def convertImg2Pdf(srcDir, dstDir, tt):

        # copy images by padding zero to it sequence number, e.g. copy "im-being-followed-by-drones-1-1024.jpg"
        # to "im-being-followed-by-drones-001-1024.jpg"
        bname = tt.getBaseFileName()
        img_files = glob.glob(srcDir + "/" +  "*")
        for oldname in img_files:
            idx = oldname.split('-1024.jpg')[0].split('-')[-1]
            newname = "%s/%s-%03d.jpg" % (srcDir, bname, int(idx))
            os.rename(oldname, newname)
        fname = tt.getPdfSlideFileName()

        # convert to pdf
        cmd_str = "convert %s/*.jpg* %s/%s" % (srcDir, dstDir, fname)
        print "       %s" % (cmd_str)
        os.system(cmd_str)

        # delete temp image files
        #cmd_str = "rm -f %s/*" % (srcDir)
        #os.system(cmd_str)

