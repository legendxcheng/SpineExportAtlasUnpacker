# Spine Export Atlas Unpacker

A Python tool for modifying Spine animation resources to ensure each animation uses its own texture atlas.

## Features

- Processes Spine animation files (.json/.skel)
- Extracts and separates texture atlases for each animation
- Modifies animation files to reference their individual atlases
- Maintains animation quality and integrity

## Requirements

- Python 3.8+
- Pillow (PIL)
- json

## Installation

1. Clone this repository:
```bash
git clone https://github.com/yourusername/SpineExportAtlasUnpacker.git
cd SpineExportAtlasUnpacker
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

```bash
python spine_unpacker.py <input_spine_file> <output_directory>
```

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.