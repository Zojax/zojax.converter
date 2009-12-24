##############################################################################
#
# Copyright (c) 2009 Zope Foundation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
""" PIL based image converter

$Id$
"""
from cStringIO import StringIO

from zope import interface
from zojax.converter.utils import log
from zojax.converter.interfaces import ConverterException
from zojax.converter.interfaces import ISimpleImageConverter

try:
    import PIL.Image
except:
    log("Python Imaging library is not available.")
    raise ImportError()


class PILImageConverter(object):
    interface.implementsOnly(ISimpleImageConverter)

    _from_format = 'raw'
    _dest_format = 'raw'

    def convert(self, data, width=None, height=None, scale=0, quality=88):
        """ convert image """
        data.seek(0, 0)
        try:
            image = PIL.Image.open(data)

            if image.mode == '1':
                image = image.convert('L')
            elif image.mode == 'P':
                image = image.convert('RGBA')

            # get width, height
            orig_size = image.size
            if width is None: width = orig_size[0]
            if height is None: height = orig_size[1]

            # Auto-scaling support
            if scale:
                width =  int(round(int(width) * scale))
                height = int(round(int(height) * scale))

            #convert image
            pilfilter = PIL.Image.NEAREST
            if PIL.Image.VERSION >= "1.1.3":
                pilfilter = PIL.Image.ANTIALIAS

            image.thumbnail((width, height), pilfilter)

            newfile = StringIO()
            image.save(newfile, self._dest_format, quality=quality)
            return newfile.getvalue()
        except Exception, e:
            raise ConverterException(str(e))
