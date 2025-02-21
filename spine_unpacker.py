#!/usr/bin/env python3
import os
import json
import argparse
from PIL import Image
from typing import Dict, List, Tuple
import shutil
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
        self.spine_data = None
        self.atlas_parser = AtlasParser()
        
    def load_spine_file(self) -> None:
        """Load and parse the Spine animation file"""
        if not os.path.exists(self.spine_file):
            raise FileNotFoundError(f"Spine file not found: {self.spine_file}")
            
        with open(self.spine_file, 'r', encoding='utf-8') as f:
            self.spine_data = json.load(f)
            
    def load_atlas_file(self) -> None:
        """Load and parse the atlas file"""
        atlas_file = os.path.splitext(self.spine_file)[0] + '.atlas'
        if not os.path.exists(atlas_file):
            raise FileNotFoundError(f"Atlas file not found: {atlas_file}")
            
        self.atlas_file = atlas_file
        self.atlas_parser.parse_file(atlas_file)
        
    def process_animation(self) -> None:
        """Process the animation and create separate atlases"""
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            
        # Create atlas splitter
        splitter = AtlasSplitter(self.atlas_parser)
        
        # Load atlas page images
        atlas_dir = os.path.dirname(self.atlas_file)
        splitter.load_page_images(atlas_dir)
        
        try:
            # Process all skins in the Spine data
            if 'skins' in self.spine_data:
                skins_data = self.spine_data['skins']
                
                # Handle both dictionary and list formats
                if isinstance(skins_data, dict):
                    # Format: {"skinName": {attachments...}}
                    skins_to_process = skins_data.items()
                else:
                    # Format: [{"name": "skinName", "attachments": {attachments...}}]
                    skins_to_process = [(skin.get('name', f'skin_{i}'), skin.get('attachments', {})) 
                                      for i, skin in enumerate(skins_data)]
                
                # Collect all unique regions from all skins
                all_regions = set()
                for skin_name, skin_data in skins_to_process:
                    print(f"Collecting regions from skin: {skin_name}")
                    
                    # Get all attachments for this skin
                    if isinstance(skin_data, dict):
                        attachments = list(skin_data.values())
                    else:
                        print(f"Warning: Unexpected skin data format for skin {skin_name}")
                        print(f"Skin data: {skin_data}")
                        continue

                    # Extract all required regions from the atlas
                    for attachment in attachments:
                        for attachment_name, attachment_data in attachment.items():
                            if isinstance(attachment_data, dict):
                                # Skip clipping regions
                                if attachment_data.get('type') == 'clipping':
                                    continue
                                # If the attachment has a name field, use that as the region name
                                region_name = attachment_data.get('name', attachment_name)
                                if not region_name in all_regions:
                                    all_regions.add(region_name)
                                    print(f"Added region: {region_name}")
                
                if not all_regions:
                    print("Warning: No valid regions found in any skin")
                    return

                print(f"Total regions to process: {len(all_regions)}")
                print(f"Regions: {sorted(list(all_regions))}")

                # Create a single atlas for all skins
                try:
                    # Generate new atlas image and data
                    new_atlas_name = os.path.splitext(spine_name)[0]  # Get name without extension
                    new_atlas_path = os.path.join(self.output_dir, f"{new_atlas_name}.png")
                    new_atlas_data_path = os.path.join(self.output_dir, f"{new_atlas_name}.atlas")
                    
                    # Extract and combine regions into new atlas
                    combined_image, region_positions = splitter.create_combined_atlas(list(all_regions))
                    combined_image.save(new_atlas_path)
                    
                    print(f"Region positions data:")
                    for pos in region_positions:
                        print(f"  {pos['name']}: xy=({pos['x']}, {pos['y']}), size=({pos['width']}, {pos['height']})")
                    
                    # Create and save new atlas data file
                    splitter.save_combined_atlas_data(
                        new_atlas_data_path,
                        new_atlas_name + ".png",
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
            
    def save_modified_spine_file(self) -> None:
        """Save the modified Spine animation file"""
        output_spine_file = os.path.join(
            self.output_dir,
            os.path.basename(self.spine_file)
        )
        with open(output_spine_file, 'w', encoding='utf-8') as f:
            json.dump(self.spine_data, f, indent=2)
            
    def process(self) -> None:
        """Main processing function"""
        self.load_spine_file()
        self.load_atlas_file()
        self.process_animation()
        self.save_modified_spine_file()

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
    exit(main()) 