import re

def gen_cookie_map(cstr):
  cmap = {}
  for pair in cstr.split(';'):
    (key, value) = pair.split('=', 1)
    cmap[key.strip()] = value.strip()
  return cmap

def gen_base_fname(title):
  fname = re.sub(r'[^A-Z^a-z^0-9^]',r' ', title)
  fname = re.sub(' +','_', fname.strip())
  return fname

def extract_speaker_info(speaker_str):
  (name, corp) = speaker_str.rsplit(',', 1)
  return (name.strip(), corp.strip())
