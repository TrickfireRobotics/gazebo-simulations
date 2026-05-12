"""Template rendering"""

from pathlib import Path


def populate_template(template_path: Path, robot: str, **extras) -> str:
    text = template_path.read_text()
    text = text.replace("__ROBOT__", robot)
    for key, value in extras.items():
        text = text.replace(f"__{key}__", value)
    return text


def write_template(src: Path, dest: Path, robot: str, **extras) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(populate_template(src, robot, **extras))
