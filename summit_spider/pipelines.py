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
import os
from lxml import html as _parse
import subprocess, shlex
from threading import Timer


logger = logging.getLogger(__name__)

def getExcludeSet(dir, suffix):
    files = glob.glob(dir + "/*" + suffix)
    files = [os.path.basename(file) for file in files]
    exclude_set = set(files)
    return exclude_set


def run(cmd, timeout_sec=10):
  proc = subprocess.Popen(shlex.split(cmd), stdout=subprocess.PIPE,
    stderr=subprocess.PIPE)
  kill_proc = lambda p: p.kill()
  timer = Timer(timeout_sec, kill_proc, [proc])
  try:
    timer.start()
    stdout,stderr = proc.communicate()
  finally:
    timer.cancel()

class VideoDlLinkSniffer(object):
  _PROXY = {'host': '127.0.0.1', 'port': '8780', 'usr': 'pico', 'pwd': 'pico2009server'}

  def __init__(self, proxy_type):
    fp = webdriver.FirefoxProfile()
    # set proxy type
    fp.set_preference('network.proxy.type', int(proxy_type))
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

  def sniff(self, vlink):
    self._driver.get("https://en.savefrom.net")
    # submit video url
    inputElement = WebDriverWait(self._driver, 30).until(EC.presence_of_element_located((By.ID, "sf_url")))
    inputElement.clear()
    inputElement.send_keys(vlink)
    inputElement.submit()

    # fetch video download link
    linkDiv = WebDriverWait(self._driver, 30).until(EC.presence_of_element_located((By.CLASS_NAME, "def-btn-box")))
    link = linkDiv.find_elements_by_xpath(".//a")

    # download video file
    dl_link = ""
    if link:
      dl_link = link[0].get_attribute("href")
    return dl_link

  def __del__(self):
    self._driver.quit()


class SummitSpiderPipeline(object):

  def open_spider(self, spider):
    proxy_type = 0
    if hasattr(spider, 'proxy_type'):
      proxy_type = spider.proxy_type 
    self._vlink_sniffer = VideoDlLinkSniffer(proxy_type)

    self._video_dir = "%s/%s" % (spider.dst_dir, "videos")
    self._video_set = getExcludeSet(self._video_dir, ".mp4")
    logger.info(">>> video exclude set: %s" % (self._video_set))

    self._slide_dir = "%s/%s" % (spider.dst_dir, "slides")
    self._slide_set = getExcludeSet(self._slide_dir, ".pdf")

    self._dl_type_list = []
    if hasattr(spider, 'dl_type'):
      self._dl_type_list.append(spider.dl_type)
    else:
      self._dl_type_list = ['slide', 'video']

  def process_item(self, item, spider):

    if 'video' in self._dl_type_list:
      ### download video file ###
      video_name = "%s.mp4" % (item['base_fname'])
      video_full_name = "%s/%s" % (self._video_dir, video_name)
      if video_name in self._video_set:
        logger.info(">>> Skip %s" % (video_name))
      else:
        video_link = item['video']['src_link']
        video_dl_link = self._vlink_sniffer.sniff(video_link)
        if video_link and video_dl_link:
          cmd_str = "/usr/bin/wget -O %s %s -o /tmp/wget.log" % (video_full_name, video_dl_link)
          logger.info(">>>> execute cmd: %s" % (cmd_str))
          run(cmd_str, 300)

    if 'slide' in self._dl_type_list:
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

        cmd_str = "/usr/bin/convert %s/*.jpg* %s/%s" % (img_tmp_dir, self._slide_dir, slide_name)
        print "       %s" % (cmd_str)
        run(cmd_str, 30)

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
    pass

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

