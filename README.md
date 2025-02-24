1. 输入文件夹路径，遍历文件夹中的所有.json文件：
    a. 如果当前工作目录下存在curSpineProj目录，则清空它内部所有文件。
    b. 复制./emptySpineProj目录下的proj.spine到curSpineProj目录下。
    c. 对于这个.json文件，找到同名的.atlas文件，打开它，读取第一行，找到.png文件的名称，记录其绝对路径。
    e. 执行命令行：（指定版本 3.8）
        i. 进行纹理解包： 上一步中获得的绝对路径 ，让spine （指定版本4.2）进行解包，解包后放到curSpineProj目录的textures目录下。
        ii. 导入spine数据
        iii. 导入spine图片
        iv. 导出到output目录下

2. spine的指令为：
    切换版本：
        切换到3.8版本：
            spine -u 3.8
        切换到4.2版本：
            spine -u 4.2

    导入spine的json数据：
        Spine -i <.json文件路径> -o <上面提到的 .curSpineProj/proj.spine> --import
    
    spine的纹理解包：
        Spine -i <上面描述的.json所在的文件夹路径> -o <./curSpineProj/textures> --unpack <上面描述的.atlas文件第一行的png文件的绝对路径>
        纹理图集解包:
        -i, --input 图集图片文件夹的路径。
        -o, --output 写入解包图片文件的路径。
        -c, --unpack 纹理图集文件的路径。

    spine的导出：
        Spine -i <./curSpineProj/proj.spine> -m -o <./output> -e json[+pack]
        导出JSON、二进制、图片或视频:
        -i, --input   文件夹、项目或数据文件的路径。覆盖导出JSON。
        -m, --clean   在导出之前执行动画清理。
        -o, --output  写入导出文件的路径。覆盖导出JSON。
        -e, --export  导出设置JSON文件的路径。

3. 使用方法：
    1. 分析一个游戏工程中的Spine动画目录（先把这里的output目录清空）
        python spine_exporter.py --input_dir "E:\IAA定制\playablead_bubble_shot\assets\resources\game\spine\win_fail"
    2. 将Output目录下的所有文件复制到上一步分析的Spine动画目录下
    3. 打开Cocos，让Cosos更新Meta文件
    4. 运行脚本更新meta文件
        python correct_spine_json_ref.py "e:\IAA定制\playablead_bubble_shot\assets\resources\game\spine\win_fail"
    5. 清理掉原来的工程文件夹中的合图



