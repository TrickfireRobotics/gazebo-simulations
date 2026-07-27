"""STL mesh triangle-count reduction via trimesh + pyfqmr"""

import glob
import os
import shutil

from ...output import info


def _imports():
    try:
        import pyfqmr  # type: ignore
        import trimesh  # type: ignore

        return trimesh, pyfqmr
    except ImportError as exc:
        raise SystemExit(
            "trimesh and pyfqmr are required for STL reduction but are not installed.\n"
            " └─ pip install trimesh pyfqmr\n"
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
    trimesh, pyfqmr = _imports()
    og_fsize = os.path.getsize(input_file_path)
    mesh = trimesh.load(input_file_path, force="mesh")
    og_len = len(mesh.faces)

    if og_len <= target_triangles:
        print(f"Mesh {input_file_path} is already below target. Saving as is.\n")
        mesh.export(output_file_path)
        return []

    simplifier = pyfqmr.Simplify()
    simplifier.setMesh(mesh.vertices, mesh.faces)
    simplifier.simplify_mesh(target_count=target_triangles, aggressiveness=7, verbose=False)
    vertices, faces, normals = simplifier.getMesh()

    result = trimesh.Trimesh(vertices=vertices, faces=faces, vertex_normals=normals)
    result.export(output_file_path)
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

    trimesh, _pyfqmr = _imports()
    for file_path in stl_files:
        filename = os.path.basename(file_path)
        out_path = os.path.join(output_dir, filename)
        mesh = trimesh.load(file_path, force="mesh")
        target = int(len(mesh.faces) * reduction_ratio)
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
