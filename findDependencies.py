#!/usr/bin/env python

from os import environ, popen
from argparse import ArgumentParser
import sys
import re
from glob import glob

parser = ArgumentParser()
parser.add_argument('-rel')
parser.add_argument('-arch', dest = 'scramarch', default = environ.get("SCRAM_ARCH"))
parser.add_argument('-scramroot', default = environ.get("SCRAMV1_ROOT"))
args = parser.parse_args()

rel = args.rel
scramarch = args.scramarch
scramroot = args.scramroot

if scramroot is None:
  scramroot = popen("sh -v scram arch 2>&1 |  grep 'SCRAMV1_ROOT=' | sed 's|;.*||;s|SCRAMV1_ROOT=||;s|\"||g' | sed -e \"s|'||g\"").read()

global name, dir
name, dir = None, None


import os
cwd = os.getcwd()

uses = {}
usedby = {}
beginning = ""

# Traverse desired filesystems
directory = rel + "/tmp" # root dir for traversing

with open(rel + "/etc/dependencies/uses.out", 'w') as file:
  for key, value in uses.items():
    file.write("%s %s\n" % (key,value))

with open(rel + "/etc/dependencies/usedby.out", 'w') as file:
  for key, value in uses.items():
    file.write("%s %s\n" % (key,value))

def doexec(*args):
  print("---- doexec running------" + name)
  getnext = 0
  with open(name, 'r') as file:
    for l in file:
      l = l.rstrip('\n')
      if re.search(r'^[^:]+ :\s*$', l): break
      l = re.sub(r'\s*\\$', r'', l)
      sp1 = l.split()
      if len(sp1) == 0: continue
      if len(sp1[0]) < 4: continue
      sp2 = sp1[0].split('/')
      tsp1 = ""
      foundsrc = 0
      for t in sp2:
        if foundsrc == 1: tsp1 += "%s/" % t
        if t == "src": foundsrc = 1
      tsp1 = tsp1[:-1]
      if tsp1 == "": continue
      if getnext == 1:
        depname = tsp1
        getnext = 0
      else:
        getnext = 0
        if re.search( r'^tmp\/', sp1[0]):
          if re.search( r'(\.o|\/a\/xr+\.cc):$', sp1[0]):
            getnext = 1
        else:
          if re.search( r'^src', sp1[0]):
            if depname in uses.keys():
              uses[depname] += tsp1
            else: uses[depname] = tsp1
            if tsp1 in usedby.keys():
              usedby[tsp1] += depname
            else: usedby[tsp1] = depname


counter = 0

count_rel = 0
count_fname = 0
count_sub_file = 0
count_line = 0

match_counter = 0

def pythonDeps(rel):

  global count_rel
  global count_fname
  global count_sub_file
  global count_line
  global counter

  # print("-- %s -- rel: %s" % (count_rel, rel))
  # count_rel += 1
  cache = {}
  for root, dirs, files in os.walk("%s/src/" % rel):
    for filename in files:
      fpath = os.path.join(root, filename)
      if re.search(r'.py$', fpath):
        fname = fpath
        # print("-- %s -- fname: %s" % (count_fname, fname))
        # count_fname += 1
        file = fname
        file = re.sub(r"^%s\/+src\/+" % rel, r'', file)
        # print("-- %s -- sub file: %s" % (count_sub_file, file))
        # count_sub_file += 1
        if not re.search(r'\/python\/', fname):
          continue
        with open(fname, 'r') as f:
          for line in f.readlines():
            if 'import ' in line:
              line = line.rstrip('\n')
              if re.search(r'^\s*#', line):
                continue
              match_from_import = re.search(r'^\s*from\s+([^\s]+)\s+import\s+', line)
              match_import = re.search(r'^\s*import\s+([^\s]+)\s*', line)
              if match_from_import:
                for x in import2CMSSWDir(match_from_import.group(1), cache):

                  if not cache.has_key("usedby"): cache["usedby"] = {}
                  if not cache.has_key("uses"): cache["uses"] = {}
                  if not cache["usedby"].has_key(x): cache["usedby"][x] = {}
                  if not cache["uses"].has_key(file): cache["uses"][file] = {}
                  if not cache["usedby"][x].has_key(file): cache["usedby"][x][file] = {}
                  if not cache["uses"][file].has_key(x): cache["uses"][file][x] = {}
                  cache["usedby"][x][file] = 1
                  cache["uses"][file][x] = 1
              elif match_import:
                for x in import2CMSSWDir(match_import.group(1), cache):
                  # print x


                  if not cache.has_key("usedby"): cache["usedby"] = {}
                  if not cache.has_key("uses"): cache["uses"] = {}
                  if not cache["usedby"].has_key(x): cache["usedby"][x] = {}
                  if not cache["uses"].has_key(file): cache["uses"][file] = {}
                  if not cache["usedby"][x].has_key(file): cache["usedby"][x][file] = {}
                  if not cache["uses"][file].has_key(x): cache["uses"][file][x] = {}

                  cache["usedby"][x][file] = 1
                  cache["uses"][file][x] = 1
                  # print(cache["usedby"][x][file])
                  # print(cache["uses"][file][x])
    from pprint import pprint
    pprint(cache)
  # for type_ in ("uses","usedby"):
  #   with open("%s/etc/dependencies/py%s.out" % (rel, type_), 'w') as ref:
  #     if not cache.has_key("type_"): cache["type_"] = {}
  #     if not cache["type_"].has_key(x): cache["type_"][x] = {}
  #     for x in sorted(cache[type_].keys()):
  #       print cache[type_][x].keys()
  #       # ref.write("%s %s\n" % (x, " ".join(sorted(cache[type_][x].keys()))))
  #       ref.write("-----------")


def import2CMSSWDir(str, cache):
  pyfiles = []
  # return "===string: %s\n---cache : %s" % (str, cache)
  if not cache.has_key("pymodule"): cache["pymodule"] = {}
  if not cache.has_key("noncmsmodule"): cache["noncmsmodule"] = {}
  for s in str.split(","):
    s = re.sub(r'\.', r'/', s)
    # print "--s--: %s" % s
    if s in cache["pymodule"]:
      pyfiles.append(cache["pymodule"][s])
      # print cache
    elif s not in cache["noncmsmodule"]:
      if os.path.exists("%s/python/%s.py" % (rel, s)):
        # print ("%s/python/%s.py" % (rel, s))
        match = re.search( r'^([^\/]+\/+[^\/]+)\/+(.+)$', s)
        if match:
          # print "*** %s\n###%s" % (match.group(1), match.group(2))
          cache["pymodule"][s] = "%s/python/%s.py" % (match.group(1), match.group(2))
          pyfiles.append("%s/python/%s.py" % (match.group(1), match.group(2)))
      else: cache["noncmsmodule"][s] = 1
  return pyfiles


'''

def buildFileDeps(rel, arch, scramroot):
  pcache = {} # to store ProjectCache.db.gz dict
  cache = {}
  for dir in sorted(pcache["BUILDTREE"].keys()):
    if pcache["BUILDTREE"][dir]["SUFFIX"] != "": continue
    if len(pcache["BUILDTREE"][dir]["METABF"]) == 0: continue
    bf = pcache["BUILDTREE"][dir]["METABF"][0]
    bf = re.sub(r'src\/', r'',bf)
    cache["dirs"][dir] = bf
    pack = dir
    class_ = pcache["BUILDTREE"][dir]["CLASS"]
    if re.search( r'^(LIBRARY|CLASSLIB)$', class_):
      pack = pcache["BUILDTREE"][dir]["PARENT"]
    cache["packs"][pack] = dir
  for dir in cache["dirs"].keys():
    updateBFDeps(dir, pcache, cache)
  for type_ in ("uses","usedby"):
    with open("%s/etc/dependencies/bf%s.out" % (rel, type_), 'w') as ref:
      for x in sorted(cache[type_].keys()):
        ref.write("%s %s\n" % (x, " ".join(sorted(cache[type_][x].keys()))))

def updateBFDeps(dir, pcache, cache):
  bf = cache["dirs"][dir]
  if bf in cache["uses"]: return 0
  cache["uses"][bf] = {}
  for pack in pcache["BUILDTREE"][dir]["RAWDATA"]["DEPENDENCIES"].keys():
    if pack in cache["packs"]:
      xdata = cache["packs"][pack]
      updateBFDeps(xdata, pcache, cache)
      xdata = cache["dirs"][xdata]
      cache["uses"][bf][xdata] = 1
      cache["usedby"][xdata][bf] = 1
      for xdep in cache["uses"][xdata].keys():
        cache["uses"][bf][xdep] = 1
        cache["usedby"][xdep][bf] = 1

import json, re, sys
def data2json(infile):
  jstr = ""
  rebs=re.compile(',\s+"BuildSystem::[a-zA-Z0-9]+"\s+\)')
  revar=re.compile("^\s*\$[a-zA-Z0-9]+\s*=")
  reundef=re.compile('\s*undef,')
  lines = [l.strip().replace(" bless(","").replace("'",'"').replace('=>',' : ')  for l in
  open(infile).readlines()]
  lines[0] = revar.sub("",lines[0])
  lines[-1] = lines[-1].replace(";","")
  for l in lines:
    l =  reundef.sub(' "",',rebs.sub("", l.rstrip()))
    jstr += l
  return json.loads(jstr)

for root, dirs, files in os.walk(directory):
  for filename in files:
    name = os.path.join(root, filename)
    if re.search( r'^.*(\.dep|\/a\/xr+\.cc\.d)\z', name): doexec(0, 'cat','{}')

'''

pythonDeps(rel)
#buildFileDeps(rel, scramarch, scramroot)
#sys.exit()
