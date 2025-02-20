from PIL import Image
from typing import Dict, List, Tuple, Optional
import os
from atlas_parser import AtlasParser, AtlasRegion, AtlasPage

class AtlasSplitter:
    def __init__(self, atlas_parser: AtlasParser):
        self.atlas_parser = atlas_parser
        self.images: Dict[str, Image.Image] = {}
        
    def load_page_images(self, atlas_dir: str) -> None:
        """Load all page images referenced in the atlas"""
        for page in self.atlas_parser.pages:
            image_path = os.path.join(atlas_dir, page.name)
            if not os.path.exists(image_path):
                raise FileNotFoundError(f"Atlas page image not found: {image_path}")
            self.images[page.name] = Image.open(image_path)
            
    def find_region(self, region_name: str) -> Tuple[Optional[AtlasPage], Optional[AtlasRegion]]:
        """Find a region and its data in the atlas pages"""
        for page in self.atlas_parser.pages:
            for region in page.regions:
                if region.name == region_name:
                    return page, region
        return None, None
            
    def extract_region(self, region_name: str) -> Tuple[Image.Image, Dict]:
        """Extract a single region from its page image"""
        print(f"\nExtracting region: {region_name}")
        page, region = self.find_region(region_name)
        if not page or not region:
            raise ValueError(f"Region not found: {region_name}")
            
        print(f"Found region in page: {page.name}")
        print(f"Region properties: xy=({region.xy}), size=({region.size}), "
              f"orig=({region.orig}), offset=({region.offset}), rotate={region.rotate}")
            
        source_image = self.images[page.name]
        x, y = region.xy
        width, height = region.size
        
        # Validate coordinates
        if x < 0 or y < 0 or x + width > source_image.width or y + height > source_image.height:
            print(f"Warning: Region {region_name} coordinates ({x}, {y}, {width}, {height}) "
                  f"exceed image bounds ({source_image.width}, {source_image.height})")
            # Adjust coordinates to fit within image bounds
            x = max(0, min(x, source_image.width - 1))
            y = max(0, min(y, source_image.height - 1))
            width = min(width, source_image.width - x)
            height = min(height, source_image.height - y)
            print(f"Adjusted coordinates: ({x}, {y}, {width}, {height})")
            
        try:
            # Extract the region
            region_image = source_image.crop((x, y, x + width, y + height))
            print(f"Successfully extracted region: {region_name} ({region_image.width}x{region_image.height})")
            
            # Handle rotation if needed
            if region.rotate:
                region_image = region_image.transpose(Image.ROTATE_90)
                print(f"Rotated region: {region_name} ({region_image.width}x{region_image.height})")
                
            region_data = {
                'name': region.name,
                'page': page.name,
                'orig': region.orig,
                'offset': region.offset,
                'rotate': region.rotate,
                'index': region.index
            }
                
            return region_image, region_data
        except Exception as e:
            print(f"Error extracting region {region_name}: {str(e)}")
            # Create a small placeholder image for failed extractions
            placeholder = Image.new('RGBA', (10, 10), (255, 0, 0, 128))
            return placeholder, region_data
        
    def create_combined_atlas(self, region_names: List[str]) -> Tuple[Image.Image, List[Dict]]:
        """Create a new atlas combining multiple regions using rectangle packing algorithm"""
        regions = []
        max_width = 0
        total_area = 0
        padding = 2  # Add some padding between regions
        
        # First pass: extract all regions and calculate dimensions
        for region_name in region_names:
            try:
                region_image, region_data = self.extract_region(region_name)
                regions.append((region_image, region_data))
                max_width = max(max_width, region_image.width)
                total_area += (region_image.width + padding) * (region_image.height + padding)
            except ValueError as e:
                print(f"Warning: {str(e)}")
                continue
                
        if not regions:
            raise ValueError("No valid regions to combine")
            
        # Sort regions by height in descending order (helps with packing efficiency)
        regions.sort(key=lambda x: x[0].height, reverse=True)
        
        # Calculate initial dimensions
        # Start with a square that can fit all regions (with some padding)
        initial_size = int((total_area * 1.1) ** 0.5)  # Add 10% for padding
        atlas_width = min(max(initial_size, max_width), 4096)  # Limit maximum width
        atlas_height = min(initial_size, 4096)  # Limit maximum height
        
        # Create new atlas image
        combined_image = Image.new('RGBA', (atlas_width, atlas_height), (0, 0, 0, 0))
        
        class Node:
            def __init__(self, x: int, y: int, width: int, height: int):
                self.x = x
                self.y = y
                self.width = width
                self.height = height
                self.used = False
                self.right = None
                self.down = None
                
            def find_node(self, width: int, height: int) -> Optional['Node']:
                if self.used:
                    return (self.right.find_node(width, height) or 
                           self.down.find_node(width, height))
                elif width <= self.width and height <= self.height:
                    return self
                return None
                
            def split(self, width: int, height: int) -> None:
                self.used = True
                self.down = Node(self.x, self.y + height + padding, 
                               self.width, self.height - height - padding)
                self.right = Node(self.x + width + padding, self.y,
                                self.width - width - padding, height)
        
        # Initialize the packing algorithm
        root = Node(0, 0, atlas_width, atlas_height)
        region_positions = []
        
        try:
            # Second pass: pack regions into the atlas
            for region_image, region_data in regions:
                node = root.find_node(region_image.width, region_image.height)
                
                if node:
                    # Place the region
                    combined_image.paste(region_image, (node.x, node.y))
                    
                    # Store position data
                    position_data = {
                        'name': region_data['name'],
                        'x': node.x,
                        'y': node.y,
                        'width': region_image.width,
                        'height': region_image.height,
                        'orig': region_data['orig'],
                        'offset': region_data['offset'],
                        'rotate': region_data['rotate'],
                        'index': region_data['index']
                    }
                    region_positions.append(position_data)
                    
                    # Split the node for future use
                    node.split(region_image.width, region_image.height)
                else:
                    print(f"Warning: Could not fit region {region_data['name']} in atlas")
                    
            # Trim unused space
            if region_positions:
                max_x = max(pos['x'] + pos['width'] for pos in region_positions)
                max_y = max(pos['y'] + pos['height'] for pos in region_positions)
                combined_image = combined_image.crop((0, 0, max_x + padding, max_y + padding))
                
            return combined_image, region_positions
        except Exception as e:
            print(f"Error creating combined atlas: {str(e)}")
            # Create a minimal valid image if combination fails
            fallback_image = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
            return fallback_image, region_positions
        
    def save_combined_atlas_data(self, atlas_path: str, image_name: str, region_positions: List[Dict]) -> None:
        """Save the atlas data file for the combined atlas"""
        with open(atlas_path, 'w', encoding='utf-8') as f:
            # Write atlas header
            f.write(f"{image_name}\n")
            f.write("size: 2048,2048\n")  # Default size, adjust if needed
            f.write("format: RGBA8888\n")
            f.write("filter: Linear,Linear\n")
            f.write("repeat: none\n\n")
            
            # Write region data
            for region in region_positions:
                f.write(f"{region['name']}\n")
                f.write(f"  rotate: {str(region['rotate']).lower()}\n")
                f.write(f"  xy: {region['x']}, {region['y']}\n")
                f.write(f"  size: {region['width']}, {region['height']}\n")
                f.write(f"  orig: {region['orig'][0]}, {region['orig'][1]}\n")
                f.write(f"  offset: {region['offset'][0]}, {region['offset'][1]}\n")
                f.write(f"  index: {region['index']}\n\n")
        
    def close(self) -> None:
        """Close all opened images"""
        for image in self.images.values():
            image.close() 