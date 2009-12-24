##############################################################################
#
# Copyright (c) 2007 Zope Corporation and Contributors.
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
"""

$Id$
"""
import mimetypes
from StringIO import StringIO
from zope import interface
from zope.component import queryUtility

import magic
from interfaces import IConverter, IConverterModule, ConverterNotFound


def convert(source, mimetype, sourceMimetype=None, *args, **kw):
    if isinstance(source, basestring):
        source = StringIO(source)

    if not sourceMimetype:
        source.seek(0, 0)
        sourceMimetype = guessMimetype(source)[0]

    converter = queryUtility(IConverter, '%s:%s'%(sourceMimetype, mimetype))
    if converter is not None:
        return converter.convert(source, *args, **kw)

    raise ConverterNotFound(
        "Converter not found for (%s, %s)"%(sourceMimetype, mimetype))


magicFile = magic.MagicFile()

def guessMimetype(data, filename=None):
    if isinstance(data, basestring):
        data = StringIO(data)

    data.seek(0, 0)

    mts = list(magicFile.detect(data))

    if filename is not None and not mts:
        mt, encoding = mimetypes.guess_type(filename, strict=True)
        if mt and mt not in ('application/octet-stream',
                             'text/x-unknown-content-type'):
            mts.append(mt)

    if not mts:
        mts.append('application/octet-stream')

    return mts


interface.moduleProvides(IConverterModule)
__all__ = tuple(IConverterModule)
