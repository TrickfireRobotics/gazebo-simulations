"""
Used to reduce the triangle count for STL files to bring down file size
"""

import glob
import os
import shutil
import sys
import open3d as o3d  # type: ignore
from . import log

# Anything less than this it leaves holes in certain meshes that make it visually offputting
MIN_TRIANGLES = 200


def reduce_file_size(input_file_path: str, output_file_path: str, target_triangles) -> list[int]:
    """Reduces the triangle count of a STL file passed to the method"""
    og_fsize = os.path.getsize(input_file_path)

    mesh = o3d.io.read_triangle_mesh(input_file_path)
    og_len = len(mesh.triangles)

    if og_len <= target_triangles:
        print(f"Mesh {input_file_path} is already below target. Saving as is.\n")
        o3d.io.write_triangle_mesh(output_file_path, mesh, write_ascii=False)
        return []
    decimated_mesh = mesh.simplify_quadric_decimation(target_number_of_triangles=target_triangles)
    decimated_mesh.compute_vertex_normals()
    o3d.io.write_triangle_mesh(output_file_path, decimated_mesh, write_ascii=False)
    new_fsize = os.path.getsize(output_file_path)
    r = []
    r.append(og_fsize)
    r.append(new_fsize)
    return r


def batch_process_directory(input_dir, output_dir, reduction_ratio=0.4):
    """
    Reads all STLs in a folder and reduces them to a percentage of their original size.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Find all STL files in the input directory
    stl_files = glob.glob(os.path.join(input_dir, "*.stl"))
    part_files = glob.glob(os.path.join(input_dir, "*.part"))
    old_file_size = 0
    new_file_size = 0

    for file_path in stl_files:
        filename = os.path.basename(file_path)
        out_path = os.path.join(output_dir, filename)

        # Read just to get current triangle count so we can apply the ratio
        mesh = o3d.io.read_triangle_mesh(file_path)
        current_triangles = len(mesh.triangles)

        target = int(current_triangles * reduction_ratio)

        r = reduce_file_size(file_path, out_path, target)
        if not len(r) == 0:
            old_file_size += r[0]
            new_file_size += r[1]
    old_file_size = old_file_size // 1000
    new_file_size = new_file_size // 1000
    log.info(f"Reduced stl folder size from {old_file_size} kb to {new_file_size} kb")

    # copy the rest of the .part files
    for file_path in part_files:
        filename = os.path.basename(file_path)
        out_path = os.path.join(output_dir, filename)
        if os.path.abspath(file_path) != os.path.abspath(out_path):
            shutil.copy(file_path, out_path)


def main():
    """Main method"""
    if len(sys.argv) == 4:
        batch_process_directory(sys.argv[1], sys.argv[2], float(sys.argv[3]))
    elif len(sys.argv) == 3:
        batch_process_directory(sys.argv[1], sys.argv[2])
    else:
        print("Invalid arguments passed please try again")


if __name__ == "__main__":
    main()
