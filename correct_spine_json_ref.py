import os
import json
import argparse

def get_png_uuid(png_meta_file):
    with open(png_meta_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        return data['uuid']

def update_json_meta(json_meta_file, png_uuid):
    with open(json_meta_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        data['textures'] = [png_uuid]
    
    with open(json_meta_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def process_json_files(folder_path):
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            if file.endswith('.json'):
                json_file = os.path.join(root, file)
                json_meta_file = json_file + '.meta'
                png_file = os.path.splitext(json_file)[0] + '.png'
                png_meta_file = png_file + '.meta'

                if os.path.exists(json_meta_file) and os.path.exists(png_meta_file):
                    png_uuid = get_png_uuid(png_meta_file)
                    update_json_meta(json_meta_file, png_uuid)
                    print(f"Updated {json_meta_file} with UUID from {png_meta_file}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Update JSON meta files with PNG UUIDs')
    parser.add_argument('folder_path', nargs='?', default=r"e:\IAA定制\playablead_bubble_shot\assets\resources\game\spine\ballDeal",
                       help='Path to the folder containing JSON files')
    args = parser.parse_args()
    process_json_files(args.folder_path)
