import svgwrite
from svgwrite import cm, mm, inch


def render_file(outline, copper, mask, silk, drill, filename='pcb.svg'):
    # initialize svg
    svg = svgwrite.Drawing(filename=filename, debug=True)

    # open outline file
    outline_file = open(outline, 'r').read()

    # set units
    unit = 'mm'
    scale = 3.543307
    if(outline_file.find('G70') != -1):
        unit = 'in'
        scale = 90

    # get board dimensions
    # get width
    width = 0
    pointer = outline_file.find('G01X')+3
    while(pointer != -1):
        temp = float(
            outline_file[pointer+1: outline_file.find('Y', pointer)])/1000
        if(temp > width):
            width = temp
        pointer = outline_file.find('X', pointer+1)
    # get height
    height = 0
    pointer = outline_file.find('Y', outline_file.find('G01X'))
    while(pointer != -1):
        y_len = 1
        while(str.isnumeric(outline_file[pointer+1+y_len])):
            y_len += 1

        temp = float(outline_file[pointer+1: pointer+1+y_len])/1000
        if(temp > height):
            height = temp
        pointer = outline_file.find('Y', pointer+1)
    print('Board Dimensions: ' + str(width) +
          ' x ' + str(height) + ' ' + str(unit))

    # draw background rectangle
    svg.add(svg.rect(insert=(0, 0), size=(
        str(width*scale), str(height*scale)), fill='#2ea64e'))

    # open top copper file
    copper_file = open(copper, 'r').read()

    # draw top silk screen
    print('Etching Copper')
    index = 0
    while(True):
        # get index of first toolpath
        index = copper_file.find('G01', index+1)
        if(index == -1):
            break
        else:
            # find X and Y coords
            curr_x = copper_file.find('X', index)
            curr_y = copper_file.find('Y', index)
            curr_x = str(float(copper_file[curr_x+1:curr_y])/1000 * scale)
            y_len = 1
            while(str.isnumeric(copper_file[curr_y+1+y_len])):
                y_len += 1
            curr_y = str(
                float(copper_file[curr_y+1: curr_y+1+y_len])/1000 * scale)

            # get D code
            D_code = copper_file.find('D', index)
            D_code = copper_file[D_code:D_code+3]
            if(D_code == 'D01'):
                # draw line
                svg.add(svg.line(start=(prev_x, prev_y),
                                 end=(curr_x, curr_y), stroke='darkgreen'))

            prev_x = curr_x
            prev_y = curr_y
    svg.save()

    # open top solder mask file
    mask_file = open(mask, 'r').read()

    # draw top solder mask
    print('Applying Solder Mask')
    # draw rectangles
    while(True):
        # get index of first rectangle
        index = mask_file.find('G36', index+1)
        if(index == -1):
            break
        else:
            # find X and Y coords of top left
            left_x = mask_file.find('X', index)
            top_y = mask_file.find('Y', index)

            left_x = float(mask_file[left_x+1:top_y])

            # get width
            r_width = 0
            tmp_x = top_y
            while(r_width == 0):
                tmp_x = mask_file.find('X', tmp_x+1)
                if(float(mask_file[tmp_x+1: mask_file.find('Y', tmp_x)]) > left_x):
                    r_width = str(
                        (float(mask_file[tmp_x+1: mask_file.find('Y', tmp_x)])-left_x)/1000 * scale)
            left_x = str(left_x/1000 * scale)

            y_len = 1
            while(str.isnumeric(mask_file[top_y+1+y_len])):
                y_len += 1
            top_y = float(mask_file[top_y+1: top_y+1+y_len])

            # get height
            r_height = 0
            tmp_y = mask_file.find('Y', index)
            while(r_height == 0):
                tmp_y = mask_file.find('Y', tmp_y+1)
                y_len = 1
                while(str.isnumeric(mask_file[tmp_y+1+y_len])):
                    y_len += 1
                if(float(mask_file[tmp_y+1: tmp_y+1+y_len]) > top_y):
                    r_height = str(
                        (float(mask_file[tmp_y+1:tmp_y+1+y_len])-top_y)/1000*scale)

            top_y = str(top_y/1000 * scale)

            # draw rect
            svg.add(svg.rect(insert=(left_x, top_y), size=(
                r_width, r_height), fill='grey'))

    # draw circles
    while(True):
        # get index of circle profile declaration
        index = mask_file.find('%ADD', index+1)
        if(index == -1):
            break
        else:
            # determine if circle or rect
            if(mask_file[index+5] == 'C' or mask_file[index+6] == 'C'):
                # draw circles
                radius = str(float(mask_file[mask_file.find(
                    ',', index)+1: mask_file.find('*', index)])/2 * scale)

                c_id = mask_file[index+4:index+6]

                # find circle centers of profile
                p_index = mask_file.find('D' + c_id, index + 8)

                # find and draw all circles for current diameter
                path = ''
                while(True):
                    p_index = mask_file.find('G', p_index+1)
                    if(mask_file[p_index: p_index+3] != 'G01'):
                        break
                    x = mask_file.find('X', p_index)
                    y = mask_file.find('Y', x)
                    x = str(float(mask_file[x+1:y])/1000*scale)
                    y = str(
                        float(mask_file[y+1:mask_file.find('D', y)])/1000*scale)
                    if(mask_file[mask_file.find('D', p_index):mask_file.find('D', p_index)+3] == 'D02'):
                        path += 'M' + x + ',' + str(float(y))
                    else:
                        path += 'L' + x + ',' + str(float(y))

                    svg.add(svg.circle(center=(x, y),
                                       r=radius, fill='grey'))
                svg.add(svg.path(d=path, stroke='grey',
                                 stroke_width=float(radius)*2))
                # draw rectangles
            else:
                r_width = str(float(mask_file[mask_file.find(
                    ',', index)+1: mask_file.find('X', index)]) * scale)
                r_height = str(float(mask_file[mask_file.find(
                    'X', index)+1: mask_file.find('*', index)]) * scale)
                r_id = mask_file[index+4:index+6]

                # findrect coords of profile
                p_index = mask_file.find('D' + r_id, index + 8)

                while(True):
                    p_index = mask_file.find('G', p_index+1)
                    if(mask_file[p_index: p_index+3] != 'G01'):
                        break
                    # find X and Y coords of top left
                    left_x = mask_file.find('X', p_index)
                    top_y = mask_file.find('Y', p_index)

                    left_x = str(
                        float(mask_file[left_x+1:top_y])/1000*scale-float(r_width)/2)

                    top_y = str(
                        float(mask_file[top_y+1: mask_file.find('D', top_y+1)])/1000*scale-float(r_height)/2)

                    # draw rect
                    svg.add(svg.rect(insert=(left_x, top_y), size=(
                        r_width, r_height), fill='grey'))

    svg.save()

    # open top silk screen file
    silk_file = open(silk, 'r').read()

    # draw top silk screen
    print('Curing Silk Screen')
    index = 0
    while(True):
        # get index of first toolpath
        index = silk_file.find('G01', index+1)
        if(index == -1):
            break
        else:
            # find X and Y coords
            curr_x = silk_file.find('X', index)
            curr_y = silk_file.find('Y', index)
            curr_x = str(float(silk_file[curr_x+1:curr_y])/1000 * scale)
            y_len = 1
            while(str.isnumeric(silk_file[curr_y+1+y_len])):
                y_len += 1
            curr_y = str(
                float(silk_file[curr_y+1: curr_y+1+y_len])/1000 * scale)

            # get D code
            D_code = silk_file.find('D', index)
            D_code = silk_file[D_code:D_code+3]
            if(D_code == 'D01'):
                # draw line
                svg.add(svg.line(start=(prev_x, prev_y),
                                 end=(curr_x, curr_y), stroke='white'))

            prev_x = curr_x
            prev_y = curr_y
    svg.save()

    # open drill file
    drill_file = open(drill, 'r').read()

    # draw drill holes
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
                svg.add(svg.circle(center=(str(hole_x*scale), str(hole_y*scale)),
                                   r=str(diameter/2*scale), fill='black'))
                curr_x = drill_file.find('X', curr_y)
                curr_y = drill_file.find('Y', curr_x)

            tool_num += 1
    svg.save()


render_file('./testgerber/Gerber_BoardOutline.GKO', './testgerber/Gerber_TopLayer.GTL',
            './testgerber/Gerber_TopSolderMaskLayer.GTS', './testgerber/Gerber_TopSilkLayer.GTO', './testgerber/Gerber_Drill_PTH.DRL', 'top.svg')

render_file('./testgerber/Gerber_BoardOutline.GKO', './testgerber/Gerber_BottomLayer.GBL',
            './testgerber/Gerber_BottomSolderMaskLayer.GBS', './testgerber/Gerber_BottomSilkLayer.GBO', './testgerber/Gerber_Drill_PTH.DRL')
