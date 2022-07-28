from ansys.mapdl.core import launch_mapdl
import os
import numpy as np
path = os.getcwd()

mapdl = launch_mapdl(run_location = path, additional_switches = '-smp')

length = 0.4
width = 0.1
notch_depth = 0.04
notch_radius = 0.01
    
mapdl.clear()
mapdl.prep7()

circ0_kp = mapdl.k(x=length / 2, y=width + notch_radius)
circ_line_num = mapdl.circle(circ0_kp, notch_radius)
circ_line_num = circ_line_num[2:]  # only concerned with the bottom arcs

# create a line and drag the top circle downward
circ0_kp = mapdl.k(x=0, y=0)
k1 = mapdl.k(x=0, y=-notch_depth)
l0 = mapdl.l(circ0_kp, k1)
mapdl.adrag(*circ_line_num, nlp1=l0)

# same thing for the bottom notch (except upwards
circ1_kp = mapdl.k(x=length / 2, y=-notch_radius)
circ_line_num = mapdl.circle(circ1_kp, notch_radius)
circ_line_num = circ_line_num[:2]  # only concerned with the top arcs

# create a line whereby the top circle will be dragged up
k0 = mapdl.k(x=0, y=0)
k1 = mapdl.k(x=0, y=notch_depth)
l0 = mapdl.l(k0, k1)
mapdl.adrag(*circ_line_num, nlp1=l0)

rect_anum = mapdl.blc4(width=length, height=width)

# Note how pyansys parses the output and returns the area numbers
# created by each command.  This can be used to execute a boolean
# operation on these areas to cut the circle out of the rectangle.
# plate_with_hole_anum = mapdl.asba(rect_anum, circ_anum)
cut_area = mapdl.asba(rect_anum, "ALL")  # cut all areas except the plate

# mapdl.aplot(vtk=True, show_line_numbering=True)
mapdl.lsla("S")
# mapdl.lplot(vtk=True, show_keypoint_numbering=True)
mapdl.lsel("all")

# Next, extrude the area to create volume
thickness = 0.01
mapdl.vext(cut_area, dz=thickness)
#mapdl.aplot()


#clean up
mapdl.allsel()
mapdl.vsel('s','volu','','all',kswp=1)
mapdl.lsel('inve')
mapdl.ksll()
mapdl.ldele('all',kswp=1)
mapdl.allsel()

mapdl.vsel('s','volu','','all',kswp=1)
mapdl.ksel('inve')
mapdl.kdele('all')
mapdl.allsel()


mapdl.et(1,200)
mapdl.keyopt(1,1,4)
mapdl.smrtsize(1)

mapdl.amesh('all')
#mapdl.eplot()

node_loc = np.array(mapdl.mesh.nodes)
elems = np.array(mapdl.mesh.elem)
node_loc = np.insert(node_loc,0,[0,0,0],0)


def norm_cen(element, ni, nj, nk):
    
    centroid_x = (node_loc[ni,0] + node_loc[nj,0] + node_loc[nk,0])/3.
    centroid_y = (node_loc[ni,1] + node_loc[nj,1] + node_loc[nk,1])/3.
    centroid_z = (node_loc[ni,2] + node_loc[nj,2] + node_loc[nk,2])/3.

    centroid = np.array([centroid_x, centroid_y, centroid_z])
    
    p1 = node_loc[ni]
    p2 = node_loc[nj]
    p3 = node_loc[nk]
    
    normal = np.cross(p1-centroid, p2-centroid)
    
    norm_x = centroid_x + normal[0]
    norm_y = centroid_y + normal[1]
    norm_z = centroid_z + normal[2]
    
    return norm_x, norm_y, norm_z, p1, p2, p3

f = open("file.stl", "wt")
f.write("solid cube\n")

for elem in elems:
    x,y,z,n1,n2,n3 = norm_cen(elem[8], elem[10], elem[11], elem[12])
    f.write("facet normal " + str(x) + " " + str(y) + " " + str(z) + "\n")
    f.write("\touter loop\n")
    f.write("\t\tvertex " + str(n1[0]) + " " + str(n1[1]) + " " + str(n1[2]) + "\n")
    f.write("\t\tvertex " + str(n2[0]) + " " + str(n2[1]) + " " + str(n2[2]) + "\n")
    f.write("\t\tvertex " + str(n3[0]) + " " + str(n3[1]) + " " + str(n3[2]) + "\n")
    f.write("\tendloop\n")
    f.write("endfacet\n")
f.write("endsolid cube")    
f.close()

mapdl.exit()