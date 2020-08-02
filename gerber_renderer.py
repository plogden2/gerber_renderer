import svgwrite
from svgwrite import cm, mm, inch

# initialize svg
svg = svgwrite.Drawing(filename='test.svg', debug=True)

# open outline file
outline_file = open('./testgerber/Gerber_Drill_PTH.DRL', 'r').read()

# set units
unit = mm
if(outline_file.find('G70') != -1):
    unit = inch

# get board dimensions
# width =


# open drill file
drill_file = open('./testgerber/Gerber_Drill_PTH.DRL', 'r').read()

# draw drill holes
print('Drilling Holes')
tool_bool = True
tool_num = 1
while(tool_bool):
    # get index of tool diameter
    index = drill_file.find('T0'+str(tool_num)+'C')+4
    if(index == 3):
        tool_bool = False
    else:
        tool_diameter = float(drill_file[index:index+5])
        hole_index = drill_file.find('T0'+str(tool_num), index+4)
        next_tool_holes = drill_file.find('T0'+str(tool_num+1), hole_index)
        next_x = drill_file.find('X', hole_index+1)
        # find and draw circles at hole coords
        while(next_x < next_tool_holes or (next_tool_holes == -1 and next_x != -1)):
            hole_index = next_x
            y_index = drill_file.find('Y', hole_index)
            next_x = drill_file.find('X', y_index)
            if(next_x != -1):
                if(drill_file.find('T', y_index) < next_x and drill_file.find('T', y_index) != -1):
                    next_x = drill_file.find('T', y_index)
                # draw holes for metric
                hole_x = float(drill_file[hole_index+1:y_index])/1000
                hole_y = float(drill_file[y_index+1:next_x-1])/1000
                svg.add(svg.circle(center=(hole_x*unit, hole_y*unit),
                                   r=tool_diameter/2*unit, fill='black'))

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
        curr_x = float(silk_file[curr_x+1:curr_y])/1000 * unit
        y_len = 1
        while(str.isnumeric(silk_file[curr_y+1+y_len])):
            y_len += 1
        curr_y = float(silk_file[curr_y+1: curr_y+1+y_len])/1000 * unit

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
