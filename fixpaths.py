import os

#For this to work place urdf file in the same folder path as the urdf file

#Keep this the same this is the package name we made
PACKAGE_NAME = "models_and_worlds"


#Hard coded for now, can automate later
INPUT_FILE = "arm.urdf"
OUTPUT_FILE = "arm_fixed.urdf"


#Keep this false for now, we arent implementing any sdf models
USE_GAZEBO_MODEL_PATH = False


GAZEBO_MODEL_NAME = "arm"

def fix_paths():
    
    if USE_GAZEBO_MODEL_PATH:
        prefix = f"model://{GAZEBO_MODEL_NAME}/"
    else:
        #Automatically replaces our package name with the gazebo model we are trying to fix the urdf file for
        prefix = f"package://{PACKAGE_NAME}/models/{GAZEBO_MODEL_NAME}"

    print(f"Processing '{INPUT_FILE}'...")
    print(f"Target Prefix: {prefix}")

    try:
        with open(INPUT_FILE, "r") as f:
            content = f.read()

        #opens the file and stores it in a string called 'content'
        
        #replaces all instances of bad model string
        new_content = content.replace('filename="assets/', f'filename="{prefix}assets/')
        
        # Handle single quotes just in case
        new_content = new_content.replace("filename='assets/", f"filename='{prefix}assets/")

        #Opens a new file and writes our new string into that file
        with open(OUTPUT_FILE, "w") as f:
            f.write(new_content)
            
        print("-" * 30)
        print(f"SUCCESS! Created '{OUTPUT_FILE}'")
        print("You can now use this new file in your launch configuration.")

    except FileNotFoundError:
        print(f"ERROR: Could not find '{INPUT_FILE}'. Please ensure the XML file is in the same folder.")
if __name__ == "__main__":
    fix_paths()
