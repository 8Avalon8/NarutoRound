"""
辅助函数模块：提供游戏中需要使用的通用工具函数
"""
import pygame
import os
import math
import random
import sys
from naruto_game.config import SCREEN_WIDTH, SCREEN_HEIGHT

# 全局字体缓存
_font_cache = {}

def get_font(size, bold=False):
    """获取支持中文的字体"""
    # 使用缓存避免重复加载字体
    key = (size, bold)
    if key in _font_cache:
        return _font_cache[key]
    
    # 默认系统字体 - 通常能显示中文
    default_font = pygame.font.SysFont(None, size, bold=bold)
    
    # 尝试按顺序加载这些字体，找到第一个可用的
    font_names = []
    
    # Windows中文字体
    if sys.platform.startswith('win'):
        font_names.extend([
            "SimHei", "Microsoft YaHei", "SimSun", "NSimSun", "FangSong", "KaiTi",
            "Arial Unicode MS", "MingLiU"
        ])
    # macOS中文字体
    elif sys.platform.startswith('darwin'):
        font_names.extend([
            "STHeiti", "Hiragino Sans GB", "Apple SD Gothic Neo", "PingFang SC",
            "STSong", "STFangsong"
        ])
    # Linux中文字体
    else:
        font_names.extend([
            "WenQuanYi Zen Hei", "WenQuanYi Micro Hei", "Droid Sans Fallback",
            "Noto Sans CJK SC", "Source Han Sans CN", "Source Han Sans SC"
        ])
    
    # 测试字符 - 包含一些常用汉字
    test_chars = "中文测试火影忍者"
    
    # 尝试找到一个支持中文的字体
    font = None
    for font_name in font_names:
        try:
            font = pygame.font.SysFont(font_name, size, bold=bold)
            # 尝试渲染测试字符
            test_surface = font.render(test_chars, True, (0, 0, 0))
            width, height = test_surface.get_size()
            
            # 检查渲染结果是否有合理的宽度 (方块字符通常很窄)
            if width > len(test_chars) * size * 0.3:  # 基本判断标准
                _font_cache[key] = font
                return font
        except:
            continue
    
    # 如果找不到合适的字体，尝试直接使用默认字体
    _font_cache[key] = default_font
    return default_font

def draw_text(surface, text, font, color, x, y, align="center"):
    """在指定位置绘制文本"""
    text_surface = font.render(text, True, color)
    text_rect = text_surface.get_rect()
    
    if align == "center":
        text_rect.center = (x, y)
    elif align == "topleft":
        text_rect.topleft = (x, y)
    elif align == "topright":
        text_rect.topright = (x, y)
    elif align == "bottomleft":
        text_rect.bottomleft = (x, y)
    elif align == "bottomright":
        text_rect.bottomright = (x, y)
    
    surface.blit(text_surface, text_rect)
    return text_rect

def load_image(filename, scale=1.0, alpha=False):
    """加载图像资源并根据需要调整大小"""
    try:
        path = os.path.join('assets', 'images', filename)
        if alpha:
            image = pygame.image.load(path).convert_alpha()
        else:
            image = pygame.image.load(path).convert()
            
        if scale != 1.0:
            new_width = int(image.get_width() * scale)
            new_height = int(image.get_height() * scale)
            image = pygame.transform.scale(image, (new_width, new_height))
        return image
    except pygame.error:
        print(f"无法加载图像: {filename}")
        # 创建一个替代的矩形图像
        placeholder = pygame.Surface((50, 50))
        placeholder.fill((255, 0, 255))  # 紫色占位符
        return placeholder

def distance(pos1, pos2):
    """计算两点之间的距离"""
    return math.sqrt((pos2[0] - pos1[0])**2 + (pos2[1] - pos1[1])**2)

def get_random_position(min_distance=50):
    """获取一个随机位置，确保与屏幕边缘保持最小距离"""
    x = random.randint(min_distance, SCREEN_WIDTH - min_distance)
    y = random.randint(min_distance, SCREEN_HEIGHT - min_distance)
    return (x, y)

def lerp(a, b, t):
    """线性插值函数，用于平滑动画"""
    return a + (b - a) * t

def create_simple_character_image(name, color=(255, 0, 0)):
    """创建简单的角色图像（圆形+名字首字）"""
    size = (100, 100)
    image = pygame.Surface(size, pygame.SRCALPHA)
    
    # 绘制圆形
    center = (size[0] // 2, size[1] // 2)
    radius = min(center)
    pygame.draw.circle(image, color, center, radius)
    
    # 在圆内部绘制名字首字
    first_char = name[0] if name else "?"
    font = get_font(radius, bold=True)
    text_surf = font.render(first_char, True, (255, 255, 255))
    text_rect = text_surf.get_rect(center=center)
    image.blit(text_surf, text_rect)
    
    return image

def create_status_effect_icon(effect_name, size=(20, 20)):
    """创建状态效果图标"""
    colors = {
        '小浮空': (0, 191, 255),  # 浅蓝色
        '大浮空': (30, 144, 255),  # 道奇蓝
        '倒地': (139, 69, 19),     # 棕色
        '击退': (255, 140, 0),     # 深橙色
        '点燃': (255, 0, 0),       # 红色
        '中毒': (128, 0, 128),     # 紫色
        '封穴': (105, 105, 105),   # 暗灰色
        '定身': (0, 0, 128),       # 深蓝色
        '混乱': (255, 20, 147),    # 深粉色
        '目盲': (0, 0, 0),         # 黑色
        '麻痹': (255, 255, 0),     # 黄色
        '睡眠': (70, 130, 180)     # 钢蓝色
    }
    
    # 默认颜色为灰色
    color = colors.get(effect_name, (128, 128, 128))
    
    # 创建一个圆形图标
    icon = pygame.Surface(size, pygame.SRCALPHA)
    pygame.draw.circle(
        icon, 
        color, 
        (size[0] // 2, size[1] // 2), 
        min(size) // 2
    )
    
    # 在图标中添加首字符
    font = pygame.font.SysFont(None, size[0])
    text = effect_name[0]  # 取第一个字
    text_surface = font.render(text, True, (255, 255, 255))
    text_rect = text_surface.get_rect(center=(size[0] // 2, size[1] // 2))
    icon.blit(text_surface, text_rect)
    
    return icon 