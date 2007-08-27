# Webwidgets web developement framework
# Copyright (C) 2006 uAnywhere, Egil Moeller <redhog@redhog.org>
# Copyright (C) 2007 FreeCode AS, Egil Moeller <redhog@redhog.org>

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

import operator

class Table(object):
    rowWidths = {}
    colWidths = {}

    def __init__(self):
        self.cells = []
        self.w = 0
        self.h = 0
        self.rowWidths = dict(self.rowWidths)
        self.colWidths = dict(self.colWidths)

    class Cell(object):
        def __init__(self, content, x, y, w, h):
            self.content = content
            self.x = x
            self.y = y
            self.w = w
            self.h = h

    def isTopLeft(self, x, y):
        return (    self.cells[y][x]
                and self.cells[y][x].x == x
                and self.cells[y][x].y == y)

    def isEdge(self, x, y):
        "Return a tuple of booleans (left, right, top, bottom)"
        if not self.cells[y][x]:
            return (True, True, True, True)
        return (self.cells[y][x].x == x,
                self.cells[y][x].x + self.cells[y][x].w - 1 == x,
                self.cells[y][x].y == y,
                self.cells[y][x].y + self.cells[y][x].h - 1 == y)
            

    def visibleSize(self, x, y):
        if self.cells[y][x]:
            cx = self.cells[y][x].x
            cy = self.cells[y][x].y
            cw = self.cells[y][x].w
            ch = self.cells[y][x].h
        else:
            cx = x
            cy = y
            cw = ch = 1
        
        xs = set(range(cx, cx + cw))
        ys = set(range(cy, cy + ch))

        rowWidths = set(self.rowWidths.keys())
        colWidths = set(self.colWidths.keys())
        
        w = len(xs - colWidths) + reduce(operator.add, [self.colWidths[col] for col in xs.intersection(colWidths)], 0)
        h = len(ys - rowWidths) + reduce(operator.add, [self.rowWidths[row] for row in xs.intersection(rowWidths)], 0)

        return (w, h)
        
    def insert(self, content, x, y, w = 1, h = 1):
        if x + w >= self.w:
            for row in range(0, self.h):
                self.cells[row].extend([None] * (x + w - self.w))
            self.w = x + w
        if y + h >= self.h:
            for n in xrange(self.h, y + h):
                self.cells.append([None] * self.w)
            self.h = y + h
        cell = self.Cell(content, x, y, w, h)
        for py in xrange(y, y + h):
            for px in xrange(x, x + w):
                self.remove(px, py)
                self.cells[py][px] = cell
        return cell
    
    def remove(self, x, y):
        cell = self.cells[y][x]
        if cell:
            for py in range(cell.y, cell.y + cell.h):
                for px in range(cell.x, cell.x + cell.w):
                    self.cells[py][px] = None
        return cell

    def __str__(self):
        res = ''
        for y in xrange(0, self.h):
            for x in xrange(0, self.w):
                left, right, top, bottom = self.isEdge(x, y)            
                if top:
                    if left:
                        res += '+'
                    else:
                        res += '-'
                    res += '----------'
                    if right:
                        res += '+'
                    else:
                        res += '-'
                else:
                    if left:
                        res += '|'
                    else:
                        res += ' '
                    res += '          '
                    if right:
                        res += '|'
                    else:
                        res += ' '
            res += '\n'
            for x in xrange(0, self.w):
                left, right, top, bottom = self.isEdge(x, y)            
                if left:
                    res += '|'
                else:
                    res += ' '
                if top:
                    if self.cells[y][x]:
                        res += str(self.cells[y][x].content).ljust(10)
                    else:
                        res += str('None').ljust(10)
                else:
                    res += '          '
                if right:
                    res += '|'
                else:
                    res += ' '
            res += '\n'
            for x in xrange(0, self.w):
                left, right, top, bottom = self.isEdge(x, y)            
                if bottom:
                    if left:
                        res += '+'
                    else:
                        res += '-'
                    res += '----------'
                    if right:
                        res += '+'
                    else:
                        res += '-'
                else:
                    if left:
                        res += '|'
                    else:
                        res += ' '
                    res += '          '
                    if right:
                        res += '|'
                    else:
                        res += ' '
            res += '\n'
        return res
