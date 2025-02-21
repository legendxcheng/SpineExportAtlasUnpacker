#!/usr/bin/env python3
import os
import argparse
from spine_unpacker import SpineAtlasUnpacker

def process_folder(input_dir: str, output_base_dir: str) -> None:
    """
    Process all .json files in the input directory
    
    Args:
        input_dir (str): Input directory containing .json files
        output_base_dir (str): Base directory for output
    """
    # 确保输出基础目录存在
    if not os.path.exists(output_base_dir):
        os.makedirs(output_base_dir)
    
    # 遍历输入目录中的所有文件
    for filename in os.listdir(input_dir):
        if filename.endswith('.json'):
            # 构建完整的输入文件路径
            input_file = os.path.join(input_dir, filename)
            
            # 为每个输入文件创建对应的输出目录
            output_dir = os.path.join(output_base_dir, os.path.splitext(filename)[0])
            
            print(f"\nProcessing: {filename}")
            print(f"Output directory: {output_dir}")
            
            try:
                # 创建SpineAtlasUnpacker实例并处理文件
                unpacker = SpineAtlasUnpacker(input_file, output_dir)
                unpacker.process()
                print(f"Successfully processed {filename}")
            except Exception as e:
                print(f"Error processing {filename}: {str(e)}")

def main():
    parser = argparse.ArgumentParser(
        description='Batch process multiple Spine animation files in a directory'
    )
    parser.add_argument(
        'input_dir',
        nargs='?',
        default='./propArrive',
        help='Directory containing Spine animation files (default: ./input)'
    )
    parser.add_argument(
        'output_dir',
        nargs='?',
        default='./output',
        help='Base directory for output files (default: ./output)'
    )
    
    args = parser.parse_args()
    
    try:
        # 确保输入目录存在
        if not os.path.exists(args.input_dir):
            raise FileNotFoundError(f"Input directory not found: {args.input_dir}")
        
        process_folder(args.input_dir, args.output_dir)
        print("\nBatch processing completed successfully!")
        print(f"Input directory: {args.input_dir}")
        print(f"Output directory: {args.output_dir}")
    except Exception as e:
        print(f"Error: {str(e)}")
        return 1
    
    return 0

if __name__ == '__main__':
    exit(main())
