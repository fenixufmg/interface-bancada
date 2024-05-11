from cx_Freeze import setup, Executable
import os

base = None    

executables = [Executable("main.py", base=base)]

def include_OpenGL(vers=64):
    if vers == 64:
        lib = "lib64"
    else:
        lib = "lib"

    path_base = os.path.abspath(f"{lib}/python3.10/site-packages/OpenGL") 
    skip_count = len(path_base) 
    zip_includes = [(path_base, "OpenGL")]
    for root, sub_folders, files in os.walk(path_base):
        for file_in_root in files:
            zip_includes.append(
                    ("{}".format(os.path.join(root, file_in_root)),
                     "{}".format(os.path.join("OpenGL", root[skip_count+1:], file_in_root))
                    ) 
            )      
    return zip_includes

# def include_images():
#     path_base = os.path.abspath(f"{lib}/python3.10/site-packages/OpenGL") 
#     skip_count = len(path_base) 
#     zip_includes = [(path_base, "OpenGL")]
#     for root, sub_folders, files in os.walk(path_base):
#         for file_in_root in files:
#             zip_includes.append(
#                     ("{}".format(os.path.join(root, file_in_root)),
#                      "{}".format(os.path.join("OpenGL", root[skip_count+1:], file_in_root))
#                     ) 
#             )      
#     return zip_includes

packages = ["idna", "PyQt5","pyqtgraph","serial","pygame"]
options = {
    'build_exe': { 
        'packages': packages,   
        'zip_includes':include_OpenGL(),
        'include_files':["./fenix.png"],
    },    
}

setup(
    name = "benchface",
    options = options,
    version = "1.0.0",
    description = 'Interface for the fenix workbench',
    executables = executables,
    maintainer = "davi"
)