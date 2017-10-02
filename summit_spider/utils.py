import re

def gen_cookie_map(cstr):
  cmap = {}
  for pair in cstr.split(';'):
    (key, value) = pair.split('=', 1)
    cmap[key.strip()] = value.strip()
  return cmap

# work for youtube video
def gen_base_fname(title):
  fname = re.sub(r'[^A-Z^a-z^0-9^]',r' ', title)
  fname = re.sub(' +','_', fname.strip())
  return fname

def extract_speaker_info(speaker_str):
  (name, corp) = speaker_str.rsplit(',', 1)
  return (name.strip(), corp.strip())

# work for vimeo video
def extract_basename(video_link):
  basename = ''
  l = re.findall('.*/(\d*).mp4.*', video_link)
  if len(l) > 0:
    basename = l[0]
  return basename

def isYoutubeVideo(link):
  import re
  regex = r'.*(youtube\.com|youtu\.be).*'
  return re.match(regex, link)

def isVimeoVideo(link):
  import re
  regex = r'.*player\.vimeo\.com.*'
  return re.match(regex, link)

def repairSlideLink(link):
  import re
  regex = r'^\/\/.*' # missing 'https:'
  link_ok= link
  if re.match(regex, link):
    link_ok = "https:%s" % (link)
  return link_ok 

