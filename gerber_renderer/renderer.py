import zipfile
import os
import shutil
import svgwrite
from svgwrite import cm, mm, inch


class Gerber:
    def __init__(self, file, verbose=False):
        self.verbose = verbose
        # extracts and sorts a zipped gerber file
        if(self.verbose):
            print('Extracting Files')
        if not os.path.exists('./gerber_files'):
            os.makedirs('./gerber_files')
        else:
            shutil.rmtree('./gerber_files')
        with zipfile.ZipFile(file, 'r') as zipped:
            zipped.extractall('./gerber_files')

        drill = ''
        outline = ''
        t_copper = ''
        t_mask = ''
        t_silk = ''
        b_copper = ''
        b_mask = ''
        b_silk = ''

        # RS274X name schemes
        for filename in os.listdir('./gerber_files'):
            if(not drill and filename[-3:].upper() == 'DRL'):
                drill = './gerber_files/'+filename
            elif(not outline and filename[-3:].upper() == 'GKO'):
                outline = './gerber_files/'+filename
            elif(not t_copper and filename[-3:].upper() == 'GTL'):
                t_copper = './gerber_files/'+filename
            elif(not t_mask and filename[-3:].upper() == 'GTS'):
                t_mask = './gerber_files/'+filename
            elif(not t_silk and filename[-3:].upper() == 'GTO'):
                t_silk = './gerber_files/'+filename
            elif(not b_copper and filename[-3:].upper() == 'GBL'):
                b_copper = './gerber_files/'+filename
            elif(not b_mask and filename[-3:].upper() == 'GBS'):
                b_mask = './gerber_files/'+filename
            elif(not b_silk and filename[-3:].upper() == 'GBO'):
                b_silk = './gerber_files/'+filename

        # render top
        if(drill and outline and t_copper and t_mask):
            if(self.verbose):
                print('Rendring Top')
            self.render_files(outline=outline, drill=drill, copper=t_copper,
                              mask=t_mask, silk=t_silk, filename='top.svg')
        else:
            print('Error identifying files')

        if(drill and outline and b_copper and b_mask):
            if(self.verbose):
                print('Rendering Bottom')
            self.render_files(outline=outline, drill=drill, copper=b_copper,
                              mask=b_mask, silk=b_silk, filename='bottom.svg')
        elif(self.verbose):
            print('No Bottom Files')

    def draw_macros(self, file, color, fill='none'):
        index = 0
        # draw circles
        while(True):
            # get index of circle profile declaration
            index = file.find('%ADD', index+1)
            if(index == -1):
                break
            else:
                # determine if circle or rect
                if(file[index+5] == 'C' or file[index+6] == 'C'):
                    # draw circles
                    radius = str(float(file[file.find(
                        ',', index)+1: file.find('*', index)])/2 * self.scale)

                    c_id = file[index+4:index+6]

                    # find circle centers of profile
                    p_index = file.find('D' + c_id, index + 8)

                    # find and draw all circles for current diameter
                    path = ''
                    while(True):
                        p_index = file.find('G', p_index+1)
                        if(file[p_index: p_index+3] != 'G01'):
                            p_index = file.find('D' + c_id, p_index)
                            if(p_index == -1):
                                break
                        x = file.find('X', p_index)
                        y = file.find('Y', x)
                        x = str(float(file[x+1:y])/1000*self.scale)
                        y = str(
                            float(file[y+1:file.find('D', y)])/1000*self.scale)
                        if(file[file.find('D', p_index):file.find('D', p_index)+3] == 'D02'):
                            path += 'M' + x + ',' + str(float(y))
                        elif (file[file.find('D', p_index):file.find('D', p_index)+3] == 'D01'):
                            path += 'L' + x + ',' + str(float(y))

                        self.drawing.add(self.drawing.circle(center=(x, y),
                                                             r=radius, fill=color))
                    if(path):
                        self.drawing.add(self.drawing.path(d=path, stroke=color,
                                                           stroke_width=float(radius)*2, fill=fill))
                    # draw rectangles
                else:
                    r_width = str(float(file[file.find(
                        ',', index)+1: file.find('X', index)]) * self.scale)
                    r_height = str(float(file[file.find(
                        'X', index)+1: file.find('*', index)]) * self.scale)
                    r_id = file[index+4:index+6]

                    # findrect coords of profile
                    p_index = file.find('D' + r_id, index + 8)

                    while(True):
                        p_index = file.find('G', p_index+1)
                        if(file[p_index: p_index+3] != 'G01'):
                            p_index = file.find('D' + r_id, p_index)
                            if(p_index == -1):
                                break
                        # find X and Y coords of top left
                        left_x = file.find('X', p_index)
                        top_y = file.find('Y', p_index)

                        left_x = str(
                            float(file[left_x+1:top_y])/1000*self.scale-float(r_width)/2)

                        top_y = str(
                            float(file[top_y+1: file.find('D', top_y+1)])/1000*self.scale-float(r_height)/2)

                        # draw rect
                        self.drawing.add(self.drawing.rect(insert=(left_x, top_y), size=(
                            r_width, r_height), fill=color))
            self.drawing.save()

    def area_fill(self, file, color):
        index = 0
        while(True):
            # get index of area fill instructions
            index = file.find('G36', index+1)
            if(index == -1):
                break
            else:
                # find all coords and draw path
                path = ''
                while(True):
                    index = file.find('G', index+1)
                    if(file[index: index+3] != 'G01'):
                        break
                    x = file.find('X', index)
                    y = file.find('Y', x)
                    x = str(float(file[x+1:y])/1000*self.scale)
                    y = str(
                        float(file[y+1:file.find('D', y)])/1000*self.scale)
                    if(file[file.find('D', index):file.find('D', index)+3] == 'D02'):
                        path += 'M' + x + ',' + str(float(y))
                    else:
                        path += 'L' + x + ',' + str(float(y))

                self.drawing.add(self.drawing.path(
                    d=path, stroke='none', fill=color))
            self.drawing.save()

    def render_files(self, outline, drill, copper, mask, silk='', filename='pcb.svg'):
        # initialize svg
        self.drawing = svgwrite.Drawing(
            filename='./gerber_files/'+filename, debug=True)

        # open outline file
        outline_file = open(outline, 'r').read()

        # set units
        unit = 'mm'
        self.scale = 3.543307
        if(outline_file.find('G70') != -1):
            unit = 'in'
            self.scale = 90

        # get board dimensions
        # get width
        self.width = 0
        pointer = outline_file.find('G01X')+3
        while(pointer != -1):
            temp = float(
                outline_file[pointer+1: outline_file.find('Y', pointer)])/1000
            if(temp > self.width):
                self.width = temp
            pointer = outline_file.find('X', pointer+1)
        # get height
        self.height = 0
        pointer = outline_file.find('Y', outline_file.find('G01X'))
        while(pointer != -1):
            y_len = 1
            while(str.isnumeric(outline_file[pointer+1+y_len])):
                y_len += 1

            temp = float(outline_file[pointer+1: pointer+1+y_len])/1000
            if(temp > self.height):
                self.height = temp
            pointer = outline_file.find('Y', pointer+1)
        if(self.verbose):
            print('Board Dimensions: ' + str(self.width) +
                  ' x ' + str(self.height) + ' ' + str(unit))

        # draw background rectangle
        self.drawing.add(self.drawing.rect(insert=(0, 0), size=(
            str(self.width*self.scale), str(self.height*self.scale)), fill='green'))

        # open copper file
        copper_file = open(copper, 'r').read()

        # draw copper layer
        if(self.verbose):
            print('Etching Copper')
        self.draw_macros(file=copper_file,
                         color='darkgreen')

        # open top solder mask file
        mask_file = open(mask, 'r').read()

        # draw top solder mask
        if(self.verbose):
            print('Applying Solder Mask')

        self.area_fill(file=mask_file,  color='grey')
        self.draw_macros(file=mask_file,  color='grey')

        if(silk):
            # open top silk screen file
            silk_file = open(silk, 'r').read()

            # draw top silk screen
            if(self.verbose):
                print('Curing Silk Screen')
            # draw silkscreen with macros
            self.draw_macros(file=silk_file,
                             color='white')
            self.area_fill(file=silk_file,
                           color='white')

        # open drill file
        drill_file = open(drill, 'r').read()

        # draw drill holes
        if(self.verbose):
            print('Drilling Holes')
        tool_num = 1
        while(True):
            # get diameter index of current tool
            diameter = drill_file.find('T0'+str(tool_num)+'C')
            if(diameter == -1):
                break
            else:
                # draw all holes for current tool
                curr_holes = drill_file.find('T0'+str(tool_num), diameter+4)+3
                # get diameter of current tool
                d_len = 0
                while(str.isnumeric(drill_file[diameter+4+d_len]) or drill_file[diameter+4+d_len] == '.'):
                    d_len += 1
                diameter = float(drill_file[diameter+4: diameter+4+d_len])

                next_tool = drill_file.find('T', curr_holes)
                curr_x = drill_file.find('X', curr_holes)
                curr_y = drill_file.find('Y', curr_x)

                # find and draw circles at hole coords
                while(curr_x < next_tool or (next_tool == -1 and curr_x != -1)):
                    y_len = 1
                    while(str.isnumeric(drill_file[curr_y+1+y_len])):
                        y_len += 1
                    hole_x = float(drill_file[curr_x+1:curr_y])/1000
                    hole_y = float(drill_file[curr_y+1: curr_y+1+y_len])/1000
                    self.drawing.add(self.drawing.circle(center=(str(hole_x*self.scale), str(hole_y*self.scale)),
                                                         r=str(diameter/2*self.scale), fill='black'))
                    curr_x = drill_file.find('X', curr_y)
                    curr_y = drill_file.find('Y', curr_x)

                tool_num += 1
        self.drawing.save()

    def get_dimensions(self):
        if(self.width):
            return [self.width, self.height]
        else:
            return 'Board Not Rendered'
