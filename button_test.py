#!/usr/bin/env python
"""
按钮测试脚本 - 用于测试UI元素的显示和行为
"""
import pygame
import sys
import os

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from naruto_game.config import SCREEN_WIDTH, SCREEN_HEIGHT, WHITE, RED, GREEN, BLUE
from naruto_game.utils.ui import Button
from naruto_game.utils.helpers import get_font

def main():
    """主函数"""
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("按钮测试")
    clock = pygame.time.Clock()
    font = get_font(24)
    
    # 打印实际屏幕尺寸
    print(f"屏幕尺寸: {SCREEN_WIDTH}x{SCREEN_HEIGHT}")
    
    # 创建多个测试按钮
    buttons = [
        Button(
            x=SCREEN_WIDTH * 0.25 - 150,
            y=SCREEN_HEIGHT * 0.88,
            width=300,
            height=60,
            text="普通攻击",
            color=(50, 100, 255)
        ),
        Button(
            x=SCREEN_WIDTH * 0.75 - 150,
            y=SCREEN_HEIGHT * 0.88,
            width=300,
            height=60,
            text="奥义技能",
            color=(255, 50, 50)
        ),
        Button(
            x=SCREEN_WIDTH * 0.5 - 150,
            y=SCREEN_HEIGHT * 0.7,
            width=300,
            height=60,
            text="使用技能",
            color=(50, 200, 50)
        )
    ]
    
    # 主循环
    running = True
    while running:
        mouse_pos = pygame.mouse.get_pos()
        
        # 处理事件
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # 检查按钮点击
                for button in buttons:
                    if button.rect.collidepoint(event.pos):
                        print(f"点击了按钮: {button.text}")
        
        # 更新按钮状态
        for button in buttons:
            button.update(mouse_pos=mouse_pos)
        
        # 绘制界面
        screen.fill((30, 30, 50))  # 深蓝色背景
        
        # 绘制辅助线
        pygame.draw.line(screen, RED, (SCREEN_WIDTH//2, 0), (SCREEN_WIDTH//2, SCREEN_HEIGHT), 1)  # 垂直中线
        pygame.draw.line(screen, GREEN, (0, SCREEN_HEIGHT//2), (SCREEN_WIDTH, SCREEN_HEIGHT//2), 1)  # 水平中线
        
        # 绘制屏幕尺寸信息
        text_surface = font.render(f"屏幕尺寸: {SCREEN_WIDTH}x{SCREEN_HEIGHT}", True, WHITE)
        screen.blit(text_surface, (10, 10))
        
        # 绘制鼠标位置
        mouse_text = font.render(f"鼠标位置: {mouse_pos}", True, WHITE)
        screen.blit(mouse_text, (10, 40))
        
        # 绘制按钮
        for button in buttons:
            button.draw(screen)
        
        # 更新屏幕
        pygame.display.flip()
        clock.tick(60)
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main() 