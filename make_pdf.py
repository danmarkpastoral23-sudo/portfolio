import os, struct

# ─────────────────────────────────────────────────────────────────
#  Minimal pure-Python PDF builder  (no dependencies)
# ─────────────────────────────────────────────────────────────────
class PDF:
    PW, PH = 595, 842   # A4

    def __init__(self):
        self._buf  = bytearray(b'%PDF-1.4\n%\xe2\xe3\xcf\xd3\n')
        self._xref = []
        self._n    = 0
        self._pages = []
        self._fonts = {}

    # ── primitives ──────────────────────────────────────────────
    def _so(self):
        self._n += 1
        self._xref.append(len(self._buf))
        self._buf += f'{self._n} 0 obj\n'.encode()
        return self._n

    def _eo(self): self._buf += b'endobj\n'
    def _w(self, s): self._buf += (s if isinstance(s, bytes) else s.encode())

    # ── font ────────────────────────────────────────────────────
    def font(self, alias, base):
        oid = self._so()
        self._w(f'<</Type/Font/Subtype/Type1/BaseFont/{base}'
                f'/Encoding/WinAnsiEncoding>>\n')
        self._eo()
        self._fonts[alias] = oid

    # ── page ────────────────────────────────────────────────────
    def page(self, ops):
        data = '\n'.join(ops).encode('latin-1', errors='replace')
        sid  = self._so()
        self._w(f'<</Length {len(data)}>>\nstream\n')
        self._buf += data
        self._w('\nendstream\n')
        self._eo()
        frefs = ' '.join(f'/{a} {i} 0 R' for a,i in self._fonts.items())
        pid = self._so()
        self._w(f'<</Type/Page/MediaBox[0 0 {self.PW} {self.PH}]'
                f'/Contents {sid} 0 R'
                f'/Resources<</Font<<{frefs}>>>>'
                f'>>\n')
        self._eo()
        self._pages.append(pid)


    # ── save ────────────────────────────────────────────────────
    def save(self, path):
        kids = ' '.join(f'{p} 0 R' for p in self._pages)
        pg = self._so()
        self._w(f'<</Type/Pages/Kids[{kids}]/Count {len(self._pages)}>>\n')
        self._eo()
        cat = self._so()
        self._w(f'<</Type/Catalog/Pages {pg} 0 R>>\n')
        self._eo()
        xoff = len(self._buf)
        self._w(f'xref\n0 {self._n+1}\n0000000000 65535 f \n')
        for o in self._xref:
            self._w(f'{o:010d} 00000 n \n')
        self._w(f'trailer\n<</Size {self._n+1}/Root {cat} 0 R>>\n'
                f'startxref\n{xoff}\n%%EOF\n')
        with open(path,'wb') as f: f.write(self._buf)
        print(f'Saved {len(self._buf):,} bytes → {path}')


# ─────────────────────────────────────────────────────────────────
#  Drawing helpers  (all coords: origin = bottom-left)
# ─────────────────────────────────────────────────────────────────
def esc(t):
    return (t.replace('\\','\\\\')
             .replace('(','\\(')
             .replace(')','\\)')
             .encode('latin-1', errors='replace')
             .decode('latin-1'))

def rect(ops, x, y, w, h, fill):
    r,g,b = int(fill[:2],16)/255, int(fill[2:4],16)/255, int(fill[4:6],16)/255
    ops += [f'{r:.3f} {g:.3f} {b:.3f} rg', f'{x} {y} {w} {h} re f']

def txt(ops, fnt, sz, x, y, col, text):
    r,g,b = int(col[:2],16)/255, int(col[2:4],16)/255, int(col[4:6],16)/255
    ops += ['BT', f'/{fnt} {sz} Tf',
            f'{r:.3f} {g:.3f} {b:.3f} rg',
            f'{x} {y} Td', f'({esc(text)}) Tj', 'ET']

def line(ops, x1,y1,x2,y2, col='000000', w=1):
    r,g,b = int(col[:2],16)/255, int(col[2:4],16)/255, int(col[4:6],16)/255
    ops += [f'{w} w', f'{r:.3f} {g:.3f} {b:.3f} RG',
            f'{x1} {y1} m', f'{x2} {y2} l', 'S']

def ctext(ops, fnt, sz, y, col, text, pw=595):
    cw = sz * (0.55 if fnt=='B' else 0.48)
    x  = max(30, (pw - len(text)*cw) / 2)
    txt(ops, fnt, sz, x, y, col, text)



# ─────────────────────────────────────────────────────────────────
#  Build PDF
# ─────────────────────────────────────────────────────────────────
pdf = PDF()
pdf.font('B',  'Helvetica-Bold')
pdf.font('R',  'Helvetica')
pdf.font('BI', 'Helvetica-BoldOblique')

W, H = 595, 842

# ═══════════════════════════════════════════════════════════════════
# PAGE 1 — COVER
# ═══════════════════════════════════════════════════════════════════
ops = []
# White background
rect(ops, 0, 0, W, H, 'FFFFFF')

# Left black sidebar
rect(ops, 0, 0, 140, H, '111111')

# Vertical text on sidebar: "PORTFOLIO"  (rotated via matrix)
ops += [
    'BT',
    '/B 11 Tf',
    '1 1 1 rg',
    '0 1 -1 0 28 200 Tm',
    '(COURSE ACCOMPLISHMENT PORTFOLIO) Tj',
    'ET'
]

# Top black bar
rect(ops, 140, H-70, W-140, 70, '111111')
txt(ops, 'R', 9, 160, H-25, 'AAAAAA', 'DAN MARK PASTORAL  |  MECHANICAL ENGINEERING')

# Main content area
# Big name block
rect(ops, 140, H-260, W-140, 185, 'F5F5F5')
txt(ops, 'B', 32, 162, H-115, '111111', 'DAN MARK')
txt(ops, 'B', 32, 162, H-155, '111111', 'PASTORAL')
line(ops, 162, H-170, 450, H-170, '111111', 1.5)
txt(ops, 'R', 11, 162, H-190, '555555', 'Mechanical Engineering Student')
txt(ops, 'R', 9,  162, H-210, '888888', 'Course Accomplishment Portfolio')

# Thin accent line
rect(ops, 155, H-262, 4, 185, '111111')

# Section boxes
sections = [
    (H-320, 'ASSIGNMENTS',    '7 Completed'),
    (H-390, 'QUIZZES',        '3 Taken'),
    (H-460, 'EXAMINATIONS',   'Midterm: 55/70'),
    (H-530, 'LECTURE NOTES',  '7 Chapters'),
]
for yy, title, sub in sections:
    rect(ops, 160, yy, W-180, 55, 'F5F5F5')
    rect(ops, 160, yy, 4, 55, '111111')
    txt(ops, 'B', 12, 174, yy+32, '111111', title)
    txt(ops, 'R', 9,  174, yy+14, '888888', sub)

# Bottom bar
rect(ops, 140, 0, W-140, 50, '111111')
txt(ops, 'R', 8, 162, 18, 'AAAAAA', 'Academic Year  |  Mechanical Engineering Profession')

pdf.page(ops)


# ═══════════════════════════════════════════════════════════════════
# PAGE 2 — PERFORMANCE OVERVIEW
# ═══════════════════════════════════════════════════════════════════
ops = []
rect(ops, 0, 0, W, H, 'FFFFFF')
rect(ops, 0, 0, 140, H, '111111')
ops += ['BT','/B 11 Tf','1 1 1 rg','0 1 -1 0 28 350 Tm',
        '(PERFORMANCE OVERVIEW) Tj','ET']

# Top header
rect(ops, 140, H-70, W-140, 70, '111111')
txt(ops, 'B', 16, 162, H-35, 'FFFFFF', 'PERFORMANCE OVERVIEW')
txt(ops, 'R',  8, 162, H-52, 'AAAAAA', 'Summary of academic standing')

# 4 stat cards  2x2
card_data = [
    ('7',     'Assignments Completed'),
    ('3',     'Quizzes Taken'),
    ('50/50', 'Perfect Score  (Finals Q1)'),
    ('7',     'Lecture Chapters'),
]
cw, ch = 190, 110
positions = [(162, H-210), (372, H-210), (162, H-340), (372, H-340)]
for (cx,cy), (val, lbl) in zip(positions, card_data):
    rect(ops, cx, cy, cw, ch, 'F5F5F5')
    rect(ops, cx, cy, 4, ch, '111111')
    txt(ops, 'B', 28, cx+16, cy+ch-50, '111111', val)
    txt(ops, 'R',  9, cx+16, cy+14,    '888888', lbl)

# Thin divider
line(ops, 162, H-370, W-30, H-370, 'CCCCCC', 0.5)

# Overview note
txt(ops, 'BI', 10, 162, H-395, '555555',
    'Finals Quiz 1 achieved a perfect score of 50/50.')
txt(ops, 'BI', 10, 162, H-412, '555555',
    'Midterm Exam: 55 out of 70  (78.6% passing rate).')

rect(ops, 140, 0, W-140, 50, '111111')
txt(ops, 'R', 8, 162, 18, 'AAAAAA', 'Performance Overview  |  Dan Mark Pastoral')
pdf.page(ops)


# ═══════════════════════════════════════════════════════════════════
# PAGE 3 — ASSIGNMENTS
# ═══════════════════════════════════════════════════════════════════
ops = []
rect(ops, 0, 0, W, H, 'FFFFFF')
rect(ops, 0, 0, 140, H, '111111')
ops += ['BT','/B 11 Tf','1 1 1 rg','0 1 -1 0 28 400 Tm',
        '(ASSIGNMENTS) Tj','ET']

rect(ops, 140, H-70, W-140, 70, '111111')
txt(ops, 'B', 16, 162, H-35, 'FFFFFF', 'ASSIGNMENTS')
txt(ops, 'R',  8, 162, H-52, 'AAAAAA', 'Seven assignments covering core topics')

assignments = [
    ('01', 'Mechanical Engineering Profession', 'Profession'),
    ('02', 'RA 8495',                           'Law & Regulation'),
    ('03', 'Implementing Rules & Regulations',  'Policy / IRR'),
    ('04', 'Code of Ethics',                    'Ethics'),
    ('05', 'Case Study 1',                      'Case Study'),
    ('06', 'Case Study 2',                      'Case Study'),
    ('07', 'National Building Code',            'Building Code'),
]

y = H - 110
for num, title, tag in assignments:
    rect(ops, 162, y-44, W-182, 42, 'F5F5F5')
    rect(ops, 162, y-44, 4, 42, '111111')
    # number badge
    rect(ops, 172, y-38, 28, 28, '111111')
    txt(ops, 'B', 10, 176, y-28, 'FFFFFF', num)
    txt(ops, 'B', 11, 210, y-20, '111111', title)
    txt(ops, 'R',  8, 210, y-34, '888888', tag)
    y -= 54

rect(ops, 140, 0, W-140, 50, '111111')
txt(ops, 'R', 8, 162, 18, 'AAAAAA', 'Assignments  |  Dan Mark Pastoral')
pdf.page(ops)


# ═══════════════════════════════════════════════════════════════════
# PAGE 4 — QUIZZES
# ═══════════════════════════════════════════════════════════════════
ops = []
rect(ops, 0, 0, W, H, 'FFFFFF')
rect(ops, 0, 0, 140, H, '111111')
ops += ['BT','/B 11 Tf','1 1 1 rg','0 1 -1 0 28 380 Tm',
        '(QUIZZES) Tj','ET']

rect(ops, 140, H-70, W-140, 70, '111111')
txt(ops, 'B', 16, 162, H-35, 'FFFFFF', 'QUIZZES')
txt(ops, 'R',  8, 162, H-52, 'AAAAAA', 'Midterm and Finals quiz results')

# MIDTERM label
rect(ops, 162, H-110, W-182, 28, '111111')
txt(ops, 'B', 11, 174, H-98, 'FFFFFF', 'MIDTERM')

# Quiz cards
quiz_cards = [
    (162, H-230, 'Quiz 1', '24', '50'),
    (372, H-230, 'Quiz 2', '12', '56'),
]
for cx,cy,lbl,score,total in quiz_cards:
    rect(ops, cx, cy, 190, 100, 'F5F5F5')
    rect(ops, cx, cy, 4, 100, '111111')
    txt(ops, 'R',  9, cx+14, cy+80, '888888', lbl)
    txt(ops, 'B', 36, cx+14, cy+38, '111111', score)
    line(ops, cx+14, cy+34, cx+80, cy+34, 'CCCCCC', 0.5)
    txt(ops, 'R',  9, cx+14, cy+16, '888888', f'out of {total}')

# FINALS label
rect(ops, 162, H-270, W-182, 28, '111111')
txt(ops, 'B', 11, 174, H-258, 'FFFFFF', 'FINALS')

# Perfect score card
rect(ops, 162, H-390, 400, 100, 'F5F5F5')
rect(ops, 162, H-390, 4, 100, '111111')
txt(ops, 'R',  9, 176, H-310, '888888', 'Quiz 1')
txt(ops, 'B', 36, 176, H-352, '111111', '50')
line(ops, 176, H-356, 300, H-356, 'CCCCCC', 0.5)
txt(ops, 'R',  9, 176, H-374, '888888', 'out of 50')
# perfect badge
rect(ops, 310, H-370, 120, 22, '111111')
txt(ops, 'B', 9, 318, H-360, 'FFFFFF', 'PERFECT SCORE')

rect(ops, 140, 0, W-140, 50, '111111')
txt(ops, 'R', 8, 162, 18, 'AAAAAA', 'Quizzes  |  Dan Mark Pastoral')
pdf.page(ops)


# ═══════════════════════════════════════════════════════════════════
# PAGE 5 — EXAMINATIONS
# ═══════════════════════════════════════════════════════════════════
ops = []
rect(ops, 0, 0, W, H, 'FFFFFF')
rect(ops, 0, 0, 140, H, '111111')
ops += ['BT','/B 11 Tf','1 1 1 rg','0 1 -1 0 28 350 Tm',
        '(EXAMINATIONS) Tj','ET']

rect(ops, 140, H-70, W-140, 70, '111111')
txt(ops, 'B', 16, 162, H-35, 'FFFFFF', 'EXAMINATIONS')
txt(ops, 'R',  8, 162, H-52, 'AAAAAA', 'Official exam results for the semester')

# Midterm exam card — big
rect(ops, 162, H-280, W-182, 180, 'F5F5F5')
rect(ops, 162, H-280, 4, 180, '111111')
txt(ops, 'R', 9,  176, H-116, '888888', 'MIDTERM EXAM')
txt(ops, 'B', 60, 176, H-200, '111111', '55')
line(ops, 176, H-208, 400, H-208, 'CCCCCC', 0.8)
txt(ops, 'R', 11, 176, H-228, '555555', 'out of 70  points')
txt(ops, 'R', 9,  176, H-248, '888888', '78.6%  passing rate')
# percent badge
rect(ops, 350, H-215, 90, 24, '111111')
txt(ops, 'B', 11, 360, H-204, 'FFFFFF', '78.6%')

# Finals exam card
rect(ops, 162, H-430, W-182, 120, '111111')
txt(ops, 'R',  9, 176, H-310, 'AAAAAA', 'FINALS EXAM')
txt(ops, 'B', 40, 176, H-380, 'FFFFFF', 'Pending')
txt(ops, 'R',  9, 176, H-400, 'AAAAAA', 'Score to be recorded')

rect(ops, 140, 0, W-140, 50, '111111')
txt(ops, 'R', 8, 162, 18, 'AAAAAA', 'Examinations  |  Dan Mark Pastoral')
pdf.page(ops)


# ═══════════════════════════════════════════════════════════════════
# PAGE 6 — LECTURE NOTES
# ═══════════════════════════════════════════════════════════════════
ops = []
rect(ops, 0, 0, W, H, 'FFFFFF')
rect(ops, 0, 0, 140, H, '111111')
ops += ['BT','/B 11 Tf','1 1 1 rg','0 1 -1 0 28 370 Tm',
        '(LECTURE NOTES) Tj','ET']

rect(ops, 140, H-70, W-140, 70, '111111')
txt(ops, 'B', 16, 162, H-35, 'FFFFFF', 'LECTURE NOTES')
txt(ops, 'R',  8, 162, H-52, 'AAAAAA', 'Seven chapters of core knowledge')

chapters = [
    ('Chapter 1', 'The Mechanical Engineering Profession'),
    ('Chapter 2', 'RA 8495  —  Mechanical Engineering Act'),
    ('Chapter 3', 'Implementing Rules and Regulations'),
    ('Chapter 4', 'Mechanical Engineering Code of Ethics'),
    ('Chapter 5', 'Local and International Codes and Standards'),
    ('Chapter 6', 'Contracts and Specifications'),
    ('Chapter 7', 'National Building Code of the Philippines'),
]

y = H - 110
for i, (ch, title) in enumerate(chapters):
    bg = 'F5F5F5' if i % 2 == 0 else 'EEEEEE'
    rect(ops, 162, y-44, W-182, 42, bg)
    rect(ops, 162, y-44, 4, 42, '111111')
    txt(ops, 'B', 9,  174, y-22, '888888', ch.upper())
    txt(ops, 'B', 11, 174, y-36, '111111', title)
    y -= 54

# Table of contents label
line(ops, 162, y-10, W-30, y-10, 'CCCCCC', 0.5)
txt(ops, 'R', 8, 162, y-26, '888888',
    'All chapters covered during the academic term.')

rect(ops, 140, 0, W-140, 50, '111111')
txt(ops, 'R', 8, 162, 18, 'AAAAAA', 'Lecture Notes  |  Dan Mark Pastoral')
pdf.page(ops)


# ═══════════════════════════════════════════════════════════════════
# PAGE 7 — TABLE OF CONTENTS
# ═══════════════════════════════════════════════════════════════════
ops = []
rect(ops, 0, 0, W, H, 'FFFFFF')
rect(ops, 0, 0, 140, H, '111111')
ops += ['BT','/B 11 Tf','1 1 1 rg','0 1 -1 0 28 320 Tm',
        '(TABLE OF CONTENTS) Tj','ET']

rect(ops, 140, H-70, W-140, 70, '111111')
txt(ops, 'B', 16, 162, H-35, 'FFFFFF', 'TABLE OF CONTENTS')
txt(ops, 'R',  8, 162, H-52, 'AAAAAA', 'Course Accomplishment Portfolio')

toc = [
    ('01', 'Cover Page'),
    ('02', 'Performance Overview'),
    ('03', 'Assignments'),
    ('  ', '   Assignment 1  —  Mechanical Engineering Profession'),
    ('  ', '   Assignment 2  —  RA 8495'),
    ('  ', '   Assignment 3  —  IRR'),
    ('  ', '   Assignment 4  —  Code of Ethics'),
    ('  ', '   Assignment 5  —  Case Study 1'),
    ('  ', '   Assignment 6  —  Case Study 2'),
    ('  ', '   Assignment 7  —  National Building Code'),
    ('04', 'Quizzes'),
    ('05', 'Examinations'),
    ('06', 'Lecture Notes'),
]

y = H - 110
for num, item in toc:
    is_main = num.strip().isdigit()
    bg = 'F5F5F5' if is_main else 'FAFAFA'
    h_row = 34 if is_main else 26
    rect(ops, 162, y-h_row, W-182, h_row-2, bg)
    if is_main:
        rect(ops, 162, y-h_row, 4, h_row-2, '111111')
        rect(ops, 172, y-h_row+6, 22, 20, '111111')
        txt(ops, 'B', 9, 175, y-h_row+11, 'FFFFFF', num)
        txt(ops, 'B', 11, 204, y-h_row+11, '111111', item)
    else:
        txt(ops, 'R', 9, 180, y-h_row+9, '555555', item)
    y -= h_row + 2

rect(ops, 140, 0, W-140, 50, '111111')
txt(ops, 'R', 8, 162, 18, 'AAAAAA', 'Table of Contents  |  Dan Mark Pastoral')
pdf.page(ops)


# ── SAVE ────────────────────────────────────────────────────────
pdf.save('/projects/sandbox/portfolio/Course_Accomplishment_Portfolio.pdf')
