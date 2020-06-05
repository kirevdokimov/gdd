#!/usr/bin/env python3

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.

import curses
import subprocess

class unit:
    def __init__(self, initialstate, name):
        self.initiallyMarked = initialstate
        self.marked = initialstate
        self.name = name

def main(scr):

    # units view shift
    shift = 0
    mincursory = 0
    maxcursory = 0
    # vertical position of cursor
    cursory = 0

    prefixgap = 6

    def renderUnits(units, height, shift):
        i = 0
        #iterate over units that should be visible
        for u in units[shift:shift+height]:
            scr.addstr(i, 0, ("[ ]", "[x]")[u.marked])
            scr.addstr(i, prefixgap, u.name)
            i+=1
    
    def getUnitUnderCursor(cursory, units):
        return units[cursory+shift]

    def prefixToMark(prefix):
        return prefix == "A " or prefix == "M "

    def lineToUnit(line):
        return unit(initialstate=prefixToMark(line[:2]), name=line[3:])

    scr.erase()
    scr.refresh()

    # get list of changed units
    output = subprocess.check_output(["git", "status", "--porcelain=v1", "--untracked-files=all"]).decode()
    splitoutput = output.split("\n")[:-1] # last item is empty string for some reason
    units = list(map(lineToUnit, splitoutput))

    height, _ = scr.getmaxyx()
    maxcursory = height - 1
    renderUnits(units, height, shift)
    
    # just variable to store latest input characted from terminal
    k = 0

    while (k != ord('q')):

        height, _ = scr.getmaxyx()
        maxcursory = height - 1
        
        # flag of repaint request
        # I use repaint just to redraw whole list of units. Cursor do
        # redraw every iteration anyway, it is cheaper than redraw
        # everything just because of cursor movement or mark
        dirty = False

        # erase cursor because it can change position in code below.
        # It can probably stay, but and I don't want to store current
        # position to be able to erase when cursory changes
        scr.addstr(cursory, 4, " ")

        if k == curses.KEY_DOWN:
            reachscredge = cursory + 1 > maxcursory
            reachunitsedge = cursory + 1 > len(units) - 1 - shift

            if not reachunitsedge:
                if reachscredge:
                    # scroll down, mark to repaint
                    shift += 1
                    dirty = True
                else:
                    # move cursor down if screen edge is not reached
                    cursory += 1

        elif k == curses.KEY_UP:
            reachscredge = cursory -1 < mincursory

            if reachscredge:
                # scroll up if possible, mark to repaint
                if shift != 0:
                    shift -= 1
                    dirty = True
            else:
                # move cursor up if screen edge is not reached
                cursory -= 1

        elif k == ord(' '):
            u = getUnitUnderCursor(cursory, units)
            u.marked = not u.marked
            # mark redraw is consistent. list reapaint is not required
            scr.addstr(cursory, 1, (" ", "x")[u.marked])
            
        elif k == curses.KEY_ENTER or k == 10:
            namestoadd = []
            add = False
            namestoreset = []
            reset = False
            for u in units:
                if u.initiallyMarked == u.marked:
                    continue
                elif u.marked:
                    namestoadd.append(u.name)
                    add = True
                else:
                    namestoreset.append(u.name)
                    reset = True
            # TODO: Do something when resultcode is not 0 
            if add:
                resultcode = subprocess.call(["git", "add"] + namestoadd)
            if reset:
                resultcode = subprocess.call(["git", "reset"] + namestoreset)
            break

        if dirty:
            scr.erase()
            renderUnits(units, height, shift)
            dirty = False

        # draw cursor
        scr.addstr(cursory, 4, "<")
        # move caret to cursor just because it should be placed somewhere
        scr.move(cursory, 4)

        scr.refresh()

        k = scr.getch()
        

if __name__ == "__main__":
    curses.wrapper(main)