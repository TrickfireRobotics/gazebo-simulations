"""Template rendering for genbot."""

from pathlib import Path


def render(template_path: Path, robot: str, **extras) -> str:
    """Read a template and substitute __ROBOT__ (and any extras) into it"""
    text = template_path.read_text()
    text = text.replace("__ROBOT__", robot)
    for key, value in extras.items():
        text = text.replace(f"__{key}__", value)
    return text


def write_template(src: Path, dest: Path, robot: str, **extras) -> None:
    """Writes a template file"""
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(render(src, robot, **extras))
