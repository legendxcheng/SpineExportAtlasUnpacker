import os
import shutil
import subprocess
import json
import glob
import argparse
import time
import psutil
import sys

CRACK_SPINE = r"D:\Program Files (x86)\Spine\spine.exe"

class SpineExporter:
    def __init__(self):
        self.cur_spine_proj_dir = "curSpineProj"
        self.empty_spine_proj_dir = "emptySpineProj"
        self.output_dir = "output"
        self.textures_dir = os.path.join(self.cur_spine_proj_dir, "images")

    def clean_cur_spine_proj(self):
        """清空curSpineProj目录并复制空项目文件"""
        if os.path.exists(self.cur_spine_proj_dir):
            shutil.rmtree(self.cur_spine_proj_dir)
        os.makedirs(self.cur_spine_proj_dir)
        
        # # 复制空项目文件
        # empty_proj_file = os.path.join(self.empty_spine_proj_dir, "proj.spine")
        # if os.path.exists(empty_proj_file):
        #     shutil.copy2(empty_proj_file, self.cur_spine_proj_dir)
        # else:
        #     raise FileNotFoundError(f"Empty project file not found: {empty_proj_file}")

    def get_png_path_from_atlas(self, atlas_file):
        """从atlas文件中读取第一行获取png文件路径"""
        try:
            with open(atlas_file, 'r', encoding='utf-8') as f:
                while True:
                    first_line = f.readline().strip()
                    if first_line.endswith('.png'):
                        break
                return os.path.abspath(os.path.join(os.path.dirname(atlas_file), first_line))
        except Exception as e:
            raise Exception(f"Error reading atlas file {atlas_file}: {str(e)}")

    def kill_spine_process(self):
        """终止所有Spine进程"""
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if 'Spine' in proc.info['name']:
                    psutil.Process(proc.info['pid']).terminate()
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass


    def run_command(self, cmd, description):
        """运行命令并显示输出"""
        print(f"\n执行命令: {' '.join(cmd)}")
        try:
            process = subprocess.run(
                cmd,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            if process.stdout:
                print("输出:")
                print(process.stdout)
            if process.stderr:
                print("错误:")
                print(process.stderr)
            return process
        except subprocess.CalledProcessError as e:
            print(f"{description}失败:")
            if e.stdout:
                print("输出:")
                print(e.stdout)
            if e.stderr:
                print("错误:")
                print(e.stderr)
            raise Exception(f"{description}: {str(e)}")

    def unpack_texture(self, json_dir, atlas_path):
        """解包纹理"""
        try:
            os.makedirs(self.textures_dir, exist_ok=True)
            self.run_command([
                'spine',
                '-u', '4.2',
                '-i', json_dir,
                '-o', self.textures_dir,
                '--unpack', atlas_path
            ], "解包纹理")
        except Exception as e:
            raise Exception(f"Failed to unpack texture: {str(e)}")

    def import_spine_data(self, json_file):
        """导入Spine数据"""
        try:
            proj_spine_path = os.path.join(self.cur_spine_proj_dir, "proj.spine")
            self.run_command([
                'spine',
                '-u', '3.8',
                '-i', json_file,
                '-o', proj_spine_path,
                '--import'
            ], "导入Spine数据")
        except Exception as e:
            raise Exception(f"Failed to import Spine data: {str(e)}")

    def export_spine_project(self):
        """导出Spine项目"""
        try:
            os.makedirs(self.output_dir, exist_ok=True)
            self.run_command([
                'spine',
                '-u', '3.8',
                '-i', os.path.join(self.cur_spine_proj_dir, "proj.spine"),
                '-m',
                '-o', self.output_dir,
                '-e', './saveParam.export.json'
            ], "导出Spine项目")
        except Exception as e:
            raise Exception(f"Failed to export Spine project: {str(e)}")

    def process_json_file(self, json_file):
        """处理单个JSON文件"""
        print(f"Processing {json_file}...")
        
        # 清理并准备工作目录
        self.clean_cur_spine_proj()
        
        # 获取相关文件路径
        json_dir = os.path.dirname(json_file)
        atlas_file = os.path.splitext(json_file)[0] + '.atlas'
        
        if not os.path.exists(atlas_file):
            raise FileNotFoundError(f"Atlas file not found: {atlas_file}")
        
        # 执行处理步骤
        self.unpack_texture(json_dir, atlas_file)
        self.import_spine_data(json_file)
        self.export_spine_project()
        
        print(f"Finished processing {json_file}")

    def process_directory(self, input_dir):
        """处理目录中的所有JSON文件"""
        json_files = glob.glob(os.path.join(input_dir, "**/*.json"), recursive=True)
        if not json_files:
            print(f"No JSON files found in {input_dir}")
            return
        
        for json_file in json_files:
            try:
                self.process_json_file(json_file)
            except Exception as e:
                print(f"Error processing {json_file}: {str(e)}")

def main():
    parser = argparse.ArgumentParser(description='Spine动画文件导出工具')
    parser.add_argument('--input_dir', '-i', 
                      default='./propArrive',  # 设置默认值为propArrive目录
                      help='要处理的文件夹路径 (默认: ./propArrive)')
    
    args = parser.parse_args()
    input_dir = args.input_dir

    try:
        if not os.path.exists(input_dir):
            print(f"错误：目录 {input_dir} 不存在")
            return
        
        exporter = SpineExporter()
        exporter.process_directory(input_dir)
        print("处理完成！")
        
    except Exception as e:
        print(f"发生错误: {str(e)}")

if __name__ == "__main__":
    main() 