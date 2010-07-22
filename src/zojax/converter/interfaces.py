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
""" zojax.converter interfaces

$Id$
"""
from zope import interface


class ConverterException(Exception):
    """ base converter exception """


class ConverterNotFound(ConverterException):
    """ required converter not found """


class MagicError(ConverterException):
    """ exception in magic detection """


class IConverter(interface.Interface):
    """ base interface for data converter """

    def convert(source, *args, **kw):
        """ convert file, return file object """


class IConverterModule(interface.Interface):
    """ converter module """

    def convert(file, mimetype, sourceMimetype=None, **kw):
        """ convert data to mimetype data, return file object """

    def quessMimetype(data, filename=None):
        """ returns a sequence of interfaces that are provided by file like
        objects (file argument) with an optional filename as name """


class ISimpleImageConverter(IConverter):
    """ simple image converter """

    def convert(source, width=None, height=None, scale=0):
        """ convert image """


class ISWFPreviewConverter(IConverter):

    def convert(source):
        """ convert to swf preview """
