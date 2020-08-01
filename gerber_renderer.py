import svgwrite
from svgwrite import cm, mm

# initialize svg
svg = svgwrite.Drawing(filename='test.svg', debug=True)

# open drill file
drill_file = open('./testgerber/Gerber_Drill_PTH.DRL', 'r').read()
print(drill_file)

# draw drill holes
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
        next_x = 0
        # find and draw circles at hole coords
        while(next_x < next_tool_holes or (next_tool_holes == -1 and next_x != -1)):
            hole_index = drill_file.find('X', hole_index+1)
            y_index = drill_file.find('Y', hole_index)
            next_x = drill_file.find('X', y_index)
            if(next_x != -1):
                if(drill_file.find('T', y_index) < next_x and drill_file.find('T', y_index) != -1):
                    next_x = drill_file.find('T', y_index)
                # draw holes for metric
                hole_x = float(drill_file[hole_index+1:y_index])/1000
                hole_y = float(drill_file[y_index+1:next_x-1])/1000
                svg.add(svg.circle(center=(hole_x*mm, hole_y*mm),
                                   r=tool_diameter/2*mm, fill='black'))

        tool_num += 1
svg.save()
