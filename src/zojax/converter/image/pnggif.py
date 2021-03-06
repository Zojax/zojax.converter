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
""" GIF -> PNG and PNG - > GIF converters

$Id$
"""
from zojax.converter.utils import log
from zojax.converter.image.pilimage import PILImageConverter

import PIL.Image

# check encoders
try:
    PIL.Image.core.gif_decoder
    PIL.Image.core.gif_encoder
    PIL.Image.core.zip_decoder
    PIL.Image.core.zip_encoder
except:
    log("PNG/GIF converters are not available. PIL doesn't support this formats")
    raise ImportError()


class PNGtoGIFConverter(PILImageConverter):

    _from_format = 'zip'
    _dest_format = 'gif'


class GIFtoPNGConverter(PILImageConverter):

    _from_format = 'gif'
    _dest_format = 'zip'
