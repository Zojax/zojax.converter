# Found on a russian zope mailing list, and modified to fix bugs in parsing
# the magic file and string making, cleanup
import sys, os.path
import struct, time, re, pprint

from interfaces import MagicError


class MagicTestError(MagicError):
    pass


class OffsetError(MagicError):
    pass


class MagicFileError(MagicError):
    pass


mime = 1
default_magic = os.path.join(os.path.dirname(__file__), 'magic.mime')

_ldate_adjust = lambda x: time.mktime( time.gmtime(x) )

BUFFER_SIZE = 1024 * 128 # 128K should be enough...


def _handle(fmt='@x',adj=None): 
    return fmt, struct.calcsize(fmt), adj


KnownTypes = {
    'byte': _handle('@b'),
    'byte': _handle('@B'),
    'ubyte': _handle('@B'),
    'string': ('s', 0, None),
    'pstring': _handle('p'),
    'short': _handle('@h'),
    'beshort': _handle('>h'),
    'leshort': _handle('<h'),
    'short': _handle('@H'),
    'beshort': _handle('>H'),
    'leshort': _handle('<H'),
    'ushort': _handle('@H'),
    'ubeshort': _handle('>H'),
    'uleshort': _handle('<H'),
    
    'long': _handle('@l'),
    'belong': _handle('>l'),
    'lelong': _handle('<l'),
    'ulong': _handle('@L'),
    'ubelong': _handle('>L'),
    'ulelong': _handle('<L'),
    
    'date': _handle('=l'),
    'bedate': _handle('>l'),
    'ledate': _handle('<l'),
    'ldate': _handle('=l', _ldate_adjust),
    'beldate': _handle('>l', _ldate_adjust),
    'leldate': _handle('<l', _ldate_adjust),
}


def has_format(s):
    n = 0
    l = None
    for c in s:
        if c == '%':
            if l == '%': n -= 1
            else       : n += 1
        l = c
    return n


def make_string(s):
    # hack, is this the right way?
    s = s.replace('\\<', '<')
    s = s.replace('\\ ', ' ')
    return eval('"%s"'%s.replace('"', '\\"'))


class MagicTest:

    def __init__(self, offset, mtype, test, message, line=None, level=None):
        self.line, self.level = line, level
        self.mtype = mtype
        self.mtest = test
        self.subtests = []
        self.mask = None
        self.smod = None
        self.nmod = None
        self.offset, self.type, self.test, self.message = \
            offset, mtype, test, message

        if self.mtype == 'true':
            return # XXX hack to enable level skips

        if (test[-1:] == '\\') and (test[-2:] != '\\\\'):
            self.test += 'n' # looks like someone wanted EOL to match?

        if mtype[:6] == 'string':
            if '/' in mtype : # for strings
                self.type, self.smod = \
                    mtype[:mtype.find('/')], mtype[mtype.find('/')+1:]
        else:
            for nm in '&+-':
                if nm in mtype: # for integer-based
                    self.nmod = nm
                    self.type = mtype[:mtype.find(nm)]

                    # convert mask to int, autodetect base
                    self.mask = int(mtype[mtype.find(nm)+1:], 0)
                    break

        self.struct, self.size, self.cast = KnownTypes[self.type]

    def __str__(self):
        return '%s %s %s %s' % (
            self.offset, self.mtype, self.mtest, self.message)

    def __repr__(self):
        return 'MagicTest(%s,%s,%s,%s,line=%s,level=%s,subtests=\n%s%s)' % (
                `self.offset`, `self.mtype`, `self.mtest`, `self.message`,
                `self.line`, `self.level`,
                '\t'*self.level, pprint.pformat(self.subtests)
        )

    def run(self, file):
        result = ''

        try:
            if self.mtype != 'true':
                data = self.read(file)
                try:
                    last = file.tell()
                except Exception, e:
                    # TODO: check what's happen here, I run into this on 
                    # windows guessing a content type for flv files. ri
                    pass
            else:
                data = last = None

            if self.check(data):
                result = self.message + ' '

                if has_format(result):
                    result %= data

                for test in self.subtests:
                    m = test.run(file)
                    if m is not None:
                        result += m

                return make_string(result)
        except Exception, e:
            #log_info('Type detection: %s'%str(e)
            pass

    def a2i(self, v, base=0):
        if v[-1:] in 'lL': 
            v = v[:-1]
        return int(v, base)

    def get_mod_and_value(self):
        if self.type[-6:] == 'string':
            if self.test[0] in '=<>':
                mod = self.test[0]
                value = make_string(self.test[1:])
            else:
                mod = '='
                value = make_string( self.test )
        else:
            if self.test[0] in '=<>&^':
                mod = self.test[0]
                value = self.a2i(self.test[1:])
            elif self.test[0] == 'x':
                mod = self.test[0]
                value = 0
            else:
                mod = '='
                value = self.a2i(self.test)
        return mod, value

    def read(self, file):
        file.seek(self.offset(file), 0) # SEEK_SET
        try:
            data = rdata = None
            # XXX self.size might be 0 here...
            if self.size == 0:
                # this is an ASCIIZ string...
                size = None
                if self.test != '>\\0': # magic's hack for string read...
                    value = self.get_mod_and_value()[1]
                    size = (value=='\0') and None or len(value)

                rdata = data = self.read_asciiz(file, size=size)
            else:
                rdata = file.read(self.size)
                if not rdata or (len(rdata) != self.size):
                    return None

                data = struct.unpack(self.struct, rdata)[0] # XXX hack??
        except:
            raise MagicTestError('@%s struct=%s size=%d rdata=%s' % (
                    self.offset, `self.struct`, self.size, `rdata`))

        if self.cast:
            data = self.cast(data)

        if self.mask:
            try:
                if self.nmod == '&':
                    data &= self.mask
                elif self.nmod == '+':
                    data += self.mask
                elif self.nmod == '-':
                    data -= self.mask
                else: 
                    raise MagicTestError(self.nmod)
            except:
                raise MagicTestError('data=%s nmod=%s mask=%s' % (
                        `data`, `self.nmod`, `self.mask`))

        return data

    def read_asciiz(self, file, size=None):
        s = []
        if size is not None :
            s = [file.read(size).split('\0')[0]]
        else:
            while 1:
                c = file.read(1)
                if (not c) or (ord(c) == 0) or (c == '\n'):
                    break
            s.append (c)

        return ''.join(s)

    def check(self, data):
        if self.mtype == 'true' :
            return '' # not None !

        mod, value = self.get_mod_and_value()
        if self.type[-6:] == 'string' :
            # "something like\tthis\n"
            if self.smod:
                xdata = data

                if 'b' in self.smod: # all blanks are optional
                    xdata = ''.join(data.split())
                    value = ''.join(value.split())

                if 'c' in self.smod: # all blanks are optional
                    xdata = xdata.upper()
                    value = value.upper()

                if 'B' in self.smod: # compact blanks
                    data = ' '.join(data.split())
                    if ' ' not in data:
                        return None
            else:
                xdata = data
        try:
            if isinstance(data, unicode):
                value = unicode(value)
            if   mod == '=' : result = data == value
            elif mod == '<' : result = data < value
            elif mod == '>' : result = data > value
            elif mod == '&' : result = data & value
            elif mod == '^' : result = (data & (~value)) == 0
            elif mod == 'x' : result = 1
            else: 
                raise MagicTestError(self.test)

            if result:
                zdata, zval = `data`, `value`

                if self.mtype[-6:] != 'string':
                    try: 
                        zdata = hex(data)
                        zval = hex(value)
                    except: 
                        zdata = `data`
                        zval = `value`

            return result
        except:
            raise MagicTestError('mtype=%s data=%s mod=%s value=%s' % (
                    `self.mtype`, `data`, `mod`, `value`))

    def add(self,mt):
        if not isinstance(mt, MagicTest):
            raise MagicTestError((mt, 'incorrect subtest type %s'%(type(mt),)))

        if mt.level == self.level+1:
            self.subtests.append(mt)

        elif self.subtests:
            self.subtests[-1].add(mt)

        elif mt.level > self.level+1:
            # it's possible to get level 3 just after level 1 !!! :-(
            level = self.level + 1
            while level < mt.level:
                xmt = MagicTest(None, 'true', 'x', '', line=self.line, level=level)
                self.add(xmt)
                level += 1
            else:
                self.add(mt) # retry...
        else:
            raise MagicTestError((mt, 'incorrect subtest level %s'%(`mt.level`,)))

    def last_test(self):
        return self.subtests[-1]


class Offset:
    pos_format = {'b':'<B','B':'>B','s':'<H','S':'>H','l':'<I','L':'>I',}
    pattern0 = re.compile(r'''    # mere offset
                ^
                &?                                          # possible ampersand
                (       0                                       # just zero
                |       [1-9]{1,1}[0-9]*        # decimal
                |       0[0-7]+                         # octal
                |       0x[0-9a-f]+                     # hex
                )
                $
                ''', re.X|re.I
    )
    pattern1 = re.compile(r'''    # indirect offset
                ^\(
                (?P<base>&?0                  # just zero
                        |&?[1-9]{1,1}[0-9]* # decimal
                        |&?0[0-7]*          # octal
                        |&?0x[0-9A-F]+      # hex
                )
                (?P<type>
                        \.         # this dot might be alone
                        [BSL]? # one of this chars in either case
                )?
                (?P<sign>
                        [-+]{0,1}
                )?
                (?P<off>0              # just zero
                        |[1-9]{1,1}[0-9]*  # decimal
                        |0[0-7]*           # octal
                        |0x[0-9a-f]+       # hex
                )?
                \)$''', re.X|re.I
    )

    def __init__(self,s):
        self.source = s
        self.value  = None
        self.relative = False
        self.base = self.type = self.sign = self.offs = None

        m = Offset.pattern0.match(s)
        if m: # just a number
            if s[0] == '&':
                self.relative = True
                self.value = int(s[1:], 0)
            else:
                self.value = int( s, 0 )
            return

        m = Offset.pattern1.match(s)
        if m: # real indirect offset
            try:
                self.base = m.group('base')
                if self.base[0] == '&':
                    self.relative = True
                    self.base = int(self.base[1:], 0)
                else:
                    self.base = int(self.base, 0)

                if m.group('type'): 
                    self.type = m.group('type')[1:]

                self.sign = m.group('sign')
                if m.group('off'):
                    self.offs = int( m.group('off'), 0 )

                if self.sign == '-':
                    self.offs = 0 - self.offs
            except:
                raise OffsetError(m.groupdict())

            return
        raise OffsetError(`s`)

    def __call__(self, file=None):
        if self.value is not None:
            return self.value

        pos = file.tell()
        try:
            if not self.relative:
                file.seek(self.offset, 0)

            frmt = Offset.pos_format.get(self.type, 'I')
            size = struct.calcsize(frmt)
            data = struct.unpack(frmt, file.read(size))

            if self.offs:
                data += self.offs

            return data
        finally:
            file.seek(pos, 0)

    def __str__(self): 
        return self.source

    def __repr__(self): 
        return 'Offset(%s)' % `self.source`


class MagicFile(object):

    def __init__(self, filename=default_magic):
        self.tests = []
        self.total_tests = 0
        self.load(filename)

    def load(self, filename=None):
        file = open(filename, 'r', BUFFER_SIZE)
        self.parse(file)
        file.close()

    def parse(self, data):
        line_no = 0
        for line in data:
            line_no += 1

            data = self.parse_line(line)
            if data is None:
                continue

            self.total_tests += 1

            level = data[0]
            new_test = MagicTest(*data[1:], **{'line': line_no, 'level': data[0]})
            try:
                if level == 0 :
                    self.tests.append( new_test )
                else:
                    self.tests[-1].add( new_test )
            except:
                raise MagicFileError('total tests=%s, level=%s, tests=%s'%(
                        len(self.total_tests), 
                        level, pprint.pformat(self.tests)))
        else:
            while self.tests[-1].level > 0 :
                self.tests.pop()

    def parse_line(self, line):
        line = line.lstrip().rstrip('\r\n')

        if not line or line[0]=='#':
            return None

        level = 0
        offset = mtype = test = message = ''

        # get optional level (count leading '>')
        while line and line[0]=='>':
            line, level = line[1:], level+1

        # get offset
        while line and not line[0].isspace():
            offset, line = offset+line[0], line[1:]

        try:
            offset = Offset(offset)
        except:
            raise MagicFileError('line=[%s]' % line)

        # skip spaces
        line = line.lstrip()

        # get type
        c = None
        while line :
            last_c, c, line = c, line[0], line[1:]
            if last_c!='\\' and c.isspace() :
                break # unescaped space - end of field
            else:
                mtype += c
                if last_c == '\\' :
                    c = None # don't fuck my brain with sequential backslashes

        # skip spaces
        line = line.lstrip()

        # get test
        c = None
        while line :
            last_c, c, line = c, line[0], line[1:]
            if last_c!='\\' and c.isspace() :
                break # unescaped space - end of field
            else:
                test += c
                if last_c == '\\' :
                    c = None # don't fuck my brain with sequential backslashes

        # skip spaces
        line = line.lstrip()

        # get message
        message = line
        if mime and line.find("\t") != -1:
            message = line[0:line.find("\t")]

        return level, offset, mtype, test, message

    def detect(self, file):
        answers = set()
        for test in self.tests:
            message = test.run(file)
            if message and message.strip():
                msg = message.strip().split()[0]
                if msg not in answers:
                    answers.add(msg)
                    yield msg
