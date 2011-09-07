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
import os, tempfile, shlex, subprocess, logging

from zope import interface
from zojax.converter.utils import log
from zojax.converter.interfaces import ConverterException
from zojax.converter.interfaces import ISWFPreviewConverter

logger = logging.getLogger('zojax.converter')

CHUNK_SIZE = 1024*64


class BasePreviceConverter(object):
    interface.implementsOnly(ISWFPreviewConverter)

    CONVERTER_EXECUTABLE = 'pdf2swf'
    
    COMMAND = 'sh -c "%s %s -o %s -T 9 -f"'

    def convert(self, data, filename=None):
        """ convert image """
        data.seek(0, 0)
        temp_files = []
        try:
            fp, pth = tempfile.mkstemp()
            fp = os.fdopen(fp, 'w')
            logger.debug('opened %s', pth)
            temp_files.append(pth)
            try:
                d = data.read(CHUNK_SIZE)
                while d:
                    fp.write(d)
                    d = data.read(CHUNK_SIZE)
            finally:
                logger.debug('closed %s', pth)
                fp.close()
            swf_path = pth + ".swf"
            parts = shlex.split(self.COMMAND % (self.CONVERTER_EXECUTABLE, pth, swf_path))
            p = subprocess.Popen(parts, stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True)
            out, errors = p.communicate()
            res = p.wait()
            if not os.path.exists(swf_path):
                raise ConverterException(out, errors)
            temp_files.append(swf_path)
            fp = open(swf_path)
            logger.debug('opened %s', swf_path)
            try:
                return fp.read()
            finally:
                logger.debug('closed %s', swf_path)
                fp.close()
        finally:
            for i in temp_files:
                os.remove(i)


class PDF2SWFPreviewConverter(BasePreviceConverter):

    CONVERTER_EXECUTABLE = 'pdf2swf'


class GIF2SWFPreviewConverter(BasePreviceConverter):
    interface.implementsOnly(ISWFPreviewConverter)

    CONVERTER_EXECUTABLE = 'gif2swf'
    COMMAND = 'sh -c "%s %s -o %s"'


class JPG2SWFPreviewConverter(BasePreviceConverter):
    interface.implementsOnly(ISWFPreviewConverter)

    CONVERTER_EXECUTABLE = 'jpeg2swf'
    COMMAND = 'sh -c "%s %s -o %s -T 9"'


class PNG2SWFPreviewConverter(BasePreviceConverter):
    interface.implementsOnly(ISWFPreviewConverter)

    CONVERTER_EXECUTABLE = 'png2swf'
    COMMAND = 'sh -c "%s %s -o %s -T 9"'


class OO2SWFPreviewConverter(PDF2SWFPreviewConverter):

    OO_CONVERTER_EXECUTABLE = 'jodconverter'

    def convert(self, data, filename=None):
        data.seek(0, 0)
        temp_files = []
        try:
            fp, pth = tempfile.mkstemp()
            if filename:
                os.close(fp)
                pth += str(os.path.splitext(filename)[1].strip())
                fp = open(pth, 'w')
            else:
                fp = os.fdopen(fp, 'w')
            logger.debug('opened %s', pth)
            pdf_path = pth + ".pdf"
            temp_files.append(pth)
            try:
                d = data.read(CHUNK_SIZE)
                while d:
                    fp.write(d)
                    d = data.read(CHUNK_SIZE)
            finally:
                fp.close()
                logger.debug('closed %s', pth)
            parts = shlex.split('sh -c "%s %s %s"' % (self.OO_CONVERTER_EXECUTABLE, pth, pdf_path))
            p = subprocess.Popen(parts, stdout=subprocess.PIPE, stderr=subprocess.PIPE,close_fds=True)
            out, errors = p.communicate()
            res = p.wait()
            if errors and res:
                logger.warning('Error getting preview (%s, %s): %s', "".join(parts), self.OO_CONVERTER_EXECUTABLE, errors)
            if not os.path.exists(pdf_path):
                raise ConverterException(out, errors)
            temp_files.append(pdf_path)
            return super(OO2SWFPreviewConverter, self).convert(open(pdf_path))
        finally:
            for i in temp_files:
                os.remove(i)


class Text2SWFPreviewConverter(PDF2SWFPreviewConverter):

    A2PS_EXECUTABLE = 'a2ps'
    
    A2PS_COMMAND = 'sh -c "%s -o - -q %s | %s - %s"'

    PS2PDF_EXECUTABLE = 'ps2pdf'

    def convert(self, data, filename=None):
        data.seek(0, 0)
        temp_files = []
        try:
            fp, pth = tempfile.mkstemp()
            fp = os.fdopen(fp, 'w')
            logger.debug('opened %s', pth)
            try:
                d = data.read(CHUNK_SIZE)
                while d:
                    fp.write(d)
                    d = data.read(CHUNK_SIZE)
            finally:
                fp.close()
                logger.debug('closed %s', pth)
            pdf_path = pth + ".pdf"
            parts = shlex.split(self.A2PS_COMMAND % (self.A2PS_EXECUTABLE, pth, self.PS2PDF_EXECUTABLE, pdf_path))
            p = subprocess.Popen(parts, stdout=subprocess.PIPE, stderr=subprocess.PIPE,close_fds=True)
            out, errors = p.communicate()
            res = p.wait()
            if errors or not os.path.exists(pdf_path):
                raise ConverterException(out, errors)
            temp_files.append(pdf_path)
            return super(Text2SWFPreviewConverter, self).convert(open(pdf_path))
        finally:
            for i in temp_files:
                os.remove(i)
                

class HTML2SWFPreviewConverter(Text2SWFPreviewConverter):

    A2PS_EXECUTABLE = 'html2ps'
    
    A2PS_COMMAND = 'sh -c "%s -o - %s | %s - %s"'