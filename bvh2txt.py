


import argparse





def get_rotation(ROTATION):
	# algortihm by Louis Miles

	#CHECK: [- Degree] or [+ Degree] or [0°]

	# [0°]
	if(ROTATION == 0):              
	    RESULT = 0

	# [+ Degree]
	if(ROTATION > 0):               
	    ROTATION = ROTATION * 45.51111111111111
	    ROTATION = 0 + ROTATION
	    RESULT = round(ROTATION)

	# [- Degree]
	if(ROTATION < 0):       
	    ROTATION = -1 * ROTATION    # [-] becomes [+]
	    ROTATION = ROTATION * 45.51111111111111
	    ROTATION = 65536 - ROTATION
	    ROTATION = round(ROTATION)
	    if(ROTATION == 65536):
	        RESULT = 0
	    else:
	        RESULT = ROTATION

	return RESULT



def read_file(filename):

	lines = []

	with open(filename, "r", encoding="utf-8", errors="ignore") as file:
		for line in file:
			lines.append(line.rstrip())


	return lines	



def new_joint():
	return {
		"type": "",
		"name": "", 
		"offset": [],
		"num_channels": 0, 
		"channels": [], 
		"subjoints": [],
		"framedata": [],
		"data": {
			"xpos": [],
			"ypos": [],
			"zpos": [],
			"xrot": [],
			"yrot": [],
			"zrot": []
		}
	}




def unpack_joint(j):

	joint = dict(j)

	if joint["type"] == "END":
		return []

	j_list = []

	for j in joint["subjoints"]:
		j_list = j_list + unpack_joint(j)

	del joint["subjoints"] 

	return [joint] + j_list




def parse_joints(LINES, sub_joint=False):

	LEN_LINES = len(LINES)

	JOINT_DATA = []

	if sub_joint:
		JOINT_LINES = LINES
	else:
		JOINT_LINES = [x.lstrip() for x in LINES]


	L_NUM = 0
	DATA_START = 0
	DATA_END = 0
	
	curr_joint = new_joint()

	while L_NUM < LEN_LINES:

		L = JOINT_LINES[L_NUM]
		line = L.split(" ")

		
		if line[0] == "ROOT":
			JOINT_DATA.append(curr_joint)
			curr_joint = new_joint()
			curr_joint["type"] = "ROOT"
			curr_joint["name"] = line[1]
		elif line[0] == "JOINT":
			JOINT_DATA.append(curr_joint)
			curr_joint = new_joint()
			curr_joint["type"] = "JOINT"
			curr_joint["name"] = line[1]
		elif line[0] == "End":
			JOINT_DATA.append(curr_joint)
			curr_joint = new_joint()
			curr_joint["type"] = "END"
			curr_joint["name"] = "End Site"

		elif line[0] == "{":
			ind = 1
			fnd = False
			brkt_num = 1
			while L_NUM + ind < LEN_LINES:
				if JOINT_LINES[L_NUM + ind] == "}": brkt_num -= 1

				elif JOINT_LINES[L_NUM + ind] == "{": brkt_num += 1
				
				if brkt_num == 0:
					fnd = True
					break

				ind += 1

			if not fnd:
				raise Exception("Improper Joint Data Format.\n" + "\n".join(LINES))

			
			j_data = parse_joints(JOINT_LINES[L_NUM+1:L_NUM+ind], sub_joint=True)

			L_NUM += ind


			if j_data != []:
				#curr_joint["name"] = j_data[0]["name"]
				curr_joint["offset"] = j_data[0]["offset"]
				curr_joint["channels"] = j_data[0]["channels"]
				curr_joint["num_channels"] = j_data[0]["num_channels"]
				curr_joint["subjoints"] = j_data[1:]

		elif line[0] == "OFFSET":
			curr_joint["offset"] = line[1:]

		elif line[0] == "CHANNELS":
			num_channels = int(line[1])
			curr_joint["num_channels"] = num_channels
			curr_joint["channels"] = line[2:]

		L_NUM += 1



	JOINT_DATA.append(curr_joint)


	

	if not sub_joint:
		return JOINT_DATA[1:]
	else:
		return JOINT_DATA
	



def parse_rotations(rot_data):

	if rot_data == []: rot_data.append([0, "0.0", 0])

	out = ""

	for r in rot_data:
		out += " [" + str(r[0]) + "," + str(get_rotation(float(r[1]))) + "," + str(r[0]) + "]"

	return out


def parse_translations(pos_data):

	if pos_data == []: pos_data.append([0, "0.0", 0])

	out = ""

	for t in pos_data:

		out += " [" + str(t[0]) + ","

		sp = t[1].split(".")

		i = int(sp[0])

		if len(sp) == 1: f = 0
		else:	f = int(sp[1])

		out += str(i) + "."

		if i == 0 and f == 0:
			out += "0"
		else:
			fs = str(f)
			out += fs + "0"*(14-len(fs))

		out += "," + str(t[2]) + "]"

	return out
		







def parse_bvh(filename):


	lines = read_file(filename)
	NUM_LINES = len(lines)


	ROOT_DATA = []

	in_hier = False
	in_motion = False

	L_NUM = 0

	while not in_hier and L_NUM < NUM_LINES:
		line = lines[L_NUM]

		if line == "HIERARCHY": in_hier = True

		L_NUM += 1



	JOINTS = []
	JOINTS_START = L_NUM

	while not in_motion and L_NUM < NUM_LINES:

		if lines[L_NUM] == "MOTION": in_motion = True

		L_NUM += 1

	JOINTS_END = L_NUM - 1

	if not in_motion:
		raise Exception("No Motion Tag Found.")

	JOINTS = parse_joints(lines[JOINTS_START:JOINTS_END])


	joints_list = []

	for j in JOINTS:
		joints_list = joints_list + unpack_joint(j)


	

	NUM_FRAMES = 0
	FRAME_TIME = 0.0

	if lines[L_NUM].split()[0] == "Frames:":
		NUM_FRAMES = int(lines[L_NUM][8:])
	else:
		raise Exception("Frames Tag not in bvh format.")

	L_NUM += 1

	if lines[L_NUM].split()[0] == "Frame" and lines[L_NUM].split()[1] == "Time:":
		FRAME_TIME = float(lines[L_NUM][13:])
	else:
		raise Exception("Frame Time Tag not in bvh format." + lines[L_NUM])

	L_NUM += 1



	for _ in range(NUM_FRAMES):
		ch_ind = 0
		ch_dat = []
		j_num = 0

		sp = lines[L_NUM].split()

		for ind in range(len(sp)):

			ch_dat.append(sp[ind])


			ch_ind += 1

			if ch_ind == joints_list[j_num]["num_channels"]:

				joints_list[j_num]["framedata"].append(ch_dat)

				j_num += 1
				ch_ind = 0


		L_NUM += 1


	

	# fix this later if there's any issues with the format

	output_data = []

	output_data.append("BCK Header")
	output_data.append("Loop Flags: 0")
	output_data.append("Angle Multiplier: 2")
	output_data.append("Animation Length: " + str(NUM_FRAMES))

	
	ch_num = 0
	for J in joints_list:
		
		for ch in J["channels"]:

			last_data = None
			f_num = 0
			for f in J["framedata"]:
				data = f[ch_num]
				if data != last_data:

					last_data = data

					chunk = [f_num, f[ch_num], 0]

					if ch == "Xposition":
						#print("appending x pos")
						J["data"]["xpos"].append(chunk)
					elif ch == "Yposition":
						#print("appending y pos")
						J["data"]["ypos"].append(chunk)
					elif ch == "Zposition":
						#print("appending z pos")
						J["data"]["zpos"].append(chunk)
					elif ch == "Xrotation":
						#print("appending x rot")
						J["data"]["xrot"].append(chunk)
					elif ch == "Yrotation":
						#print("appending y rot")
						J["data"]["yrot"].append(chunk)
					elif ch == "Zrotation":
						#print("appending z rot")
						J["data"]["zrot"].append(chunk)
					else:
						raise ValueError("unknown channel:" + str(ch))



				f_num += 1


			ch_num += 1


		output_data.append("\nJoint " + str(j_num))
		output_data.append("X Scale: [0,1.0,0]")
		output_data.append("X Rotation:" + parse_rotations(J["data"]["xrot"]))
		output_data.append("X Translation:" + parse_translations(J["data"]["xpos"]))
		output_data.append("Y Scale: [0,1.0,0]")
		output_data.append("Y Rotation:" + parse_rotations(J["data"]["yrot"]))
		output_data.append("Y Translation:" + parse_translations(J["data"]["ypos"]))
		output_data.append("Z Scale: [0,1.0,0]")
		output_data.append("Z Rotation:" + parse_rotations(J["data"]["zrot"]))
		output_data.append("Z Translation:" + parse_translations(J["data"]["zpos"]))




		j_num += 1


	return output_data









	


















if __name__ == "__main__":

	parser = argparse.ArgumentParser(description="Convert a bvh file into the relevant animation txt file.")

	parser.add_argument("file", type=str, help="Name of file to convert")

	#parser.add_argument("-o", dest="outfile", type=str, help="Name of file to convert")


	OUTPUT_F = None
	INPUT_F = None

	ARGS = vars(parser.parse_args())

	INPUT_F = ARGS["file"].replace("\\", "/")

	if "outfile" in ARGS:
		OUTPUT_F = ARGS["outfile"]

	if OUTPUT_F == None:
		sp = INPUT_F.split("/")

		pth = "/".join(sp[:-1])
		if pth != "": pth += "/"


		OUTPUT_F = pth + ".".join(sp[-1].split(".")[:-1]) + ".txt"



	#print(INPUT_F)

	j_data = parse_bvh(INPUT_F)

	with open(OUTPUT_F, "w", encoding="utf-8") as F:
		FIRST_LINE = True
		for line in j_data:
			if FIRST_LINE: FIRST_LINE = False
			else:	F.write("\n")
			F.write(line)

