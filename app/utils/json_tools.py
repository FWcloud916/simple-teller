# json tools
from pathlib import Path


def read_file(file_path: str) -> str:
    """
    Read file content
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File {file_path} not found")
    with path.open("r", encoding="utf-8") as file:
        return file.read()
