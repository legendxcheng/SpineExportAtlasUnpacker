from dataclasses import dataclass
from typing import List, Dict, Optional
import re

@dataclass
class AtlasRegion:
    name: str
    xy: tuple[int, int]
    size: tuple[int, int]
    orig: tuple[int, int]
    offset: tuple[int, int]
    rotate: bool
    index: int

class AtlasPage:
    def __init__(self, name: str):
        self.name = name
        self.size: Optional[tuple[int, int]] = None
        self.format: str = ""
        self.filter: tuple[str, str] = ("", "")
        self.repeat: str = ""
        self.regions: List[AtlasRegion] = []

class AtlasParser:
    def __init__(self):
        self.pages: List[AtlasPage] = []
        self._current_page: Optional[AtlasPage] = None
        
    def validate_parsing(self) -> None:
        """Validate that all regions were parsed correctly"""
        print("\nValidating parsing results:")
        for page in self.pages:
            print(f"\nPage: {page.name}")
            print(f"Page properties: size={page.size}, format={page.format}, "
                  f"filter={page.filter}, repeat={page.repeat}")
            
            for region in page.regions:
                if region.xy == (0, 0) and region.size == (0, 0):
                    print(f"Warning: Region {region.name} has invalid coordinates or size!")
                print(f"  Region: {region.name}")
                print(f"    xy: {region.xy}")
                print(f"    size: {region.size}")
                print(f"    orig: {region.orig}")
                print(f"    offset: {region.offset}")
                print(f"    rotate: {region.rotate}")
                print(f"    index: {region.index}")
                
    def parse_file(self, atlas_path: str) -> None:
        """Parse a Spine atlas file"""
        print(f"Parsing atlas file: {atlas_path}")
        with open(atlas_path, 'r', encoding='utf-8') as f:
            lines = [line.rstrip('\n') for line in f.readlines()]  # Only remove newlines, keep spaces
            
        i = 0
        parsing_page_properties = False
        
        while i < len(lines):
            line = lines[i]
            line_stripped = line.strip()
            print(f"Line {i}: {line}")
            
            # Skip empty lines
            if not line_stripped:
                parsing_page_properties = False
                i += 1
                continue
                
            # New page starts with a non-indented line that ends with .png
            if not line.startswith(' ') and line_stripped.endswith('.png'):
                print(f"Found page: {line}")
                self._current_page = AtlasPage(line_stripped)
                self.pages.append(self._current_page)
                parsing_page_properties = True  # Start parsing page properties
                i += 1
                continue
                    
            # Parse page properties
            if parsing_page_properties and ':' in line_stripped:
                print(f"Parsing page property: {line}")
                i = self._parse_page_property(lines, i)
                i += 1
                continue
                    
            # Parse region (only if we're not parsing page properties and line doesn't contain ':')
            if self._current_page is not None and not parsing_page_properties and not ':' in line_stripped and not line.startswith(' '):
                print(f"Found region: {line}")
                next_i = self._parse_region_property(lines, i)
                if next_i <= i:  # 防止索引没有前进
                    i += 1
                else:
                    i = next_i + 1  # 跳过已处理的行
                continue
                
            # If we get here with a non-indented line, stop parsing page properties
            if not line.startswith(' '):
                parsing_page_properties = False
                
            i += 1
            
        print(f"Parsed {len(self.pages)} pages with {sum(len(page.regions) for page in self.pages)} regions")
        self.validate_parsing()
        
    def _parse_page_property(self, lines: List[str], i: int) -> int:
        """Parse a page property line"""
        line = lines[i]
        line_stripped = line.strip()
        if ':' not in line_stripped:
            return i
            
        key, value = [x.strip() for x in line_stripped.split(':', 1)]
        print(f"  Setting page property: {key} = {value}")
        
        try:
            if key == 'size':
                w, h = map(int, value.replace(' ', '').split(','))
                self._current_page.size = (w, h)
            elif key == 'format':
                self._current_page.format = value
            elif key == 'filter':
                min_filter, mag_filter = value.split(',')
                self._current_page.filter = (min_filter.strip(), mag_filter.strip())
            elif key == 'repeat':
                self._current_page.repeat = value
        except Exception as e:
            print(f"Warning: Failed to parse page property {key}: {str(e)}")
            
        return i
        
    def _parse_region_property(self, lines: List[str], i: int) -> int:
        """Parse a region and its properties"""
        line = lines[i]
        line_stripped = line.strip()
        if ':' in line_stripped:  # Skip lines that look like properties
            return i
            
        print(f"\nParsing properties for region: {line_stripped}")
        
        # Initialize region with default values
        region = AtlasRegion(
            name=line_stripped,
            xy=(0, 0),
            size=(0, 0),
            orig=(0, 0),
            offset=(0, 0),
            rotate=False,
            index=-1
        )
        
        # Parse region properties
        next_line = i + 1
        properties_found = False  # Track if we found any properties
        
        while next_line < len(lines):
            line = lines[next_line]
            line_stripped = line.strip()
            
            # End of region properties when we hit a non-empty line without indentation
            if line_stripped and not line.startswith('  '):
                break
                
            # Process property lines (they should be indented and contain ':')
            if line.startswith('  ') and ':' in line_stripped:
                print(f"  Processing line: {line}")
                try:
                    # Split the line into key and value, handling extra spaces
                    parts = line_stripped.split(':', 1)
                    if len(parts) == 2:
                        key = parts[0].strip()
                        value = parts[1].strip()
                        properties_found = True  # Mark that we found at least one property
                        
                        if key == 'rotate':
                            region.rotate = value.lower() == 'true'
                            print(f"    Set rotate: {region.rotate}")
                        elif key == 'xy':
                            x, y = map(int, value.replace(' ', '').split(','))
                            region.xy = (x, y)
                            print(f"    Set xy: {region.xy}")
                        elif key == 'size':
                            w, h = map(int, value.replace(' ', '').split(','))
                            region.size = (w, h)
                            print(f"    Set size: {region.size}")
                        elif key == 'orig':
                            w, h = map(int, value.replace(' ', '').split(','))
                            region.orig = (w, h)
                            print(f"    Set orig: {region.orig}")
                        elif key == 'offset':
                            x, y = map(int, value.replace(' ', '').split(','))
                            region.offset = (x, y)
                            print(f"    Set offset: {region.offset}")
                        elif key == 'index':
                            region.index = int(value)
                            print(f"    Set index: {region.index}")
                except Exception as e:
                    print(f"Warning: Failed to parse property in line '{line}': {str(e)}")
            
            next_line += 1
            
        if properties_found:
            print(f"Finished parsing region: {line_stripped} - xy={region.xy}, size={region.size}, "
                  f"orig={region.orig}, offset={region.offset}, rotate={region.rotate}")
            if self._current_page is not None:
                self._current_page.regions.append(region)
            else:
                print(f"Warning: No current page to add region {line_stripped} to!")
        else:
            print(f"Warning: No properties found for region {line_stripped}")
            
        return next_line - 1
        
    def save_atlas(self, output_path: str) -> None:
        """Save the atlas data to a file"""
        with open(output_path, 'w', encoding='utf-8') as f:
            for page in self.pages:
                # Write page name
                f.write(f"{page.name}\n")
                
                # Write page properties
                if page.size:
                    f.write(f"size: {page.size[0]}, {page.size[1]}\n")
                if page.format:
                    f.write(f"format: {page.format}\n")
                if page.filter[0] and page.filter[1]:
                    f.write(f"filter: {page.filter[0]}, {page.filter[1]}\n")
                if page.repeat:
                    f.write(f"repeat: {page.repeat}\n")
                    
                # Write regions
                for region in page.regions:
                    f.write(f"\n{region.name}\n")
                    f.write(f"  rotate: {str(region.rotate).lower()}\n")
                    f.write(f"  xy: {region.xy[0]}, {region.xy[1]}\n")
                    f.write(f"  size: {region.size[0]}, {region.size[1]}\n")
                    f.write(f"  orig: {region.orig[0]}, {region.orig[1]}\n")
                    f.write(f"  offset: {region.offset[0]}, {region.offset[1]}\n")
                    if region.index >= 0:
                        f.write(f"  index: {region.index}\n")
                        
                f.write("\n") 