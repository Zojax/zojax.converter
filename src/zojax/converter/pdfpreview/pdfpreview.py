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
""" File converter

$Id$
"""
import os
import tempfile
import shlex
import subprocess
import logging

from zope import interface
# from zojax.converter.utils import log
from zojax.converter.interfaces import ConverterException
from zojax.converter.interfaces import IPDFPreviewConverter

logger = logging.getLogger('zojax.converter')

CHUNK_SIZE = 1024 * 64


class BasePreviewConverter(object):
    interface.implementsOnly(IPDFPreviewConverter)


class OO2PDFPreviewConverter(BasePreviewConverter):

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
            parts = shlex.split('sh -c "%s %s %s"' % (
                self.OO_CONVERTER_EXECUTABLE, pth, pdf_path))
            p = subprocess.Popen(
                parts,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                close_fds=True)
            out, errors = p.communicate()
            res = p.wait()
            if errors and res:
                logger.warning(
                    'Error getting preview (%s, %s): %s', "".join(parts),
                    self.OO_CONVERTER_EXECUTABLE, errors)
            if not os.path.exists(pdf_path):
                raise ConverterException(out, errors)
            temp_files.append(pdf_path)
            fp = open(pdf_path)
            logger.debug('opened %s', pdf_path)
            try:
                return fp.read()
            finally:
                logger.debug('closed %s', pdf_path)
                fp.close()
        finally:
            for i in temp_files:
                os.remove(i)


class Text2PDFPreviewConverter(BasePreviewConverter):

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
            parts = shlex.split(self.A2PS_COMMAND % (
                self.A2PS_EXECUTABLE, pth, self.PS2PDF_EXECUTABLE, pdf_path))
            p = subprocess.Popen(
                parts,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                close_fds=True)
            out, errors = p.communicate()
            # res = p.wait()
            if errors or not os.path.exists(pdf_path):
                raise ConverterException(out, errors)
            temp_files.append(pdf_path)
            fp = open(pdf_path)
            logger.debug('opened %s', pdf_path)
            try:
                return fp.read()
            finally:
                logger.debug('closed %s', pdf_path)
                fp.close()
        finally:
            for i in temp_files:
                os.remove(i)
