# MediaOrganizer
根据拍摄时间自动分类和整理你的媒体文件，让你的图库更加清晰有序

## 缘起
[老婆也能懂：两句话让 AI 帮你生成一个照片整理工具](https://mp.weixin.qq.com/s/ddQjaYXB5vlJ4sHqRPcoyw)
代码全由 Trae 自动生成，毫无人工干预（包括此 README...）

## 主要功能
- 自动读取照片和视频的拍摄时间，按日期分类整理
- 支持多种图片格式：PNG、JPG、JPEG、GIF、BMP、HEIC、WEBP
- 支持多种视频格式：MP4、MOV、AVI、MKV、WMV、FLV
- 自动创建日期文件夹（格式：YYYY.MM.DD）
- 智能处理重复文件，通过MD5校验避免重复复制
- 保留原始文件的元数据信息
- 友好的图形界面，显示实时处理进度
- 支持中断处理过程
- 自动记录不支持的文件类型到日志文件

## 安装步骤
1. 确保已安装Python 3.x
2. 克隆或下载本仓库
3. 安装依赖库：
```bash
pip install pillow hachoir tkinter hashlib
```

## 使用方法
1. 运行程序：
```bash
python main.py
```
2. 在界面中选择源文件夹（包含待整理的媒体文件）
3. 选择目标文件夹（整理后的文件将存放在这里）
4. 点击"开始整理"按钮
5. 等待处理完成，可以随时点击"停止整理"按钮中断处理

## 打包为独立EXE
1. 确保已安装所有依赖库
2. 安装PyInstaller：
```bash
pip install pyinstaller
```
3. 运行打包脚本：
```bash
python build.py
```
4. 打包完成后，可在dist目录下找到MediaOrganizer.exe文件
5. 双击exe文件即可运行程序，无需安装Python环境

## 注意事项
- 源文件夹和目标文件夹不能互相包含
- 程序会自动跳过重复的文件（通过MD5校验）
- 对于无法读取拍摄时间的文件，将使用文件修改时间作为分类依据
- 如果文件名重复，程序会自动在文件名后添加数字后缀
- 不支持的文件类型会被记录到日志文件中（保存在目标文件夹）
- 支持中断处理过程，可随时点击"停止整理"

## 程序截图
![程序主界面](images/screenshot.png)
