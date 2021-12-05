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
from reportlab.pdfgen import canvas


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

    def render(self, output, silk=True, drc=False):
        self.silk_bool = silk
        self.drc = drc

        if(drc):
            # setup drc error bools
            self.drill_diameter_not_tenth_mm = False
            self.drill_diameter_too_small = False
            self.annular_ring_error = False  # TODO
            self.pad_to_pad_clearance_error = False  # TODO
            self.trace_clearance_error = False  # TODO
            self.trace_width_error = False
            # setup capabilities
            self.min_trace_width = 0.127
            self.min_trace_clearance = 0.127
            self.min_annular_ring = 0.13
            self.min_pad_to_pad = 0.2
            self.min_drill_diameter = 0.3
            # setup drc arrays
            self.traces = []
            self.pads = []
            self.drc_scale = 1

        # setup output path
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

        # print drc results
        if(self.drc):
            print('\nDesign Rules Check Results:')
            print('Drill diameter not tenth of mm:' +
                  str(self.drill_diameter_not_tenth_mm))
            print('Drill diameter below minimum:' +
                  str(self.drill_diameter_too_small))
            # print('Annular ring too small:'+str(self.annular_ring_error))
            # print('Pad to pad clearance too small:' +
            #       str(self.pad_to_pad_clearance_error))
            # print('Trace to trace clearance too small:' +
            #       str(self.trace_clearance_error))
            print('Trace width too small:'+str(self.trace_width_error))

    def draw_svg(self, layer, filename):
        self.copper_bool = False

        if(not self.width):
            self.set_dimensions()
            self.scale = self.max_height/self.height

        # initialize svg
        self.drawing = svgwrite.Drawing(
            filename=self.output_folder+filename, size=(self.width*self.scale, self.height*self.scale), debug=False)

        # draw background rectangle
        self.drawing.add(self.drawing.rect(insert=(0, 0), size=(
            str(self.width*self.scale), str(self.height*self.scale)), fill='darkgreen'))
        #  fill='#f0e6aa'

        # if(self.verbose):
        #     print('Milling Outline')
        # self.init_file('outline')
        # self.draw_macros(file=self.files['outline'],
        #                  color='darkgreen')

        # draw copper layer
        if(self.verbose):
            print('Etching Copper')
        self.copper_bool = True
        self.init_file(layer+'_copper')
        self.clear_color = 'darkgreen'
        self.draw_macros(file=self.files[layer+'_copper'],
                         color='green')
        self.copper_bool = False

        if(self.files[layer+'_silk'] and self.silk_bool):
            # draw silk screen
            if(self.verbose):
                print('Curing Silk Screen')
            self.init_file(layer+'_silk')
            self.draw_macros(file=self.files[layer+'_silk'],
                             color='white')

        # draw solder mask
        if(self.verbose):
            print('Applying Solder Mask')
        self.init_file(layer+'_mask')
        self.draw_macros(file=self.files[layer+'_mask'],  color='#969696')

        # draw drill holes
        if(self.verbose):
            print('Drilling Holes')
        self.drill_holes()

        self.drawing.save()

    def render_pdf(self, output, layer='top_copper', color='white', scale_compensation=0.0, full_page=False, mirrored=False, offset=(0, 0)):
        self.drc = False
        # setup output path
        self.output_folder = output
        if(self.output_folder[-1] == '/'):
            self.output_folder = self.output_folder[:-1]
        if not os.path.exists(self.output_folder):
            os.makedirs(self.output_folder)
        self.output_folder += '/'

        if(not self.width):
            self.set_dimensions()

        self.scale = 3.543307 if self.unit == 'mm' else 90

        # initialize svg
        self.drawing = svgwrite.Drawing(
            filename=self.output_folder+layer+'.svg', size=(self.width*self.scale+offset[0], self.height*self.scale+offset[1]), debug=False)

        # draw background rectangle
        self.drawing.add(self.drawing.rect(insert=(0, 0), size=(
            str(self.width*self.scale), str(self.height*self.scale+5)), fill='black' if color == 'white' else 'white'))

        # draw layer
        self.init_file(layer)
        self.clear_color = 'black' if color == 'white' else 'white'
        self.draw_macros(file=self.files[layer],
                         color=color)

        self.drawing.save()

        # convert svg drawing to pdf
        drawing = svg2rlg(self.output_folder+layer+".svg")
        if(mirrored):
            drawing.scale(-1, 1)
            drawing.translate(-self.width*self.scale *
                              (1+scale_compensation[0])-offset[0]*2, 0)
        # drawing.rotate(-90)
        drawing.translate(offset[0], 0)
        drawing.scale(1+scale_compensation[0], 1+scale_compensation[1])
        drawing.translate(0, -offset[1])
        d = graphics.shapes.Drawing(self.width*self.scale*(
            1+scale_compensation[0])+offset[0], self.height*self.scale*(1+scale_compensation[1])+offset[1])
        d.add(drawing)
        renderPDF.drawToFile(d, self.output_folder +
                             layer+".pdf", autoSize=int(not full_page))
        os.remove(self.output_folder+layer+".svg")

    def draw_macros(self, file, color, fill='none'):
        self.last_x = -1
        self.last_y = -1
        if(len(self.aperture_locs) > 0 and file.find('X') < self.aperture_locs[0][1] and file.find('X') != -1):
            self.draw_section(file[:self.aperture_locs[0][1]], False, color)
        for macro in self.aperture_locs:
            if(file == self.files['outline']):
                self.polygon_fill(file[macro[1]:macro[2]], color)
            else:
                self.draw_section(file[macro[1]:macro[2]], macro[0], color)

    def draw_section(self, g_code, a_id, color):
        if(a_id):
            radius = float(self.apertures[a_id][1])
            shape = self.apertures[a_id][0]
        g_loc = 0
        x_loc = 0
        x = self.last_x
        y = self.last_y
        self.fill_polarity = 1  # dark
        # find all coords and draw path
        path = ''

        g_loc = g_code.find('G')

        # get fill polarity
        if(g_code.find('LPC*%') < g_loc and g_code.find('LPC*%') != -1):
            self.fill_polarity = 0

        # case where no g code is present for first move
        x_loc = g_code.find('X')
        if(x_loc < g_loc or g_loc == -1):
            g_code = 'G01*' + g_code[x_loc:]
            g_loc = 0

        while(True):
            if(g_loc == -1):
                break
            code = g_code[g_loc:g_loc+3]

            if(code == 'G37'):
                code = 'G01'

            if(code == 'G36'):
                next_code = g_code.find('G37', g_loc)
                self.polygon_fill(
                    g_code[g_loc:next_code], color)
                g_loc = next_code
            else:
                next_code = g_code.find('G', g_loc+1)
                x_loc = g_code.find('X', g_loc+1)
                while((x_loc < next_code and x_loc != -1) or (next_code == -1 and x_loc != -1)):
                    y_loc = g_code.find('Y', x_loc)
                    if(code == 'G01'):
                        d_code = g_code[g_code.find(
                            'D', x_loc):g_code.find('D', x_loc)+3]

                        if(d_code == 'D01' and path == '' and x != -1):
                            path += 'M' + x + ',' + y

                        x = str(
                            ((abs(float(g_code[x_loc+1:y_loc]))/self.x_decimals)-self.min_x)*self.scale)
                        y = str(
                            ((abs(float(g_code[y_loc+1:g_code.find('D', y_loc)]))/self.y_decimals)-self.min_y)*self.scale)

                        if(d_code == 'D02' or path == ''):
                            path += 'M' + x + ',' + y
                            if(g_code.find('D01', y_loc, g_code.find('D02', g_code.find('D', x_loc)+3)) != -1 and shape == 'C'):
                                self.drawing.add(self.drawing.circle(
                                    center=(x, y), r=radius, fill=color))
                        elif (d_code == 'D01'):
                            path += 'L' + x + ',' + y
                            if(self.drc and self.copper_bool and self.last_x != -1):
                                self.drc_check(
                                    'trace', radius, [self.last_x, self.last_y], [x, y])

                        if(d_code == 'D01' or d_code == 'D03'):
                            if(shape == 'C'):
                                self.drawing.add(self.drawing.circle(
                                    center=(x, y), r=radius, fill=color))
                            elif(shape == 'O'):
                                self.drawing.add(self.drawing.ellipse(center=(x, y), r=(str(float(
                                    self.apertures[a_id][1])/2), str(float(self.apertures[a_id][2])/2)), fill=color))
                            elif(shape == 'R'):
                                width = float(self.apertures[a_id][1])
                                height = float(self.apertures[a_id][2])
                                self.drawing.add(self.drawing.rect(insert=(str(float(
                                    x)-width/2), str(float(y)-height/2)), size=(str(width), str(height)), fill=color))
                            # else:
                            #     print(shape)
                    elif(code == 'G02' or code == 'G03'):
                        if(code == 'G02'):
                            sweep_flag = '0'
                        else:
                            sweep_flag = '1'
                        path += self.draw_arc(
                            g_code[x_loc-3:g_code.find('*', x_loc)], sweep_flag, start_pos=(x, y))
                    # else:
                        # print(code)
                    x_loc = g_code.find('X', x_loc+1)
                if(g_code.find('LPC*%', g_loc) < next_code and g_code.find('LPC*%', g_loc) != -1):
                    self.fill_polarity = 0
                if(g_code.find('LPD*%', g_loc) < next_code and g_code.find('LPD*%', g_loc) > g_code.find('LPC*%', g_loc) and g_code.find('LPC*%', g_loc) != -1):
                    self.fill_polarity = 1
                g_loc = next_code
        self.last_x = x
        self.last_y = y
        if(path):
            self.drawing.add(self.drawing.path(
                d=path, stroke=color, stroke_width=radius*2, fill='none'))

    def drc_check(self, p_type, radius, start_pos, end_pos):
        radius /= self.scale/self.drc_scale
        # start_pos[0] = float(start_pos[0]) / self.scale/self.drc_scale
        # start_pos[1] = float(start_pos[1]) / self.scale/self.drc_scale
        # end_pos[0] = float(end_pos[0]) / self.scale/self.drc_scale
        # end_pos[1] = float(end_pos[1]) / self.scale/self.drc_scale
        if(p_type == 'trace'):
            # width check
            if(radius*2 < self.min_trace_width):
                self.trace_width_error = True

            # clearance check
            # if(end_pos[0] != start_pos[0]):
            #     new_trace_slope = (end_pos[1]-start_pos[1]) / \
            #         (end_pos[0]-start_pos[0])
            # else:
            #     new_trace_slope = 9999999999

            # if(new_trace_slope == 0):
            #     new_trace_slope = 0.00000000001
            # # find points of bounding lines
            # start_endpoints = self.find_endpoints(
            #     start_pos, radius+self.min_trace_clearance, -1/new_trace_slope)
            # end_endpoints = self.find_endpoints(
            #     end_pos, radius+self.min_trace_clearance, -1/new_trace_slope)
            # new_trace_left_bound = [start_endpoints[0], end_endpoints[0]]
            # new_trace_right_bound = [start_endpoints[0], end_endpoints[0]]
            # self.drawing.add(self.drawing.circle(
            #                         center=(new_trace_left_bound[1][0]*self.scale*self.drc_scale, new_trace_left_bound[1][1]*self.scale*self.drc_scale), r=1.0, fill='red'))
            # self.drawing.add(self.drawing.line(
            #     start=(new_trace_left_bound[0][0]*self.scale*self.drc_scale, new_trace_left_bound[0][1]*self.scale*self.drc_scale), end=(new_trace_left_bound[1][0]*self.scale*self.drc_scale, new_trace_left_bound[1][1]*self.scale*self.drc_scale), stroke='red'))
            # clearance check
            # for trace in self.traces:
            #     existing_trace_left_bound = [[trace[1][0]-trace[0], trace[1][1]-trace[0]], [trace[2][0]-trace[0], trace[2][1]-trace[0]]]
            #     existing_trace_right_bound = [[trace[1][0]+trace[0], trace[1][1]+trace[0]], [trace[2][0]+trace[0], trace[2][1]+trace[0]]]
            # self.traces.append([radius, start_pos, end_pos])

    def find_endpoints(self, start_pos, distance, slope):
        x1 = start_pos[0]
        y1 = start_pos[1]

        c = 1/math.sqrt(1+pow(slope, 2))
        s = slope/math.sqrt(1+pow(slope, 2))

        left_point = [x1 - distance * c, y1 - distance * s]
        right_point = [x1 + distance * c, y1 + distance * s]

        return [left_point, right_point]

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

    def polygon_fill(self, g_code, color):
        g_loc = 0
        x_loc = 0
        # find all coords and draw path
        path = ''

        g_loc = g_code.find('G')
        # case where no g code is present for first move
        x_loc = g_code.find('X')
        if(x_loc < g_loc or g_loc == -1):
            g_code = 'G01*' + g_code[x_loc:]
            g_loc = 0
        while(True):
            if(g_loc == -1):
                break
            code = g_code[g_loc:g_loc+3]
            if(code == 'G36'):
                code = 'G01'
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
                    if(code == 'G02'):
                        sweep_flag = '0'
                    else:
                        sweep_flag = '1'
                    path += self.draw_arc(
                        g_code[x_loc-3:g_code.find('*', x_loc)], sweep_flag, start_pos=(x, y))

                x_loc = g_code.find('X', x_loc+1)
            g_loc = next_code
        path += ' Z'

        if(self.fill_polarity):
            self.drawing.add(self.drawing.path(
                d=path, stroke='none', fill=color))
        else:
            self.drawing.add(self.drawing.path(
                d=path, stroke='none', fill=self.clear_color))

    def drill_holes(self):
        self.trailing_zeros = -1
        self.get_drill_decimals()
        self.get_drill_tools()
        file = self.files['drill'][self.drill_header_end:]
        self.get_drill_locs(file)

        for tool in self.drill_tools:
            diameter = tool['diameter']
            # draw all holes for current tool

            section = file[tool['start']:tool['end']]
            curr_x = section.find('X')
            curr_y = section.find('Y', curr_x)

            # find and draw circles at hole coords
            while(curr_x != -1):
                y_len = 1
                while(str.isnumeric(section[curr_y+1+y_len]) or section[curr_y+1+y_len] == '.' or section[curr_y+1+y_len] == '-'):
                    y_len += 1
                if(self.trailing_zeros == -1):
                    hole_x = (abs(float(section
                                        [curr_x+1:curr_y])))/(self.drill_decimals if (section[curr_x+1:curr_y]).find('.') == -1 else 1)
                    hole_y = (abs(float(section
                                        [curr_y+1: curr_y+1+y_len])))/(self.drill_decimals if (section[curr_y+1: curr_y+1+y_len]).find('.') == -1 else 1)
                else:
                    if ((section[curr_x+1:curr_y]).find('.') == -1):
                        hole_x = (abs(float(section[curr_x+1:curr_y-self.trailing_zeros] +
                                            '.'+section[curr_y-self.trailing_zeros:curr_y])))
                    if ((section[curr_y+1: curr_y+1+y_len]).find('.') == -1):
                        hole_y = (abs(float(section
                                            [curr_y+1: curr_y+1+y_len-self.trailing_zeros]+'.'+section
                                            [curr_y+1+y_len-self.trailing_zeros: curr_y+1+y_len])))

                self.drawing.add(self.drawing.circle(center=(str(hole_x*self.drill_scale-self.min_x*self.scale), str(hole_y*self.drill_scale-self.min_y*self.scale)),
                                                     r=str((diameter/2)*self.drill_scale), fill='black'))
                curr_x = section.find('X', curr_y)
                curr_y = section.find('Y', curr_x)

    def get_drill_decimals(self):
        file = self.files['drill']
        self.drill_scale = self.scale
        index = file.find('METRIC')
        if(index != -1):
            initial = file.find('.', index)+1
            i = initial
            if(i < file.find('T', index) and i < file.find(';', index)):
                while(file[i] == '0'):
                    i += 1

                self.drill_decimals = pow(10, int(i-initial))
            else:
                self.drill_decimals = 1000
            if(self.unit == 'in'):
                self.drill_scale = self.scale / 25.4
        elif(file.find('INCH') != -1):
            index = file.find('INCH')
            initial = file.find('.', index)+1
            i = initial
            if(i < file.find('T', index) and i < file.find(';', index)):
                while(file[i] == '0'):
                    i += 1

                self.drill_decimals = pow(10, int(i-initial))
            else:
                self.drill_decimals = 10000
            if(self.unit == 'mm'):
                self.drill_scale = self.scale * 25.4
        else:
            self.drill_decimals = 1000

    def get_drill_tools(self):
        metric_drill_bool = True
        self.drill_tools = []
        file = self.files['drill']
        tool_start = file.find('METRIC')+7
        if(tool_start == 6):
            tool_start = file.find('INCH')+5
            metric_drill_bool = False
        self.drill_header_end = file.find('%', tool_start)
        file = file[tool_start:self.drill_header_end]
        file = self.remove_comments(file)

        index = -2
        next_index = -2
        while(index != -1):
            curr_tool = {}

            if(next_index != -2):
                index = next_index
            else:
                index = file.find('T', index+2)
                if(file[index+1] == 'Z'):
                    index = file.find('T', index+2)

            if(index == -1):
                break

            # set tool id and next tool id
            c_index = file.find('C', index)
            curr_tool['name'] = file[index:c_index]
            next_index = file.find('T', c_index)
            curr_tool['next'] = file[next_index:file.find('C', next_index)]

            # get diameter
            curr_tool['diameter'] = float(file[c_index+1:next_index])

            if(self.drc and not self.drill_diameter_not_tenth_mm):
                diam = curr_tool['diameter']
                if(not metric_drill_bool):
                    diam *= 25.4
                if(math.floor(diam*10) != diam*10):
                    self.drill_diameter_not_tenth_mm = True

            if(self.drc and not self.drill_diameter_too_small):
                diam = curr_tool['diameter']
                if(not metric_drill_bool):
                    diam *= 25.4
                if(diam < self.min_drill_diameter):
                    self.drill_diameter_too_small = True

            self.drill_tools.append(curr_tool)

    def get_drill_locs(self, file):
        for tool in self.drill_tools:
            start_index = file.find(tool['name'])
            end_index = file.find('T', start_index+1)
            if(end_index == -1):
                end_index = file.find('M', start_index)
            tool['start'] = int(start_index)
            tool['end'] = int(end_index)

    def remove_comments(self, file):
        start_index = file.find(';')

        while(start_index != -1):
            end_index = file.find('\n', start_index)
            if(file.find('\r', start_index) < end_index and file.find('\r', start_index) != -1):
                end_index = file.find('\r', start_index)
            file = file[:start_index]+file[end_index:]
            start_index = file.find(';')
        return file

    def find_all_groups(self, file, start, end):
        arr = []
        index = file.find(start)
        while(index != -1):
            end_pos = file.find(end, index)
            arr.append((index, end_pos))
            index = file.find(start, end_pos)
        return arr

    def store_apertures(self, filename):
        # [[id,type, radius, additional rect dimention]]
        file = self.files[filename]
        self.apertures = {}
        index = file.find('ADD')
        a_id = False
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
                    'X', file.find('X', index)+1)+1: file.find('*', index)]) * self.scale))
            self.apertures[a_id] = (profile)
            index = file.find('ADD', index+1)
        if(a_id):
            self.files[filename] = file[file.find(
                '%', file.find('ADD'+a_id))+1:]

    def find_aperture_locations(self, file):
        self.aperture_locs = []
        for aperture in self.apertures.keys():
            locs = [j.start()
                    for j in re.finditer('(?=D'+str(aperture)+'\*)', file)]
            for i in locs:
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
        self.x_decimals = pow(10, int(self.x_decimals))
        self.y_decimals = pow(10, int(self.y_decimals))

    def set_dimensions(self):
        file = self.files['outline']
        self.set_decimal_places(file)
        self.width = 0
        self.height = 0
        self.min_x = 9999999
        self.min_y = 9999999
        pointer = file.find('D10')
        pointer = file.find('X', pointer)
        while(pointer != -1):
            y = file.find('Y', pointer+1)
            temp = abs(float(
                file[pointer+1: y]))/self.x_decimals
            if(temp > self.width):
                self.width = temp
            if(temp < self.min_x):
                self.min_x = temp

            pointer = file.find(
                'D', y+1)
            if(file[y+1:pointer].find('I') != -1):
                pointer = file.find('I', y+1, pointer)
            if(file[y+1:pointer].find('J') != -1):
                pointer = file.find('J', y+1, pointer)
            temp = file[y+1: pointer]
            temp = abs(float(temp))/self.y_decimals
            if(temp > self.height):
                self.height = temp
            if(temp < self.min_y):
                self.min_y = temp
            pointer = file.find('X', pointer)
        self.width -= self.min_x
        self.height -= self.min_y
        self.unit = 'mm'
        if(file.find('MOIN') != -1):
            self.unit = 'in'
            if(self.drc):
                self.drc_scale = 25.4

        if(self.verbose):
            print('Board Dimensions: ' + str(round(self.width, 2)) +
                  ' x ' + str(round(self.height, 2)) + ' ' + str(self.unit))

    def get_dimensions(self):
        if(self.width):
            if(self.unit == 'in'):
                return [self.width*25.4, self.height*25.4]
            return [self.width, self.height]
        else:
            return 'Board Not Rendered'

    def get_files(self):
        return self.files

    def infer_filetype(self, file, filename):
        if(filename[:-4].upper() == 'PROFILE'):
            self.files['outline'] = file
        elif(file.upper().find('TOP') != -1):
            if(file.upper().find('COPPER') != -1):
                self.files['top_copper'] = file
            elif(file.upper().find('SOLDERMASK') != -1):
                self.files['top_mask'] = file
            elif(file.upper().find('SILK') != -1):
                self.files['top_silk'] = file
        elif(file.upper().find('BOTTOM') != -1):
            if(file.upper().find('COPPER') != -1):
                self.files['bottom_copper'] = file
            elif(file.upper().find('SOLDERMASK') != -1):
                self.files['bottom_mask'] = file
            elif(file.upper().find('SILK') != -1):
                self.files['bottom_silk'] = file

    def identify_files(self):
        unidentified_files = 0
        subfolder = ''

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
        for root, dirs, files in os.walk(self.temp_path):
            for filename in files:
                if(not self.files['drill'] and filename[-3:].upper() == 'DRL' or filename[-3:].upper() == 'XLN'):
                    self.files['drill'] = open(root+'/'+filename, 'r').read()
                elif(not self.files['outline'] and (filename[-3:].upper() == 'GKO' or filename[-3:].upper() == 'GM1')):
                    self.files['outline'] = open(root+'/'+filename, 'r').read()
                elif(not self.files['top_copper'] and filename[-3:].upper() == 'GTL'):
                    self.files['top_copper'] = open(
                        root+'/'+filename, 'r').read()
                elif(not self.files['top_mask'] and filename[-3:].upper() == 'GTS'):
                    self.files['top_mask'] = open(
                        root+'/'+filename, 'r').read()
                elif(not self.files['top_silk'] and filename[-3:].upper() == 'GTO'):
                    self.files['top_silk'] = open(
                        root+'/'+filename, 'r').read()
                elif(not self.files['bottom_copper'] and filename[-3:].upper() == 'GBL'):
                    self.files['bottom_copper'] = open(
                        root+'/'+filename, 'r').read()
                elif(not self.files['bottom_mask'] and filename[-3:].upper() == 'GBS'):
                    self.files['bottom_mask'] = open(
                        root+'/'+filename, 'r').read()
                elif(not self.files['bottom_silk'] and filename[-3:].upper() == 'GBO'):
                    self.files['bottom_silk'] = open(
                        root+'/'+filename, 'r').read()
                elif(filename[-3:].upper() == 'GBR'):
                    temp = open(root+'/'+filename, 'r').read()
                    self.infer_filetype(temp, filename)
                else:
                    unidentified_files += 1

        shutil.rmtree(self.temp_path)

        if(self.files['drill'] and self.files['outline'] and self.files['top_copper'] and self.files['top_mask']):
            if(self.verbose):
                print('Files Loaded\nUnidentified Files: ' +
                      str(unidentified_files))
        else:
            print('Error identifying files')

    def copy_files(self, file):
        for item in os.listdir(file):
            s = os.path.join(file, item)
            d = os.path.join(self.temp_path, item)
            shutil.copytree(s, d)

    def extract_files(self, file):
        if(self.verbose):
            print('Extracting Files')
        with zipfile.ZipFile(file, 'r') as zipped:
            zipped.extractall(self.temp_path)

    def open_file(self, filename):
        return open(self.temp_path+'/'+filename, 'r').read()

    def init_file(self, filename):
        self.set_decimal_places(self.files[filename])
        self.store_apertures(filename)
        self.find_aperture_locations(self.files[filename])
