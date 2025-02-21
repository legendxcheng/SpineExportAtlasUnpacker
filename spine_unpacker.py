#!/usr/bin/env python3
import os
from PIL import Image
from atlas_parser import AtlasParser
from atlas_splitter import AtlasSplitter

# Default spine file name
spine_name = 'xingxingdaojubaodian.json'

class SpineAtlasUnpacker:
    def __init__(self, spine_file: str, output_dir: str):
        """
        Initialize the SpineAtlasUnpacker with input file and output directory
        
        Args:
            spine_file (str): Path to the Spine animation file (.json/.skel)
            output_dir (str): Directory where the processed files will be saved
        """
        self.spine_file = spine_file
        self.output_dir = output_dir
        self.atlas_parser = AtlasParser()
        
    def load_atlas_file(self) -> None:
        """Load and parse the atlas file with the same name as spine file"""
        atlas_file = os.path.splitext(self.spine_file)[0] + '.atlas'
        if not os.path.exists(atlas_file):
            raise FileNotFoundError(f"Atlas file not found: {atlas_file}")
            
        self.atlas_file = atlas_file
        self.atlas_parser.parse_file(atlas_file)
        
    def process_atlas(self) -> None:
        """Process the atlas and create a new combined atlas"""
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            
        # Create atlas splitter
        splitter = AtlasSplitter(self.atlas_parser)
        
        # Load atlas page images
        atlas_dir = os.path.dirname(self.atlas_file)
        splitter.load_page_images(atlas_dir)
        
        try:
            # Get all regions from the atlas
            all_regions = []
            for page in self.atlas_parser.pages:
                for region in page.regions:
                    all_regions.append(region.name)
                    print(f"Found region: {region.name}")
            
            if not all_regions:
                print("Warning: No regions found in atlas")
                return

            print(f"Total regions to process: {len(all_regions)}")
            print(f"Regions: {sorted(all_regions)}")

            # Create a new combined atlas
            try:
                # Generate new atlas image and data
                new_atlas_name = os.path.splitext(os.path.basename(self.spine_file))[0]
                new_atlas_path = os.path.join(self.output_dir, f"{new_atlas_name}.png")
                new_atlas_data_path = os.path.join(self.output_dir, f"{new_atlas_name}.atlas")
                
                # Extract and combine regions into new atlas
                combined_image, region_positions = splitter.create_combined_atlas(all_regions)
                combined_image.save(new_atlas_path)
                
                print(f"Region positions data:")
                for pos in region_positions:
                    print(f"  {pos['name']}: xy=({pos['x']}, {pos['y']}), size=({pos['width']}, {pos['height']})")
                
                # Create and save new atlas data file
                splitter.save_combined_atlas_data(
                    new_atlas_data_path,
                    os.path.basename(new_atlas_path),  # Use the new PNG filename
                    region_positions
                )
                
                print(f"Created combined atlas with {len(region_positions)} regions")
                
            except Exception as e:
                print(f"Error creating combined atlas: {str(e)}")
                import traceback
                traceback.print_exc()
                    
        finally:
            # Clean up
            splitter.close()
            
    def process(self) -> None:
        """Main processing function"""
        self.load_atlas_file()
        self.process_atlas()

def main():
    parser = argparse.ArgumentParser(
        description='Unpack Spine animation resources to use individual atlases'
    )
    parser.add_argument(
        'spine_file',
        nargs='?',  # Make the argument optional
        default=f'./propArrive/{spine_name}',  # Default spine file path
        help=f'Path to the Spine animation file (default: ./propArrive/{spine_name})'
    )
    parser.add_argument(
        'output_dir',
        nargs='?',  # Make the argument optional
        default='./output',  # Default output directory
        help='Output directory for processed files (default: ./output)'
    )
    
    args = parser.parse_args()
    
    try:
        unpacker = SpineAtlasUnpacker(args.spine_file, args.output_dir)
        unpacker.process()
        print(f"Processing completed successfully!")
        print(f"Input file: {args.spine_file}")
        print(f"Output directory: {args.output_dir}")
    except Exception as e:
        print(f"Error: {str(e)}")
        return 1
    
    return 0

if __name__ == '__main__':
    import argparse
    exit(main()) 