import os, stat, struct


class GIFFileSized(object):

    def __init__(self, image):
        self._image = image


    def getImageSize(self):
        data = self._image
        data.seek(0)
        data = data.read(24)
        size = len(data)
        width = -1
        height = -1
        if (size >= 10) and data[:6] in ('GIF87a', 'GIF89a'):
            # Check to see if content_type is correct
            w, h = struct.unpack("<HH", data[6:10])
            width = int(w)
            height = int(h)
        return width, height
