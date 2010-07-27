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
import os, tempfile, shlex, subprocess

from zope import interface
from zojax.converter.utils import log
from zojax.converter.interfaces import ConverterException
from zojax.converter.interfaces import ISWFPreviewConverter


class PDF2SWFPreviewConverter(object):
    interface.implementsOnly(ISWFPreviewConverter)

    PDF_CONVERTER_EXECUTABLE = 'pdf2swf'

    def convert(self, data):
        """ convert image """
        data.seek(0, 0)
        temp_files = []
        try:
            pth = tempfile.mkstemp()[1]
            try:
                fp = open(pth, 'w')
                fp.write(data.read())
            finally:
                fp.close()
            temp_files.append(pth)
            swf_path = pth + ".swf"
            parts = shlex.split('sh -c "%s %s -o %s -T 9 -f"' % (self.PDF_CONVERTER_EXECUTABLE, pth, swf_path))
            p = subprocess.Popen(parts, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out, errors = p.communicate()
            if not os.path.exists(swf_path):
                raise ConverterException(out, errors)
            temp_files.append(swf_path)
            return open(swf_path).read()
        finally:
            for i in temp_files:
                os.remove(i)


class OO2SWFPreviewConverter(PDF2SWFPreviewConverter):

    OO_CONVERTER_EXECUTABLE = 'unoconv'

    def convert(self, data):
        data.seek(0, 0)
        temp_files = []
        try:
            pth = tempfile.mkstemp()[1]
            fp = open(pth, 'w')
            try:
                fp.write(data.read())
            finally:
                fp.close()
            pdf_path = pth + ".pdf"
            parts = shlex.split('sh -c "%s --stdout %s > %s"' % (self.OO_CONVERTER_EXECUTABLE, pth, pdf_path))
            p = subprocess.Popen(parts, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out, errors = p.communicate()
            if not os.path.exists(pdf_path):
                raise ConverterException(out, errors)
            temp_files.append(pdf_path)
            return super(OO2SWFPreviewConverter, self).convert(open(pdf_path))
        finally:
            for i in temp_files:
                os.remove(i)


class Text2SWFPreviewConverter(PDF2SWFPreviewConverter):

    A2PS_EXECUTABLE = 'a2ps'

    PS2PDF_EXECUTABLE = 'ps2pdf'

    def convert(self, data):
        data.seek(0, 0)
        temp_files = []
        try:
            pth = tempfile.mkstemp()[1]
            fp = open(pth, 'w')
            try:
                fp.write(data.read())
            finally:
                fp.close()
            pdf_path = pth + ".pdf"
            parts = shlex.split('sh -c "%s -o - -q %s | %s - %s"' % (self.A2PS_EXECUTABLE, pth, self.PS2PDF_EXECUTABLE, pdf_path))
            p = subprocess.Popen(parts, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out, errors = p.communicate()
            if errors or not os.path.exists(pdf_path):
                raise ConverterException(out, errors)
            temp_files.append(pdf_path)
            return super(Text2SWFPreviewConverter, self).convert(open(pdf_path))
        finally:
            for i in temp_files:
                os.remove(i)
