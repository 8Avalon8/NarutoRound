#!/usr/bin/env python
"""
火影忍者OL战斗原型 - 启动文件
"""
import os
import sys

# 添加当前目录到Python路径，以便导入naruto_game包
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from naruto_game.scenes import Game

if __name__ == "__main__":
    print("启动火影忍者OL战斗原型...")
    game = Game()
    game.run() 