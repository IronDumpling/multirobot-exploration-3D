import xml.etree.ElementTree as ET
import cv2, argparse
from PIL import Image

def img_pre_process(file_name, file_type, scale=200):
    origin_img = cv2.imread(file_name + file_type, cv2.IMREAD_GRAYSCALE)
    proc_img = cv2.resize(origin_img, (scale, scale), interpolation=cv2.INTER_NEAREST)
    proc_img = cv2.cvtColor(proc_img, cv2.COLOR_GRAY2BGR)
    proc_filename = file_name + "_proc" + file_type
    cv2.imwrite(proc_filename, proc_img)

def obstacle_link(start, end, y, model):
    length = end - start
    width = 1
    x = (start + end) / 2.0
    wall_name = "Wall_{0}_{1}".format(x, y)
    
    def transform_tags(parent):
        geometry = ET.SubElement(parent, "geometry")
        box = ET.SubElement(geometry, "box")
        size = ET.SubElement(box, "size")
        size.text = "{0} {1} {2}".format(length * cell_scale, width * cell_scale, cell_height)
        pose = ET.SubElement(collision, "pose", frame='')
        pose.text = "{0} {1} {2} 0 -0 0".format(x * cell_scale, y * cell_scale, cell_height/2.0)
    
    link = ET.SubElement(model, "link", name=wall_name)
    # collision
    collision = ET.SubElement(link, "collision", name=wall_name + "_Collision")
    transform_tags(collision)
    # visualization
    visual = ET.SubElement(link, "visual", name=wall_name + "_Visual")
    transform_tags(visual)
    # material
    material = ET.SubElement(visual, "material")
    material_script = ET.SubElement(material, "script")
    ET.SubElement(material_script, "uri").text = "file://media/materials/scripts/gazebo.material"
    ET.SubElement(material_script, "name").text = "Gazebo/Grey"
    ET.SubElement(material, "ambient").text = "1 1 1 1"
    # meta
    meta = ET.SubElement(visual, "meta")
    ET.SubElement(meta, "layer").text = "0"
    # position
    pose = ET.SubElement(link, "pose", frame='')
    pose.text = "{0} {1} {2} 0 -0 0".format(x * cell_scale, y * cell_scale, cell_height/2.0)

def parse_jpg_to_sdf(file_name, file_type):
    img = Image.open(file_name + "_proc" + file_type)
    img = img.convert("L")

    width, height = img.size

    # Create the root element for the SDF file
    sdf_root = ET.Element("sdf", version="1.6")
    model = ET.SubElement(sdf_root, "model", name="GridMap")
    pose = ET.SubElement(model, "pose", frame='')
    pose.text = "{0} {1} {2} 0 -0 0".format(0, 0, 0)

    # Loop through the image pixels
    for y in range(height):
        has_wall = False
        start, end = 0.0, 0.0
        for x in range(width):
            pixel_value = img.getpixel((x, y))
            # black pixel: wall's starting point
            if pixel_value == 0 and not has_wall:
                start = x
                has_wall = True
            # white pixel: wall's ending point
            if pixel_value == 1 and has_wall:
                end = x - cell_scale
                obstacle_link(start, end, y, model)
                print("end at free space: ({}, {})".format(x, y))
                has_wall = False
            # end of line: wall's ending point
            if x == width-1 and has_wall:
                end = x
                obstacle_link(start, end, y, model)
                print("end of line: {}".format(y))
                has_wall = False

    ET.SubElement(model, "static").text = "1"

    # Create the SDF tree and write it to the file
    sdf_tree = ET.ElementTree(sdf_root)
    sdf_tree.write(file_name + ".sdf", encoding="UTF-8", xml_declaration=True)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", type=str, help="Path to the input file", required=True)
    parser.add_argument("--type", type=str, help="Input file type", default=".jpg", required=False)
    parser.add_argument("--size", type=int, help="Image scale", default=200, required=False)
    parser.add_argument("--scale", type=float, help="Cell scale", default=0.1, required=False)
    parser.add_argument("--height", type=float, help="Wall Height", default=2.0, required=False)

    args = parser.parse_args()

    cell_height = args.height
    cell_scale = args.scale

    img_pre_process(args.name, args.type, scale=args.size)
    parse_jpg_to_sdf(args.name, args.type)
