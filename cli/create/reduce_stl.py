"""STL mesh triangle-count reduction via open3d."""

import glob
import os
import shutil

from ..output import info


def _o3d():
    try:
        import open3d as o3d  # type: ignore

        return o3d
    except ImportError as exc:
        raise SystemExit(
            "open3d is required for STL reduction but is not installed.\n"
            " └─ pip install open3d\n"
            "    Or skip reduction with --no-reduce"
        ) from exc


MIN_TRIANGLES = 200


def reduce_file_size(
    input_file_path: str, output_file_path: str, target_triangles: int
) -> list[int]:
    """
    Reduce the number of triangles in the STL file to target_triangles and save to output_file_path.
    Returns original and new file sizes
    """
    o3d = _o3d()
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
    return [og_fsize, new_fsize]


def batch_process_directory(input_dir: str, output_dir: str, reduction_ratio: float = 0.4) -> None:
    """Reduce STL files in input_dir and save to output_dir, keeping .part files as is"""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    stl_files = glob.glob(os.path.join(input_dir, "*.stl"))
    part_files = glob.glob(os.path.join(input_dir, "*.part"))
    old_file_size = 0
    new_file_size = 0

    o3d = _o3d()
    for file_path in stl_files:
        filename = os.path.basename(file_path)
        out_path = os.path.join(output_dir, filename)
        mesh = o3d.io.read_triangle_mesh(file_path)
        target = int(len(mesh.triangles) * reduction_ratio)
        r = reduce_file_size(file_path, out_path, target)
        if r:
            old_file_size += r[0]
            new_file_size += r[1]

    info(f"Reduced STL folder size from {old_file_size // 1000} kb to {new_file_size // 1000} kb")

    for file_path in part_files:
        filename = os.path.basename(file_path)
        out_path = os.path.join(output_dir, filename)
        if os.path.abspath(file_path) != os.path.abspath(out_path):
            shutil.copy(file_path, out_path)
