import math
import zipfile
import os
import shutil
import svgwrite
from svgwrite import cm, mm, inch
from svglib.svglib import svg2rlg
from reportlab.graphics import renderPDF


class Board:
    def __init__(self, file, max_height=500, verbose=False):
        self.max_height = max_height
        self.verbose = verbose
        self.temp_path = './temp_gerber_files'

        if(self.verbose):
            print('Extracting Files')
        if not os.path.exists(self.temp_path):
            os.makedirs(self.temp_path)
        with zipfile.ZipFile(file, 'r') as zipped:
            zipped.extractall(self.temp_path)

        self.files = {}
        self.files['drill'] = ''
        self.files['outline'] = ''
        self.files['top_copper'] = ''
        self.files['top_mask'] = ''
        self.files['top_silk'] = ''
        self.files['bottom_copper'] = ''
        self.files['bottom_mask'] = ''
        self.files['bottom_silk'] = ''

        # RS274X name schemes
        for filename in os.listdir(self.temp_path):
            if(not self.files['drill'] and filename[-3:].upper() == 'DRL'):
                self.files['drill'] = self.open_file(filename)
            elif(not self.files['outline'] and filename[-3:].upper() == 'GKO'):
                self.files['outline'] = self.open_file(filename)
            elif(not self.files['top_copper'] and filename[-3:].upper() == 'GTL'):
                self.files['top_copper'] = self.open_file(filename)
            elif(not self.files['top_mask'] and filename[-3:].upper() == 'GTS'):
                self.files['top_mask'] = self.open_file(filename)
            elif(not self.files['top_silk'] and filename[-3:].upper() == 'GTO'):
                self.files['top_silk'] = self.open_file(filename)
            elif(not self.files['bottom_copper'] and filename[-3:].upper() == 'GBL'):
                self.files['bottom_copper'] = self.open_file(filename)
            elif(not self.files['bottom_mask'] and filename[-3:].upper() == 'GBS'):
                self.files['bottom_mask'] = self.open_file(filename)
            elif(not self.files['bottom_silk'] and filename[-3:].upper() == 'GBO'):
                self.files['bottom_silk'] = self.open_file(filename)

        shutil.rmtree(self.temp_path)

        if(self.files['drill'] and self.files['outline'] and self.files['top_copper'] and self.files['top_mask']):
            if(self.verbose):
                print('Files Loaded')
        else:
            print('Error identifying files')

    def render(self, output):
        self.output_folder = output
        if(self.output_folder[-1] == '/'):
            self.output_folder = self.output_folder[:-1]
        if not os.path.exists(self.output_folder):
            os.makedirs(self.output_folder)
        self.output_folder += '/'

        # render top
        if(self.files['drill'] and self.files['outline'] and self.files['top_copper'] and self.files['top_mask']):
            if(self.verbose):
                print('Rendring Top')
            self.draw_svg(layer='top', filename='top.svg')
        else:
            print('Error identifying files')

        # render bottom
        if(self.files['drill'] and self.files['outline'] and self.files['bottom_copper'] and self.files['bottom_mask']):
            if(self.verbose):
                print('Rendering Bottom')
            self.draw_svg(layer='bottom', filename='bottom.svg')
        elif(self.verbose):
            print('No Bottom Files')

    def draw_svg(self, layer, filename):
        self.set_dimensions()

        self.scale = self.max_height/self.height

        # initialize svg
        self.drawing = svgwrite.Drawing(
            filename=self.output_folder+filename, size=(self.width*self.scale, self.height*self.scale), debug=False)

        # draw background rectangle
        self.drawing.add(self.drawing.rect(insert=(0, 0), size=(
            str(self.width*self.scale), str(self.height*self.scale)), fill='green'))

        # draw copper layer
        if(self.verbose):
            print('Etching Copper')
        self.setDecimalPlaces(self.files[layer+'_copper'])
        self.draw_macros(file=self.files[layer+'_copper'],
                         color='darkgreen')
        self.area_fill(file=self.files[layer+'_copper'],  color='darkgreen')
        self.draw_arcs(file=self.files[layer+'_copper'],  color='darkgreen')

        # draw solder mask
        if(self.verbose):
            print('Applying Solder Mask')
        self.setDecimalPlaces(self.files[layer+'_mask'])
        self.area_fill(file=self.files[layer+'_mask'],  color='grey')
        self.draw_macros(file=self.files[layer+'_mask'],  color='grey')
        self.draw_arcs(file=self.files[layer+'_mask'],  color='grey')

        if(self.files[layer+'_silk']):
            # draw silk screen
            if(self.verbose):
                print('Curing Silk Screen')
            # draw silkscreen with macros
            self.setDecimalPlaces(self.files[layer+'_silk'])
            self.draw_macros(file=self.files[layer+'_silk'],
                             color='white')
            self.area_fill(file=self.files[layer+'_silk'],
                           color='white')
            self.draw_arcs(file=self.files[layer+'_silk'],
                           color='white')

        # draw drill holes
        if(self.verbose):
            print('Drilling Holes')
        self.drill_holes()

        self.drawing.save()

    def render_pdf(self, output, layer='top_copper', color='white'):
        self.set_dimensions()

        self.scale = self.max_height/self.height

        self.output_folder = output
        if(self.output_folder[-1] == '/'):
            self.output_folder = self.output_folder[:-1]
        if not os.path.exists(self.output_folder):
            os.makedirs(self.output_folder)
        self.output_folder += '/'

        # initialize svg
        self.drawing = svgwrite.Drawing(
            filename=self.output_folder+layer+'.svg', size=(self.width*self.scale, self.height*self.scale), debug=False)

        # draw background rectangle
        self.drawing.add(self.drawing.rect(insert=(0, 0), size=(
            str(self.width*self.scale), str(self.height*self.scale)), fill='black' if color == 'white' else 'white'))

        # draw copper layer
        self.draw_macros(file=self.files[layer],
                         color=color)
        self.area_fill(file=self.files[layer],
                       color=color)

        self.drawing.save()

        # drawing = svg2rlg(self.output_folder+layer+".svg")
        # renderPDF.drawToFile(drawing, self.output_folder+layer+".pdf")

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
                        x = str(float(file[x+1:y])/self.x_decimals*self.scale)
                        y = str(
                            float(file[y+1:file.find('D', y)])/self.y_decimals*self.scale)
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
                            float(file[left_x+1:top_y])/self.x_decimals*self.scale-float(r_width)/2)

                        top_y = str(
                            float(file[top_y+1: file.find('D', top_y+1)])/self.y_decimals*self.scale-float(r_height)/2)

                        # draw rect
                        self.drawing.add(self.drawing.rect(insert=(left_x, top_y), size=(
                            r_width, r_height), fill=color))

    def draw_arcs(self, file, color):
        index = 0
        single_quadrant_done = False
        large_arc_flag = 0
        while(True):
            if(not single_quadrant_done):
                index = file.find('G74', index+1)
            else:
                index = file.find('G75', index+1)
            if(index == -1):
                if(single_quadrant_done):
                    break
                else:
                    single_quadrant_done = True
                    large_arc_flag = 1
                    index = index = file.find('G75', index+1)
            else:
                # find all coords and draw path
                path = ''
                while(True):
                    index = file.find('G', index+1)
                    if(file[index: index+3] == 'G01'):
                        x = file.find('X', index)
                        y = file.find('Y', x)
                        x = str(float(file[x+1:y])/self.x_decimals*self.scale)
                        y = str(
                            float(file[y+1:file.find('D', y)])/self.y_decimals*self.scale)
                        path += 'M' + x + ',' + str(float(y))
                    elif(file[index: index+3] == 'G02' or file[index: index+3] == 'G03'):
                        path += self.draw_arc(
                            file[index:file.find('*', index)], large_arc_flag)
                    else:
                        break
                self.drawing.add(self.drawing.path(
                    d=path, stroke=color, fill='none'))

    def draw_arc(self, g_code, large_arc_flag):
        y_loc = g_code.find('Y')
        i_loc = g_code.find('I')
        d_loc = g_code.find('D')
        x = float(g_code[4:y_loc])/self.x_decimals*self.scale
        y = float(g_code[y_loc+1:i_loc])/self.y_decimals*self.scale
        i = 0
        j = 0

        if(g_code.find('J') != -1):
            j = float(g_code[g_code.find('J')+1:d_loc]) / \
                self.x_decimals*self.scale
            print(g_code[g_code.find('J')+1:d_loc])
            d_loc = g_code.find('J')

        i = float(g_code[i_loc+1:d_loc])/self.x_decimals*self.scale

        radius = math.sqrt(i**2 + j**2)

        return('A '+str(radius)+' '+str(radius) +
               ' 0 '+str(large_arc_flag) + ' 1 ' + str(x) + ' ' + str(y))

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
                        if(file[index: index+3] == 'G02' or file[index: index+3] == 'G03'):
                            self.draw_arc(file[index:file.find('*', index)])
                        break
                    x = file.find('X', index)
                    y = file.find('Y', x)
                    x = str(float(file[x+1:y])/self.x_decimals*self.scale)
                    y = str(
                        float(file[y+1:file.find('D', y)])/self.y_decimals*self.scale)
                    if(file[file.find('D', index):file.find('D', index)+3] == 'D02'):
                        path += 'M' + x + ',' + str(float(y))
                    else:
                        path += 'L' + x + ',' + str(float(y))

                self.drawing.add(self.drawing.path(
                    d=path, stroke='none', fill=color))

    def drill_holes(self):
        tool_num = 1
        while(True):
            # get diameter index of current tool
            diameter = self.files['drill'].find('T0'+str(tool_num)+'C')
            if(diameter == -1):
                break
            else:
                # draw all holes for current tool
                curr_holes = self.files['drill'].find(
                    'T0'+str(tool_num), diameter+4)+3
                # get diameter of current tool
                d_len = 0
                while(str.isnumeric(self.files['drill'][diameter+4+d_len]) or self.files['drill'][diameter+4+d_len] == '.'):
                    d_len += 1
                diameter = float(self.files['drill']
                                 [diameter+4: diameter+4+d_len])

                next_tool = self.files['drill'].find('T', curr_holes)
                curr_x = self.files['drill'].find('X', curr_holes)
                curr_y = self.files['drill'].find('Y', curr_x)

                # find and draw circles at hole coords
                while(curr_x < next_tool or (next_tool == -1 and curr_x != -1)):
                    y_len = 1
                    while(str.isnumeric(self.files['drill'][curr_y+1+y_len])):
                        y_len += 1
                    hole_x = float(self.files['drill']
                                   [curr_x+1:curr_y])/self.x_decimals
                    hole_y = float(self.files['drill']
                                   [curr_y+1: curr_y+1+y_len])/self.y_decimals
                    self.drawing.add(self.drawing.circle(center=(str(hole_x*self.scale), str(hole_y*self.scale)),
                                                         r=str(diameter/2*self.scale), fill='black'))
                    curr_x = self.files['drill'].find('X', curr_y)
                    curr_y = self.files['drill'].find('Y', curr_x)

                tool_num += 1

    def setDecimalPlaces(self, file):
        index = file.find('FSLAX')
        self.x_decimals = int(file[index+6:index+7])
        self.y_decimals = int(file[index+9:index+10])
        temp = '1'
        for i in range(self.x_decimals):
            temp += '0'
        self.x_decimals = int(temp)
        temp = '1'
        for i in range(self.y_decimals):
            temp += '0'
        self.y_decimals = int(temp)

    def set_dimensions(self):
        self.setDecimalPlaces(self.files['outline'])
        self.width = 0
        pointer = self.files['outline'].find('D10')
        pointer = self.files['outline'].find('X', pointer)
        while(pointer != -1):
            temp = float(
                self.files['outline'][pointer+1: self.files['outline'].find('Y', pointer)])/self.x_decimals
            if(temp > self.width):
                self.width = temp
            pointer = self.files['outline'].find('X', pointer+1)

        self.height = 0
        pointer = self.files['outline'].find(
            'Y', self.files['outline'].find('X'))
        while(pointer != -1):
            y_len = 1
            while(str.isnumeric(self.files['outline'][pointer+1+y_len])):
                y_len += 1

            temp = float(self.files['outline']
                         [pointer+1: pointer+1+y_len])/self.y_decimals
            if(temp > self.height):
                self.height = temp
            pointer = self.files['outline'].find('Y', pointer+1)

        unit = 'mm'
        if(self.files['outline'].find('MOIN') != -1):
            unit = 'in'

        if(self.verbose):
            print('Board Dimensions: ' + str(self.width) +
                  ' x ' + str(self.height) + ' ' + str(unit))

    def get_dimensions(self):
        if(self.width):
            return [self.width, self.height, self.scale]
        else:
            return 'Board Not Rendered'

    def open_file(self, filename):
        return open(self.temp_path+'/'+filename, 'r').read()
