import re
import sys
import xml.etree.ElementTree as ET
doc=ET.parse(sys.argv[1])
for node in doc.iter("node"):
    if "Create locally" in node.attrib.get("text",""):
        coords=list(map(int,re.findall(r"\d+",node.attrib["bounds"])))
        print((coords[0]+coords[2])//2,(coords[1]+coords[3])//2)
        break
else:
    raise SystemExit("Create button not found")
