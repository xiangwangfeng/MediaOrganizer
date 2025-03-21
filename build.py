import os
import shutil
from pathlib import Path

# 清理旧的构建文件
dist_dir = Path('dist')
build_dir = Path('build')

if dist_dir.exists():
    shutil.rmtree(dist_dir)
if build_dir.exists():
    shutil.rmtree(build_dir)

# 使用PyInstaller打包应用
os.system('pyinstaller --name MediaOrganizer --onefile --noconsole --clean main.py')

# 检查构建结果
exe_path = dist_dir / 'MediaOrganizer.exe'
if exe_path.exists():
    print(f'构建成功！可执行文件位置：{exe_path}')
else:
    print('构建失败，请检查错误信息')