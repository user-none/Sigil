#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab

# Copyright (c) 2014-2023 Kevin B. Hendricks, and Doug Massay
# Copyright (c) 2014      John Schember
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice, this list of
# conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice, this list
# of conditions and the following disclaimer in the documentation and/or other materials
# provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY
# EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES
# OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT
# SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED
# TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS;
# OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY
# WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

from collections import OrderedDict

SPECIAL_HANDLING_TAGS = OrderedDict([
    ('?xml', ('xmlheader', -1)),
    ('!--', ('comment', -3)),
    ('!DOCTYPE', ('doctype', -1)),
    ('![CDATA[', ('cdata', -3)),
    ('?', ('pi', -1))

])

SPECIAL_HANDLING_TYPES = ['xmlheader', 'doctype', 'comment', 'cdata', 'pi']

WHITESPACE_CHARS = (' ', '\n', '\r', '\f', '\t', '\v')

class QuickXHTMLParser(object):

    def __init__(self):
        self.pos = 0
        self.content = None
        self.clen = 0
        self.tagpath = None

    def setContent(self, data, codec='utf-8'):
        if data is None:
            data = ''
        if isinstance(data, bytes):
            self.content = data.decode(codec)
        else:
            self.content = data
        self.pos = 0
        self.clen = len(self.content)
        self.tagpath = ['']


    # parses string version of tag to identify its name,
    # its type 'begin', 'end' or 'single',
    # plus build a hashtable of its atributes
    def parsetag(self, s):
        n = len(s)
        p = 1
        # get the tag name
        tname = None
        ttype = None
        tattr = OrderedDict()
        while p < n and s[p:p + 1] == ' ' : p += 1
        if s[p:p + 1] == '/':
            ttype = 'end'
            p += 1
            while p < n and s[p:p + 1] == ' ' : p += 1
        b = p
        # handle comment special case as there may be no spaces to
        # delimit name begin or end
        if s[b:].startswith('!--'):
            p = b + 3
            tname = '!--'
            ttype, backstep = SPECIAL_HANDLING_TAGS[tname]
            tattr['special'] = s[p:backstep]
            return tname, ttype, tattr
        # handle cdata special case as there may be no spaces to delimit name begin or end
        if s[b:b+8] == "![CDATA[":
            p = b+8
            tname = "![CDATA["
            ttype, backstep = SPECIAL_HANDLING_TAGS[tname]
            tattr['special'] = s[p:backstep]
            return tname, ttype, tattr
        while p < n and s[p:p + 1] not in ('>', '/', ' ', '"', "'", "\r", "\n") : p += 1
        tname = s[b:p].lower()
        # deal with other remaining special cases
        # generic xml processing instruction (pi)
        if tname != "?xml" and s[b:b+1] == "?":
            p = b+1
            tname = "?"
            ttype, backstep = SPECIAL_HANDLING_TAGS[tname]
            tattr['special'] = s[p:backstep]
            return tname, ttype, tattr
        # remaining special cases
        if tname == '!doctype':
            tname = '!DOCTYPE'
        if tname in SPECIAL_HANDLING_TAGS:
            ttype, backstep = SPECIAL_HANDLING_TAGS[tname]
            tattr['special'] = s[p:backstep]
        if ttype is None:
            # parse any attributes
            while s.find('=', p) != -1 :
                while p < n and s[p:p + 1] in WHITESPACE_CHARS : p += 1
                b = p
                while p < n and s[p:p + 1] != '=' : p += 1
                # attribute names can be mixed case and are in SVG
                aname = s[b:p]
                aname = aname.rstrip(' ')
                p += 1
                while p < n and s[p:p + 1] in WHITESPACE_CHARS : p += 1
                if s[p:p + 1] in ('"', "'") :
                    qt = s[p:p + 1]
                    p = p + 1
                    b = p
                    while p < n and s[p:p + 1] != qt : p += 1
                    val = s[b:p]
                    p += 1
                else :
                    b = p
                    while p < n and s[p:p + 1] not in ('>', '/', ' ') : p += 1
                    val = s[b:p]
                tattr[aname] = val
        # label beginning and single tags
        if ttype is None:
            ttype = 'begin'
            if s.find('/', p) >= 0:
                ttype = 'single'
        return tname, ttype, tattr

    # parse leading text of xhtml and tag
    # returns as tuple (Leading Text, Tag)
    # only one will have a value, the other will always be None
    def parseml(self):
        p = self.pos
        if p >= self.clen:
            return None, None
        if self.content[p] != '<':
            res = self.content.find('<', p)
            if res == -1 :
                res = len(self.content)
            self.pos = res
            return self.content[p:res], None
        # handle comment as a special case to deal with multi-line comments
        if self.content[p:p+4] == '<!--':
            te = self.content.find('-->',p+1)
            if te != -1:
                te = te+2
        # handle cdata section as a special case to deal with multi-line 
        elif self.content[p:p+9] == '<![CDATA[':
            te = self.content.find(']]>',p+9)
            if te != -1:
                te = te+2
        else:
            te = self.content.find('>', p + 1)
            ntb = self.content.find('<', p + 1)
            if ntb != -1 and ntb < te:
                self.pos = ntb
                return self.content[p:ntb], None
        self.pos = te + 1
        return None, self.content[p:te + 1]



    # yields leading text, tagpath prefix, tag name, tag type, tag attributes
    # tag prefix is a dotted history of all open parent ("begin') tags
    # tag types are "single", "begin", "end", "comment", "xmlheader", and "doctype"
    # tag attributes is a dictionary of key and value pairs
    def parse_iter(self):
        while True:
            text, tag = self.parseml()
            if text is None and tag is None:
                break
            tp = ".".join(self.tagpath)
            if text is not None:
                tname = ttype = tattr = None
            if tag is not None:
                text = None
                tname, ttype, tattr = self.parsetag(tag)
                if ttype == 'end':
                    last_begin = self.tagpath[-1]
                    if last_begin != tname:
                        print('Warning: Improperly Nested Tags, nesting: ', self.tagpath, ' but parsing end tag: ', tname)
            yield text, tp, tname, ttype, tattr
            if ttype is not None:
                if ttype == 'begin':
                    self.tagpath.append(tname)
                elif ttype == 'end':
                    self.tagpath.pop()


    # create xml tag from tag info
    def tag_info_to_xml(self, tname, ttype, tattr=None):
        if ttype is None or tname is None:
            return ''
        if ttype == 'end':
            return '</%s>' % tname
        if ttype in SPECIAL_HANDLING_TYPES and tattr is not None and 'special' in tattr:
            info = tattr['special']
            if ttype == 'comment':
                return '<%s%s-->' % (tname, info)
            if ttype == 'cdata':
                return '<%s%s]]>' % (tname, info)
            # handle doctype, xmlheader and pi
            return '<%s%s>' % (tname, info)
        res = []
        res.append('<%s' % tname)
        if tattr is not None:
            for key in tattr:
                res.append(' %s="%s"' % (key, tattr[key]))
        if ttype == 'single':
            res.append('/>')
        else :
            res.append('>')
        return "".join(res)
