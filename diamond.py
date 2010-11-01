#!/usr/bin/env python

import sys
import mclevel
from numpy import array, where
import cPickle

def get_locs_for_world(world):
  diamond = world.materials.materialNamed("Diamond Ore")
  locs = {}
  for chunkx, chunkz in world.presentChunks:
    print "Processing %d, %d" % (chunkx, chunkz)
    chunk = world.getChunk(chunkx, chunkz)
    for row in array(where(chunk.Blocks == diamond)).T:
      locs[tuple(row + (chunkx * 16, chunkz * 16, 0))] = 1
  return locs

adjacency = []
for x in range(-1, 2):
  for y in range(-1, 2):
    for z in range(-1, 2):
      if x == 0 or y == 0 or z == 0:
        adjacency.append((x,y,z))

def remove_cluster(locs):
  index = 0
  cluster = [locs.iterkeys().next()]
  del locs[cluster[0]]

  while index < len(cluster):
    current = cluster[index]
    for dir_ in adjacency:
      tup = tuple([current[x] + dir_[x] for x in range(3)])
      if tup in locs:
        cluster.append(tup)
        del locs[tup]
    index += 1
  return cluster

def num_to_shape(num):
  chrs = ('.', '#')
  out = []
  for row in range(3):
    slice_ = [chrs[(num >> x) & 1] for x in range(row * 4, (row + 1) * 4)]
    if row == 1:
      slice_.insert(2, num & 4096 and '_' or ' ')
    else:
      slice_.insert(2, ' ')
    out.append(''.join(slice_))
  out.reverse()
  return '\n'.join(out)

def clust_to_num(clust):
  t = zip(*clust)
  mins = [min(x) for x in t]
  maxs = [max(x) for x in t]
  if maxs[0] - mins[0] > 1 or maxs[1] - mins[1] > 1 or maxs[2] - mins[2] > 2:
    return None
  acc = 0
  #if maxs[0] // 16 > mins[0] // 16 or maxs[1] // 16 > mins[1] // 16:
    # Crosses chunk boundary
    #acc = 4096
  for tup in clust:
    acc += 1 << ((tup[2] - mins[2]) * 4 +
                 (tup[1] - mins[1]) * 2 +
                 (tup[0] - mins[0]) * 1)
  return acc

dedup_table = range(1 << 13)

def dedup(num):
  if not num:
    return num
  # Lower to base level
  while not num & 0xF:
    num >>= 4
  min_ = num
  for flips in range(2):
    for rotates in range(4):
      min_ = min(min_, num)
      num = (num&0x111)<<1 | (num&0x222)<<2 | (num&0x444)>>2 | (num&0x888)>>1
    num = (num&0x333)<<2 | (num&0xCCC)>>2
  return min_

def bits(num):
  acc = 0
  while num:
    acc += 1
    num = num & (num - 1)
  return acc

for x in dedup_table:
  # Compare rightside-up and upside-down versions
  dedup_table[x] = min(dedup((x&0x00F)<<8 | (x&0x0F0) | (x&0xF00)>>8),
                       dedup(x&0xFFF)) | x & 0x1000
  if bits(x) != bits(dedup_table[x]):
    raise ValueError("Whoops!")

if __name__ == '__main__':
  world = mclevel.fromFile("../World2.bigger")
  locs = get_locs_for_world(world)
  cPickle.dump(locs, file("cached_locs", "wb"), 2)

if __name__ == '__main__':
  locs = cPickle.load(file("cached_locs", "rb"))
  print "Found %d diamond ore" % len(locs)

  clusters = []
  while len(locs):
    clusters.append(remove_cluster(locs))

  cluster_sizes = [0]*20
  by_slice = [0]*20
  maxes = [[0]*20 for x in range(3)]
  cluster_shapes = {}
  for clust in clusters:
    cluster_sizes[len(clust)] += 1
    num = clust_to_num(clust)
    if num is not None:
      num = dedup_table[num]
      cluster_shapes[num] = cluster_shapes.setdefault(num, 0) + 1
    for tup in clust:
      by_slice[tup[2]] += 1
    t = zip(*clust)
    for x in range(3):
      maxes[x][max(t[x]) - min(t[x])] += 1
  print "Cluster size distribution: %r" % cluster_sizes
  print "Slice height distribution: %r" % by_slice
  print "Length(x) distribution: %r" % maxes[0]
  print "Width(z) distribution: %r" % maxes[1]
  print "Height(y) distribution: %r" % maxes[2]
  shapes = cluster_shapes.items()
  shapes.sort(key=lambda x:x[1])
  shapes.reverse()
  acc = 0
  total = 0
  for shape, count in shapes:
    acc += bits(shape) * count
    total += count
  print "Average diamond/deposit: %.3f" % (float(acc) / total)
  i = 0
  line = []
  for shape, count in shapes:
    if not i % 10:
      print "\n".join(["   ".join(x) for x in zip(*line)])
      print
      line = []
    i += 1
    line.append(("%-5d\n%s" % (count, num_to_shape(shape))).split("\n"))
  print "\n".join(["   ".join(x) for x in zip(*line)])
