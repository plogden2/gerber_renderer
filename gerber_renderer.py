import svgwrite
from svgwrite import cm, mm, inch

# initialize svg
svg = svgwrite.Drawing(filename='test.svg', debug=True)

# open outline file
outline_file = open('./testgerber/Gerber_BoardOutline.GKO', 'r').read()

# set units
unit = 'mm'
if(outline_file.find('G70') != -1):
    unit = 'in'

# get board dimensions
# get width
width = 0
pointer = outline_file.find('G01X')+3
while(pointer != -1):
    temp = float(outline_file[pointer+1: outline_file.find('Y', pointer)])/1000
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


# open drill file
drill_file = open('./testgerber/Gerber_Drill_PTH.DRL', 'r').read()

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
            svg.add(svg.circle(center=(str(hole_x)+unit, str(hole_y)+unit),
                               r=str(diameter/2)+unit, fill='black'))
            curr_x = drill_file.find('X', curr_y)
            curr_y = drill_file.find('Y', curr_x)

        tool_num += 1
svg.save()

# open top silk screen file
silk_file = open('./testgerber/Gerber_TopSilkLayer.GTO', 'r').read()

# draw top silk screen
print('Curing Silk Screen')
index = 0
while(True):
    # get index of tool diameter
    index = silk_file.find('G01', index+1)
    if(index == -1):
        break
    else:
        # find X and Y coords
        curr_x = silk_file.find('X', index)
        curr_y = silk_file.find('Y', index)
        curr_x = str(float(silk_file[curr_x+1:curr_y])/1000) + unit
        y_len = 1
        while(str.isnumeric(silk_file[curr_y+1+y_len])):
            y_len += 1
        curr_y = str(float(silk_file[curr_y+1: curr_y+1+y_len])/1000) + unit

        # get D code
        D_code = silk_file.find('D', index)
        D_code = silk_file[D_code:D_code+3]
        if(D_code == 'D01'):
            # draw line
            svg.add(svg.line(start=(prev_x, prev_y),
                             end=(curr_x, curr_y), stroke='black'))

        prev_x = curr_x
        prev_y = curr_y
svg.save()
