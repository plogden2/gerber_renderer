import math
import zipfile
import os
import re
import shutil
import svgwrite
from svgwrite import cm, mm, inch
from svglib.svglib import svg2rlg
import reportlab.graphics as graphics
from reportlab.graphics import renderPDF


class Board:
    def __init__(self, file, max_height=500, verbose=False):
        self.width = False
        self.max_height = max_height
        self.verbose = verbose
        self.temp_path = './temp_gerber_files'

        if not os.path.exists(self.temp_path):
            os.makedirs(self.temp_path)

        if(file[-3:].upper() == 'ZIP'):
            self.extract_files(file)
        else:
            self.copy_files(file)

        self.identify_files()

    def render(self, output):
        #setup output path
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
            print('No Top Files')

        # render bottom
        if(self.files['drill'] and self.files['outline'] and self.files['bottom_copper'] and self.files['bottom_mask']):
            if(self.verbose):
                print('Rendering Bottom')
            self.draw_svg(layer='bottom', filename='bottom.svg')
        elif(self.verbose):
            print('No Bottom Files')

    def draw_svg(self, layer, filename):
        if(not self.width):
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
        self.init_file(self.files[layer+'_copper'])
        self.area_fill(file=self.files[layer+'_copper'],
                         color='darkgreen')
        self.draw_macros(file=self.files[layer+'_copper'],
                         color='darkgreen')

        # draw solder mask
        if(self.verbose):
            print('Applying Solder Mask')
        self.init_file(self.files[layer+'_mask'])
        # self.draw_macros(file=self.files[layer+'_mask'],  color='grey')

        # if(self.files[layer+'_silk']):
        #     # draw silk screen
        #     if(self.verbose):
        #         print('Curing Silk Screen')
        #     self.init_file(self.files[layer+'_silk'])
        # self.draw_macros(file=self.files[layer+'_silk'],
        #                  color='white')

        # draw drill holes
        if(self.verbose):
            print('Drilling Holes')
        self.drill_holes()

        self.drawing.save()

    # scale compensation +0.05 = 5% bigger
    def render_pdf(self, output, layer='top_copper', color='white', scale_compensation=0.0, full_page=True, mirrored=False, offset=(0,0)):
        #setup output path
        self.output_folder = output
        if(self.output_folder[-1] == '/'):
            self.output_folder = self.output_folder[:-1]
        if not os.path.exists(self.output_folder):
            os.makedirs(self.output_folder)
        self.output_folder += '/'

        if(not self.width):
            self.set_dimensions()

        self.scale = 3.543307 if self.unit == 'mm' else 90
        self.scale *= (1+scale_compensation)

        # initialize svg
        self.drawing = svgwrite.Drawing(
            filename=self.output_folder+layer+'.svg', size=(self.width*self.scale, self.height*self.scale), debug=False)

        # draw background rectangle
        self.drawing.add(self.drawing.rect(insert=(0, 0), size=(
            str(self.width*self.scale), str(self.height*self.scale)), fill='black' if color == 'white' else 'white'))

        # draw layer
        self.init_file(self.files[layer])
        self.draw_macros(file=self.files[layer],
                         color=color)

        self.drawing.save() 

        #convert svg drawing to pdf
        drawing = svg2rlg(self.output_folder+layer+".svg")
        if(mirrored):
            drawing.scale(-1, 1)
            drawing.translate(float(drawing.getBounds()[0]), 0)
        drawing.translate(offset[0], offset[1])
        renderPDF.drawToFile(drawing, self.output_folder +
                             layer+".pdf", autoSize=int(not full_page))
        os.remove(self.output_folder+layer+".svg")

    def draw_arcs(self, g_code, color, radius):
        index = 0
        # find all coords and draw path
        path = ''
        while(True):
            index = g_code.find('G', index+1)
            if(g_code[index: index+3] == 'G01'):
                x = g_code.find('X', index)
                y = g_code.find('Y', x)
                x = str(
                    ((abs(float(g_code[x+1:y]))/self.x_decimals)-self.min_x)*self.scale)
                y = str(((abs(
                    float(g_code[y+1:g_code.find('D', y)]))/self.y_decimals)-self.min_y)*self.scale)
                path += 'M' + x + ',' + str(float(y))
            elif(g_code[index: index+3] == 'G02' or g_code[index: index+3] == 'G03'):
                if(g_code[index: index+3] == 'G02'):
                    sweep_flag = '0'
                else:
                    sweep_flag = '1'
                path += self.draw_arc(
                    g_code[index:g_code.find('*', index)], sweep_flag, start_pos=(x, y))
            else:
                break
        self.drawing.add(self.drawing.path(
            d=path, stroke=color, stroke_width=radius*2, fill='none'))

    def draw_arc(self, g_code, sweep_flag, start_pos, multiquadrant_bool=True):
        y_loc = g_code.find('Y')
        i_loc = g_code.find('I')
        d_loc = g_code.find('D')
        x = ((abs(float(g_code[4:y_loc])) /
              self.x_decimals)-self.min_x)*self.scale
        i = 0
        j = 0

        if(g_code.find('J') != -1):
            j = float(g_code[g_code.find('J')+1:d_loc]) / \
                self.y_decimals*self.scale
            d_loc = g_code.find('J')

        if(i_loc != -1):
            y = ((abs(float(g_code[y_loc+1:i_loc])) /
                  self.y_decimals)-self.min_y)*self.scale
            i = float(g_code[g_code.find('I')+1:d_loc]) / \
                self.x_decimals*self.scale
        else:
            y = ((abs(float(g_code[y_loc+1:d_loc])) /
                  self.y_decimals)-self.min_y)*self.scale

        center = (float(start_pos[0])+i, float(start_pos[1])+j)

        start_angle = self.find_angle(start_pos, center)
        end_angle = self.find_angle((x, y), center)
        if(sweep_flag == '0'):
            angle = (start_angle-end_angle)
        else:
            angle = (end_angle-start_angle)

        if(not multiquadrant_bool and angle > 0.5):
            if(sweep_flag == '0'):
                angle = (end_angle-start_angle)
            else:
                angle = (start_angle-end_angle)

        if((angle) >= 1):
            large_arc_flag = 1
        else:
            large_arc_flag = 0

        radius = math.sqrt(i**2 + j**2)

        return('A '+str(radius)+' '+str(radius) +
               ' 0 '+str(large_arc_flag) + ' ' + sweep_flag + ' ' + str(x) + ' ' + str(y))

    def find_angle(self, pos, center):
        y = float(pos[1]) - float(center[1])
        x = float(pos[0]) - float(center[0])
        angle = math.atan2(y, x)
        angle /= math.pi
        if(angle < 0):
            angle += 2
        return angle

    def polygon_fill(self, g_code, color, radius):
        g_loc = 0
        x_loc = 0
        # find all coords and draw path
        path = ''
        g_loc = g_code.find('G')
        while(True):
            if(g_loc == -1):
                break
            code = g_code[g_loc:g_loc+3]
            next_code = g_code.find('G', g_loc+1)
            x_loc = g_code.find('X', g_loc+1)
            while((x_loc < next_code and x_loc != -1) or (next_code == -1 and x_loc != -1)):
                y_loc = g_code.find('Y', x_loc)
                if(code == 'G01'):
                    x = str(((abs(float(g_code[x_loc+1:y_loc]
                                        ))/self.x_decimals)-self.min_x)*self.scale)
                    y = str(
                        ((abs(float(g_code[y_loc+1:g_code.find('D', y_loc)]))/self.y_decimals)-self.min_y)*self.scale)
                    if(g_code[g_code.find('D', x_loc):g_code.find('D', x_loc)+3] == 'D02' or path == ''):
                        path += 'M' + x + ',' + str(float(y))
                    elif (g_code[g_code.find('D', x_loc):g_code.find('D', x_loc)+3] == 'D01'):
                        path += 'L' + x + ',' + str(float(y))
                elif(code == 'G02' or code == 'G03'):
                    sweep_flag = '1'
                    path += self.draw_arc(
                        g_code[x_loc-3:g_code.find('*', x_loc)], sweep_flag, start_pos=(x, y))

                x_loc = g_code.find('X', x_loc+1)
            g_loc = next_code
        path += ' Z'
        self.drawing.add(self.drawing.path(
            d=path, stroke='none', fill=color))

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

                    x = str(
                        ((abs(float(file[x+1:y]))/self.x_decimals)-self.min_x)*self.scale)
                    y = str(
                        ((abs(float(file[y+1:file.find('D', y)]))/self.y_decimals)-self.min_y)*self.scale)
                    if(file[file.find('D', index):file.find('D', index)+3] == 'D02'):
                        path += 'M' + x + ',' + y
                    else:
                        path += 'L' + x + ',' + y

                self.drawing.add(self.drawing.path(
                    d=path, stroke='black', stroke_width=10, fill=color))

    def drill_holes(self):
        tool_num = 1
        leading_zero = True
        while(True):
            # get diameter index of current tool
            diameter = self.files['drill'].find('T0'+str(tool_num)+'C')
            if(diameter == -1 and self.files['drill'].find('T'+str(tool_num)+'C') == -1):
                break
            else:
                if(diameter == -1):
                    leading_zero = False
                    diameter = self.files['drill'].find('T'+str(tool_num)+'C')
                # draw all holes for current tool
                curr_holes = self.files['drill'].find(
                    'T'+('0' if leading_zero else '')+str(tool_num), diameter+4)+3
                # get diameter of current tool
                d_len = 0
                increment = (4 if leading_zero else 3)
                while(str.isnumeric(self.files['drill'][diameter+increment+d_len]) or self.files['drill'][diameter+increment+d_len] == '.'):
                    d_len += 1
                diameter = float(self.files['drill']
                                 [diameter+increment: diameter+increment+d_len])

                next_tool = self.files['drill'].find(
                    'T'+('0' if leading_zero else '')+str(tool_num+1), curr_holes)
                curr_x = self.files['drill'].find('X', curr_holes)
                curr_y = self.files['drill'].find('Y', curr_x)

                # find and draw circles at hole coords
                while(curr_x < next_tool or (next_tool == -1 and curr_x != -1)):
                    y_len = 1
                    while(str.isnumeric(self.files['drill'][curr_y+1+y_len]) or self.files['drill'][curr_y+1+y_len] == '.' or self.files['drill'][curr_y+1+y_len] == '-'):
                        y_len += 1
                    hole_x = (abs(float(self.files['drill']
                                        [curr_x+1:curr_y]))-self.min_x)/(self.x_decimals if (self.files['drill'][curr_x+1:curr_y]).find('.') == -1 else 1)
                    hole_y = (abs(float(self.files['drill']
                                        [curr_y+1: curr_y+1+y_len]))-self.min_y)/(self.y_decimals if (self.files['drill'][curr_y+1: curr_y+1+y_len]).find('.') == -1 else 1)
                    self.drawing.add(self.drawing.circle(center=(str(hole_x*self.scale), str(hole_y*self.scale)),
                                                         r=str(diameter/2*self.scale), fill='black'))
                    curr_x = self.files['drill'].find('X', curr_y)
                    curr_y = self.files['drill'].find('Y', curr_x)

                tool_num += 1

    def draw_macros(self, file, color, fill='none'):
        arc_starts = list(self.arcs.keys())
        arc_starts.sort()
        polygon_starts = list(self.polygons.keys())
        polygon_starts.sort()

        for macro in self.aperture_locs:
            # draw all polygons within macro
            while(len(polygon_starts) != 0):
                if(int(polygon_starts[0]) >= int(macro[1]) and int(self.polygons[polygon_starts[0]]) <= int(macro[2])):
                    self.polygon_fill(
                        file[int(polygon_starts[0]):int(self.polygons[polygon_starts[0]])], color, float(self.apertures[macro[0]][1]))
                    del polygon_starts[0]
                else:
                    break
            # draw all arcs within macro
                # while(len(arc_starts) != 0):
                #     # print('woo')
                #     if(int(arc_starts[0]) >= int(macro[1]) and int(self.arcs[arc_starts[0]]) <= int(macro[2])):
                #         self.draw_arcs(
                #             file[int(arc_starts[0]):int(self.arcs[arc_starts[0]])], color, float(self.apertures[macro[0]][1]))
                #         del arc_starts[0]
                #     else:
                #         break
            if(self.apertures[macro[0]][0] == 'C'):
                # draw circle apertures
                path = ''

                # find first x
                index = file.find('X', macro[1])

                while(index < macro[2] and index != -1):
                    y_loc = file.find('Y', index)
                    if(file[y_loc+1:file.find('D', y_loc)].find('J') == -1 and file[y_loc+1:file.find('D', y_loc)].find('I') == -1):
                        x = str(((abs(float(file[index+1:y_loc]
                                            ))/self.x_decimals)-self.min_x)*self.scale)
                        y = str(
                            ((abs(float(file[y_loc+1:file.find('D', y_loc)]))/self.y_decimals)-self.min_y)*self.scale)
                        if(file[file.find('D', index):file.find('D', index)+3] == 'D02'):
                            path += 'M' + x + ',' + str(float(y))
                        elif (file[file.find('D', index):file.find('D', index)+3] == 'D01'):
                            path += 'L' + x + ',' + str(float(y))

                        self.drawing.add(self.drawing.circle(center=(x, y),
                                                             r=self.apertures[macro[0]][1], fill=color))
                    index = file.find('X', index+1)

                if(path):
                    self.drawing.add(self.drawing.path(d=path, stroke=color,
                                                       stroke_width=float(self.apertures[macro[0]][1])*2, fill=fill))

            elif(self.apertures[macro[0]][0] == 'O'):
                # draw obround apertures
                path = ''

                # find first x
                index = file.find('X', macro[1])

                while(index < macro[2] and index != -1):
                    y_loc = file.find('Y', index)
                    if(file[y_loc+1:file.find('D', y_loc)].find('J') == -1 and file[y_loc+1:file.find('D', y_loc)].find('I') == -1):
                        x = str(((abs(float(file[index+1:y_loc]
                                            ))/self.x_decimals)-self.min_x)*self.scale)
                        y = str(
                            ((abs(float(file[y_loc+1:file.find('D', y_loc)]))/self.y_decimals)-self.min_y)*self.scale)
                        if(file[file.find('D', index):file.find('D', index)+3] == 'D02'):
                            path += 'M' + x + ',' + str(float(y))
                        elif (file[file.find('D', index):file.find('D', index)+3] == 'D01'):
                            path += 'L' + x + ',' + str(float(y))

                        self.drawing.add(self.drawing.ellipse(center=(x, y),
                                                              r=(str(float(self.apertures[macro[0]][1])/2), str(float(self.apertures[macro[0]][2])/2)), fill=color))
                    index = file.find('X', index+1)

                if(path):
                    self.drawing.add(self.drawing.path(d=path, stroke=color,
                                                       stroke_width=float(self.apertures[macro[0]][1])*2, fill=fill))

            # draw rectangular apertures
            elif(self.apertures[macro[0]][0] == 'R'):
                g_loc = file.find('G', macro[1])
                if(g_loc == -1):
                    g_loc = macro[2]
                index = file.find('X', macro[1])
                while(index < g_loc and index != -1):
                    y = file.find('Y', index)
                    if(file[y+1:file.find('D', y)].find('J') == -1 and file[y+1:file.find('D', y)].find('I') == -1):
                        width = float(self.apertures[macro[0]][1])
                        height = float(self.apertures[macro[0]][2])

                        x = str(
                            ((abs(float(file[index+1:y]))/self.x_decimals)-self.min_x)*self.scale-float(width)/2)

                        y = str(
                            ((abs(float(file[y+1: file.find('D', y+1)]))/self.y_decimals)-self.min_y)*self.scale-float(height)/2)

                        # draw rect
                        self.drawing.add(self.drawing.rect(insert=(x, y), size=(
                            width, height), fill=color))
                        index = file.find('X', index+1)

    def store_polygons(self, file):
        self.polygons = {}
        # store all polygons start_location: end location
        for i in self.find_all_groups(file, 'G36', 'G37'):
            self.polygons[i[0]] = i[1]

    def store_arcs(self, file):
        self.arcs = {}
        # store all arcs start_location: end location
        # store G74 arcs
        for i in self.find_all_groups(file, 'G74', 'G01*'):
            self.arcs[i[0]] = i[1]
        # store G75 arcs
        for i in self.find_all_groups(file, 'G75', 'G01*'):
            self.arcs[i[0]] = i[1]

    def find_all_groups(self, file, start, end):
        arr = []
        index = file.find(start)
        while(index != -1):
            end_pos = file.find(end, index)
            arr.append((index, end_pos))
            index = file.find(start, end_pos)
        return arr

    def store_apertures(self, file):
        # [[id,type, radius, additional rect dimention]]
        self.apertures = {}
        index = file.find('ADD')
        while(index != -1):
            profile = []
            id_end = file.find(',', index)-1
            a_id = file[index+3:id_end]
            # store macro type
            profile.append(file[id_end])
            # single dimension
            if(file.find('X', index, file.find('*', index)) == -1):
                profile.append(str(float(file[file.find(
                    ',', index)+1: file.find('*', index)])/2 * self.scale))
            # two dimensions
            elif(file.find('X', file.find('X', index)+1, file.find('*', index)) == -1):
                profile.append(str(float(file[file.find(
                    ',', index)+1: file.find('X', index)]) * self.scale))
                profile.append(str(float(file[file.find(
                    'X', index)+1: file.find('*', index)]) * self.scale))
            # three dimensions
            else:
                profile.append(str(float(file[file.find(
                    ',', index)+1: file.find('X', index)]) * self.scale))
                profile.append(str(float(file[file.find(
                    'X', index)+1: file.find('X', file.find(
                        'X', index)+1)]) * self.scale))
                profile.append(str(float(file[file.find(
                    'X', index)+1: file.find('*', index)]) * self.scale))
            self.apertures[a_id] = (profile)
            index = file.find('ADD', index+1)

    def find_aperture_locations(self, file):
        self.aperture_locs = []
        for aperture in self.apertures.keys():
            i = file.find('D'+str(aperture)+'*')
            self.aperture_locs.append((aperture, i))
        self.aperture_locs.sort(key=self.aperture_sort)
        self.find_macro_endings(file)

    def aperture_sort(self, e):
        return e[1]

    def find_macro_endings(self, file):
        for i in range(len(self.aperture_locs)):
            start_pos = self.aperture_locs[i][1]
            if(i == len(self.aperture_locs)-1):
                end_pos = len(file)
            else:
                end_pos = self.aperture_locs[i+1][1]
            self.aperture_locs[i] += (end_pos,)

    def select_aperture(self, file, id, ref_index):
        aperture_index = file.find('G01' + id, ref_index + 8)
        next_index = file.find('D', aperture_index+1)

        while(next_index != -1 and (file[file.find('D', next_index): file.find('D', next_index)+3] == 'D01', file[file.find('D', next_index): file.find('D', next_index)+3] == 'D02', file[file.find('D', next_index): file.find('D', next_index)+3] == 'D03')):
            next_index = file.find('D', next_index+3)
        if(next_index == -1):
            next_index = file.find('M02')

        return (aperture_index, next_index)

    def set_decimal_places(self, file):
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
        self.set_decimal_places(self.files['outline'])
        self.width = 0
        self.height = 0
        self.min_x = 9999999
        self.min_y = 9999999
        pointer = self.files['outline'].find('D10')
        pointer = self.files['outline'].find('X', pointer)
        while(pointer != -1):
            y = self.files['outline'].find('Y', pointer+1)
            temp = abs(float(
                self.files['outline'][pointer+1: y]))/self.x_decimals
            if(temp > self.width):
                self.width = temp
            if(temp < self.min_x):
                self.min_x = temp

            pointer = self.files['outline'].find(
                'D', y+1)
            temp = self.files['outline'][y+1: pointer]
            temp = abs(float(temp))/self.y_decimals
            if(temp > self.height):
                self.height = temp
            if(temp < self.min_y):
                self.min_y = temp
            pointer = self.files['outline'].find('X', pointer)
        self.width -= self.min_x
        self.height -= self.min_y
        self.unit = 'mm'
        if(self.files['outline'].find('MOIN') != -1):
            self.unit = 'in'

        if(self.verbose):
            print('Board Dimensions: ' + str(round(self.width, 2)) +
                  ' x ' + str(round(self.height, 2)) + ' ' + str(self.unit))

    def get_dimensions(self):
        if(self.width):
            return [self.width, self.height, self.scale]
        else:
            return 'Board Not Rendered'

    def identify_files(self):
        unidentified_files = 0

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
            elif(not self.files['outline'] and (filename[-3:].upper() == 'GKO' or filename[-3:].upper() == 'GM1')):
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
            else:
                unidentified_files +=1;

        shutil.rmtree(self.temp_path)

        if(self.files['drill'] and self.files['outline'] and self.files['top_copper'] and self.files['top_mask']):
            if(self.verbose):
                print('Files Loaded\nUnidentified Files: '+str(unidentified_files))

        else:
            print('Error identifying files')

    def copy_files(self, file):
        for item in os.listdir(file):
            s = os.path.join(file, item)
            d = os.path.join(self.temp_path, item)
            shutil.copy(s, d)

    def extract_files(self, file):
        if(self.verbose):
            print('Extracting Files')
        with zipfile.ZipFile(file, 'r') as zipped:
            zipped.extractall(self.temp_path)

    def open_file(self, filename):
        return open(self.temp_path+'/'+filename, 'r').read()

    def init_file(self, file):
        self.set_decimal_places(file)
        self.store_apertures(file)
        self.find_aperture_locations(file)
        self.store_polygons(file)
        self.store_arcs(file)
