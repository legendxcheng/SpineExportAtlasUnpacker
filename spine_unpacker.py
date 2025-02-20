#!/usr/bin/env python3
import os
import json
import argparse
from PIL import Image
from typing import Dict, List, Tuple
import shutil
from atlas_parser import AtlasParser
from atlas_splitter import AtlasSplitter

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
            # Process each skin in the Spine data
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
                
                for skin_name, skin_data in skins_to_process:
                    print(f"Processing skin: {skin_name}")
                    skin_dir = os.path.join(self.output_dir, skin_name)
                    os.makedirs(skin_dir, exist_ok=True)
                    
                    # Get all attachments for this skin
                    if isinstance(skin_data, dict):
                        attachments = list(skin_data.values())
                    else:
                        print(f"Warning: Unexpected skin data format for skin {skin_name}")
                        print(f"Skin data: {skin_data}")
                        continue

                    # Extract all required regions from the atlas
                    regions_to_extract = []
                    for attachment in attachments:
                        for attachment_name in attachment:
                            if isinstance(attachment[attachment_name], dict):
                                if not attachment_name in regions_to_extract:
                                    regions_to_extract.append(attachment_name)
                    
                    if not regions_to_extract:
                        print(f"Warning: No valid regions found in skin {skin_name}")
                        continue

                    # Create a new atlas for this skin
                    try:
                        # Generate new atlas image and data
                        new_atlas_name = f"{skin_name}_atlas"
                        new_atlas_path = os.path.join(skin_dir, f"{new_atlas_name}.png")
                        new_atlas_data_path = os.path.join(skin_dir, f"{new_atlas_name}.atlas")
                        
                        # Extract and combine regions into new atlas
                        combined_image, region_positions = splitter.create_combined_atlas(regions_to_extract)
                        combined_image.save(new_atlas_path)
                        
                        # Create and save new atlas data file
                        splitter.save_combined_atlas_data(
                            new_atlas_data_path,
                            new_atlas_name + ".png",
                            region_positions
                        )
                        
                        # Update references in spine data
                        # for attachment in attachments:
                        #     if isinstance(attachment, dict) and 'name' in attachment:
                        #         attachment['atlas'] = f"{new_atlas_name}.atlas"
                                
                        print(f"Created new atlas for skin {skin_name}")
                        
                    except Exception as e:
                        print(f"Error processing skin {skin_name}: {str(e)}")
                        continue
                        
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
        default='./propArrive/bubble_hxc.json',  # Default spine file path
        help='Path to the Spine animation file (default: ./propArrive/bubble_hxc.json)'
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