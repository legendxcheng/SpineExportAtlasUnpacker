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
        # Only log for b_00016 or if there's an error
        is_target = region_name == "b_00016"
        if is_target:
            print(f"\n=== Processing target region: {region_name} ===")
            
        page, region = self.find_region(region_name)
        if not page or not region:
            raise ValueError(f"Region not found: {region_name}")
            
        if is_target:
            print(f"Found in page: {page.name}")
            print(f"Region data:")
            print(f"  - xy: ({region.xy[0]}, {region.xy[1]})")
            print(f"  - size: ({region.size[0]}, {region.size[1]})")
            print(f"  - orig: ({region.orig[0]}, {region.orig[1]})")
            print(f"  - offset: ({region.offset[0]}, {region.offset[1]})")
            print(f"  - rotate: {region.rotate}")
            
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
            if is_target:
                print(f"Adjusted coordinates: ({x}, {y}, {width}, {height})")
            
        try:
            # Extract the region
            region_image = source_image.crop((x, y, x + width, y + height))
            if is_target:
                print(f"Extracted region size: {region_image.width}x{region_image.height}")
            
            # Handle rotation if needed
            if region.rotate:
                region_image = region_image.transpose(Image.ROTATE_90)
                if is_target:
                    print(f"After rotation: {region_image.width}x{region_image.height}")
            
            region_data = {
                'name': region.name,
                'orig': region.orig,
                'offset': region.offset,
                'rotate': region.rotate,
                'index': region.index
            }
            
            if is_target:
                print("=== Extraction completed successfully ===\n")
            
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
        max_height = 0
        total_area = 0
        padding = 2  # Add some padding between regions
        
        print("\n=== Atlas Creation Process ===")
        print(f"Total regions to process: {len(region_names)}")
        
        # First pass: extract all regions and calculate dimensions
        for region_name in region_names:
            try:
                region_image, region_data = self.extract_region(region_name)
                regions.append((region_image, region_data))
                max_width = max(max_width, region_image.width)
                max_height = max(max_height, region_image.height)
                total_area += (region_image.width + padding) * (region_image.height + padding)
            except ValueError as e:
                print(f"Warning: {str(e)}")
                continue
                
        if not regions:
            raise ValueError("No valid regions to combine")
            
        # Sort regions by height in descending order (helps with packing efficiency)
        regions.sort(key=lambda x: (
            x[0].width * x[0].height,  # First sort by area
            max(x[0].width, x[0].height)  # Then by max dimension
        ), reverse=True)
        
        # Calculate initial dimensions
        # Start with dimensions that can fit all regions (with some padding)
        initial_size = int((total_area * 1.3) ** 0.5)  # Slightly increase padding to 30%
        atlas_width = max(initial_size, max_width + padding)
        atlas_height = max(initial_size, max_height + padding)
        
        print(f"\nAtlas dimensions:")
        print(f"  - Total area of all regions: {total_area}")
        print(f"  - Initial calculated size: {initial_size}")
        print(f"  - Final atlas size: {atlas_width}x{atlas_height}")
        
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
                # Try rotating the region if it doesn't fit
                elif height <= self.width and width <= self.height:
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
                region_name = region_data['name']
                if region_name in ['b_00016', 'b_00017']:
                    print(f"\nTrying to pack {region_name}:")
                    print(f"  Region size: {region_image.width}x{region_image.height}")
                    print(f"  Available atlas space: {atlas_width}x{atlas_height}")
                
                # Try both orientations
                node = root.find_node(region_image.width, region_image.height)
                rotated = False
                
                if not node:
                    # Try rotating the region
                    node = root.find_node(region_image.height, region_image.width)
                    if node and region_name in ['b_00016', 'b_00017']:
                        print(f"  Found space after rotation")
                    if node:
                        rotated = True
                        region_image = region_image.transpose(Image.ROTATE_90)
                
                if node:
                    if region_name in ['b_00016', 'b_00017']:
                        print(f"  Successfully placed at: ({node.x}, {node.y})")
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
                        'rotate': rotated,
                        'index': region_data['index']
                    }
                    region_positions.append(position_data)
                    
                    # Split the node for future use
                    node.split(region_image.width, region_image.height)
                else:
                    if region_name in ['b_00016', 'b_00017']:
                        print(f"  Failed to find space in both orientations")
                    print(f"Warning: Could not fit region {region_data['name']} in atlas")
                    
            # Trim unused space
            if region_positions:
                max_x = max(pos['x'] + pos['width'] for pos in region_positions)
                max_y = max(pos['y'] + pos['height'] for pos in region_positions)
                combined_image = combined_image.crop((0, 0, max_x + padding, max_y + padding))
                print(f"\nFinal atlas size after trimming: {max_x + padding}x{max_y + padding}")
                
            return combined_image, region_positions
        except Exception as e:
            print(f"Error creating combined atlas: {str(e)}")
            # Create a minimal valid image if combination fails
            fallback_image = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
            return fallback_image, region_positions
        
    def save_combined_atlas_data(self, atlas_path: str, image_name: str, region_positions: List[Dict]) -> None:
        """Save the atlas data file for the combined atlas"""
        # Get the actual image dimensions
        image_path = os.path.join(os.path.dirname(atlas_path), image_name)
        with Image.open(image_path) as img:
            actual_width, actual_height = img.size
            
        # Write atlas header
        with open(atlas_path, 'w', encoding='utf-8') as f:
            f.write(f"{image_name}\n")
            f.write(f"size: {actual_width},{actual_height}\n")
            f.write("format: RGBA8888\n")
            f.write("filter: Linear,Linear\n")
            f.write("repeat: none\n")
            
            # Create a map of the new positions
            region_map = {pos['name']: pos for pos in region_positions}
            
            # Write all regions in the original order, preserving those not in the new atlas
            for page in self.atlas_parser.pages:
                for region in page.regions:
                    f.write(f"{region.name}\n")
                    if region.name in region_map:
                        # Use new position data
                        pos = region_map[region.name]
                        f.write(f"  rotate: {str(pos['rotate']).lower()}\n")
                        f.write(f"  xy: {pos['x']}, {pos['y']}\n")
                        f.write(f"  size: {pos['width']}, {pos['height']}\n")
                        f.write(f"  orig: {pos['orig'][0]}, {pos['orig'][1]}\n")
                        f.write(f"  offset: {pos['offset'][0]}, {pos['offset'][1]}\n")
                        f.write(f"  index: {pos['index']}\n")
                    else:
                        # Keep original data for regions not in the new atlas
                        f.write(f"  rotate: {str(region.rotate).lower()}\n")
                        f.write(f"  xy: {region.xy[0]}, {region.xy[1]}\n")
                        f.write(f"  size: {region.size[0]}, {region.size[1]}\n")
                        f.write(f"  orig: {region.orig[0]}, {region.orig[1]}\n")
                        f.write(f"  offset: {region.offset[0]}, {region.offset[1]}\n")
                        f.write(f"  index: {region.index}\n")
        
    def close(self) -> None:
        """Close all opened images"""
        for image in self.images.values():
            image.close() 