__all__ = ["OutputEngine"]

import os
import re
import time
from sets import Set
from kofoto.common import symlinkOrCopyFile

class OutputEngine:
    def __init__(self, env):
        self.env = env
        self.blurb = 'Generated by <a href="http://svn.rosdahl.net/kofoto/kofoto/" target="_top">Kofoto</a> %s.' % time.strftime("%Y-%m-%d %H:%M:%S")
        self.generatedFiles = Set()


    def getImageReference(self, image, widthlimit, heightlimit):
        def helper():
            # Given the image, this function computes and returns a
            # suitable image name and a reference be appended to
            # "@images/".
            captured = image.getAttribute(u"captured")
            if captured:
                m = re.match("^(\d+)-(\d+)", captured)
                if m:
                    timestr = captured \
                              .replace(" ", "_") \
                              .replace(":", "") \
                              .replace("-", "")
                    name = "%s-%sx%s.jpg" % (
                        timestr,
                        widthlimit,
                        heightlimit)
                    return "/".join([m.group(1), m.group(2), name])
            base, ext = os.path.splitext(os.path.basename(image.getLocation()))
            return "/".join([
                "undated",
                "%s-%dx%d-%d%s" % (
                    base, widthlimit, heightlimit, image.getId(), ext)])

        key = (image.getHash(), widthlimit, heightlimit)
        if not self.imgref.has_key(key):
            if self.env.verbose:
                self.env.out("Generating image %d, size limit %dx%d..." % (
                    image.getId(), widthlimit, heightlimit))
            imgabsloc, width, height = self.env.imagecache.get(
                image, widthlimit, heightlimit)
            htmlimgloc = os.path.join(
                "@images", helper().encode(self.env.codeset))
            # Generate a unique htmlimgloc/imgloc.
            i = 1
            while True:
                if not htmlimgloc in self.generatedFiles:
                    self.generatedFiles.add(htmlimgloc)
                    break
                base, ext = os.path.splitext(htmlimgloc)
                htmlimgloc = re.sub(r"(-\d)?$", "-%d" % i, base) + ext
                i += 1
            imgloc = os.path.join(self.dest, htmlimgloc)
            try:
                os.makedirs(os.path.dirname(imgloc))
            except OSError:
                pass
            symlinkOrCopyFile(imgabsloc, imgloc)
            self.imgref[key] = ("/".join(htmlimgloc.split(os.sep)),
                                width,
                                height)
            if self.env.verbose:
                self.env.out("\n")
        return self.imgref[key]


    def writeFile(self, filename, text, binary=False):
        if binary:
            mode = "wb"
        else:
            mode = "w"
        file(os.path.join(self.dest, filename), mode).write(text)


    def symlinkFile(self, source, destination):
        symlinkOrCopyFile(source, os.path.join(self.dest, destination))


    def makeDirectory(self, dir):
        absdir = os.path.join(self.dest, dir)
        if not os.path.isdir(absdir):
            os.mkdir(absdir)


    def generate(self, root, subalbums, dest):
        def addDescendants(albumset, album):
            if not album in albumset:
                albumset.add(album)
                for child in album.getAlbumChildren():
                    addDescendants(albumset, child)

        self.dest = dest.encode(self.env.codeset)
        try:
            os.mkdir(self.dest)
        except OSError:
            pass
        self.imgref = {}

        self.env.out("Calculating album paths...\n")
        albummap = _findAlbumPaths(root)

        albumsToGenerate = Set()
        if subalbums:
            for subalbum in subalbums:
                addDescendants(albumsToGenerate, subalbum)
            for subalbum in subalbums:
                albumsToGenerate |= Set(subalbum.getAlbumParents())
        else:
            albumsToGenerate |= Set(albummap.keys())

        self.preGeneration(root)
        i = 1
        items = albummap.items()
        items.sort(lambda x, y: cmp(x[0].getTag(), y[0].getTag()))
        for album, paths in items:
            if album in albumsToGenerate:
                nchildren = len(list(album.getChildren()))
                if nchildren == 1:
                    childrentext = "1 child"
                else:
                    childrentext = "%d children" % nchildren
                self.env.out("Creating album %s (%d of %d) with %s...\n" % (
                    album.getTag().encode(self.env.codeset),
                    i,
                    len(albumsToGenerate),
                    childrentext))
                i += 1
                self._generateAlbumHelper(album, paths)
        self.postGeneration(root)


    def _generateAlbumHelper(self, album, paths):
        if self.env.verbose:
            self.env.out("Generating album page for %s...\n" %
                         album.getTag().encode(self.env.codeset))

        # Design choice: This output engine sorts subalbums before
        # images.
        children = list(album.getChildren())
        albumchildren = [x for x in children if x.isAlbum()]
        imagechildren = [x for x in children if not x.isAlbum()]

        self.generateAlbum(
            album, albumchildren, imagechildren, paths)

        for ix in range(len(imagechildren)):
            child = imagechildren[ix]
            if self.env.verbose:
                self.env.out(
                    "Generating image page for image %d in album %s...\n" % (
                        child.getId(),
                        album.getTag().encode(self.env.codeset)))
            self.generateImage(album, child, imagechildren, ix, paths)


######################################################################

def _findAlbumPaths(startalbum):
    """Traverse all albums reachable from a given album and find
    possible paths to the albums.

    The traversal is started at startalbum. The return value is a
    mapping where each key is an Album instance and the associated
    value is a list of paths, where a path is a list of Album
    instances."""
    def helper(album, path):
        if album in path:
            # Already visited album, so break recursion here.
            return
        path = path[:] + [album]
        if not albummap.has_key(album):
            albummap[album] = []
        albummap[album].append(path)
        for child in album.getChildren():
            if child.isAlbum():
                helper(child, path)
    albummap = {}
    helper(startalbum, [])
    return albummap
