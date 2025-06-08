"""
UI组件模块：包含游戏中使用的各种UI元素
"""
import pygame
from naruto_game.config import BLACK, WHITE, RED, GREEN, GREY, YELLOW, BUTTON_WIDTH, BUTTON_HEIGHT
from naruto_game.utils.helpers import get_font

class Button:
    """按钮控件：可响应点击事件"""
    def __init__(self, x, y, width=BUTTON_WIDTH, height=BUTTON_HEIGHT, text="按钮", color=(100, 100, 200), text_color=WHITE, action=None):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.original_color = color
        self.hover_color = tuple(min(c + 50, 255) for c in color)  # 悬停时颜色变亮
        self.text_color = text_color
        self.action = action
        self.font = get_font(24)
        self.hovered = False
        self.available = True
        print(f"创建按钮: '{text}' 位置:({x}, {y}) 大小:({width}x{height})")
    
    def update(self, chakra=None, mouse_pos=None):
        """更新按钮状态"""
        if mouse_pos:
            self.hovered = self.rect.collidepoint(mouse_pos) and self.available
        else:
            self.hovered = False
    
    def draw(self, screen):
        """绘制按钮"""
        # 选择颜色 (悬停、正常或不可用)
        current_color = self.hover_color if self.hovered else self.original_color
        if not self.available:
            current_color = tuple(c // 2 for c in self.original_color)  # 变暗表示不可用
        
        # 绘制按钮主体 - 使用更亮的颜色
        pygame.draw.rect(screen, current_color, self.rect, border_radius=8)
        
        # 绘制边框 - 使用更醒目的边框
        border_width = 4 if self.hovered else 3
        border_color = (255, 255, 0) if self.hovered else (255, 255, 255)
        pygame.draw.rect(screen, border_color, self.rect, width=border_width, border_radius=8)
        
        # 再添加一个外层边框，更容易看见
        outer_rect = self.rect.inflate(10, 10)
        pygame.draw.rect(screen, (255, 0, 0), outer_rect, width=2, border_radius=10)
        
        # 绘制文本 - 使用更大的字体
        self.font = get_font(28)  # 增大字体
        text_surface = self.font.render(self.text, True, self.text_color)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)
        
        # 如果按钮是技能按钮，添加点击提示
        if hasattr(self, 'skill'):
            hint_font = get_font(20)  # 增大提示字体
            hint_text = "点击选择"
            hint_surface = hint_font.render(hint_text, True, (255, 255, 0))
            hint_rect = hint_surface.get_rect(center=(self.rect.centerx, self.rect.bottom + 20))
            screen.blit(hint_surface, hint_rect)

class ProgressBar:
    """进度条：显示生命值、查克拉等数值"""
    def __init__(self, x, y, width, height, max_value, current_value, bg_color=(50, 50, 50), fill_color=GREEN, border_color=WHITE):
        self.rect = pygame.Rect(x, y, width, height)
        self.max_value = max_value
        self.current_value = current_value
        self.bg_color = bg_color
        self.fill_color = fill_color
        self.border_color = border_color
    
    def update(self, new_value):
        """更新当前值"""
        self.current_value = min(max(0, new_value), self.max_value)
    
    def draw(self, surface):
        """绘制进度条"""
        # 绘制背景
        pygame.draw.rect(surface, self.bg_color, self.rect)
        
        # 绘制填充部分
        if self.current_value > 0:
            fill_width = int(self.rect.width * (self.current_value / self.max_value))
            fill_rect = pygame.Rect(self.rect.x, self.rect.y, fill_width, self.rect.height)
            pygame.draw.rect(surface, self.fill_color, fill_rect)
        
        # 绘制边框
        pygame.draw.rect(surface, self.border_color, self.rect, 1)

class CharacterCard:
    """角色卡片：显示角色基本信息"""
    def __init__(self, x, y, width, height, character):
        self.rect = pygame.Rect(x, y, width, height)
        self.character = character
        self.hp_bar = ProgressBar(
            x + 10, 
            y + height - 25, 
            width - 20, 
            10, 
            character.max_hp,
            character.current_hp
        )
        self.font_name = get_font(20)
        self.font_stats = get_font(16)
        self.selected = False
        self.is_hovered = False
    
    def update(self):
        """更新角色卡片状态"""
        self.hp_bar.current_value = self.character.current_hp
    
    def draw(self, surface):
        """绘制角色卡片"""
        # 绘制背景
        bg_color = (60, 60, 60)
        if self.selected:
            # 如果被选中，使用高亮颜色
            bg_color = (100, 100, 160)
        elif self.is_hovered:
            # 如果鼠标悬停，使用不同颜色
            bg_color = (80, 80, 100)
            
        pygame.draw.rect(surface, bg_color, self.rect, border_radius=5)
        
        # 绘制边框
        border_color = WHITE
        if self.selected:
            border_color = YELLOW
        pygame.draw.rect(surface, border_color, self.rect, width=2, border_radius=5)
        
        # 绘制角色名称
        name_surface = self.font_name.render(self.character.name, True, WHITE)
        name_rect = name_surface.get_rect(center=(self.rect.centerx, self.rect.y + 20))
        surface.blit(name_surface, name_rect)
        
        # 绘制角色图像
        char_image_size = 130
        char_image = pygame.transform.scale(self.character.image, (char_image_size, char_image_size))
        char_rect = char_image.get_rect(center=(self.rect.centerx, self.rect.centery - 20))
        surface.blit(char_image, char_rect)
        
        # 绘制生命值条
        self.hp_bar.draw(surface)
        hp_text = f"HP: {self.character.current_hp}/{self.character.max_hp}"
        hp_surface = self.font_stats.render(hp_text, True, WHITE)
        hp_rect = hp_surface.get_rect(center=(self.rect.centerx, self.rect.bottom - 15))
        surface.blit(hp_surface, hp_rect)
    
    def handle_event(self, event):
        """处理点击事件"""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos) and self.character.is_alive:
                return self.character
        return None
    
    def update_hover(self, mouse_pos):
        """更新鼠标悬停状态"""
        self.is_hovered = self.rect.collidepoint(mouse_pos) and self.character.is_alive

class MessageBox:
    """消息框：显示战斗信息"""
    def __init__(self, x, y, width, height, font_size=18):
        self.rect = pygame.Rect(x, y, width, height)
        self.font = get_font(font_size)
        self.messages = []
        self.max_messages = 8  # 最多显示8条消息
        self.bg_color = (0, 0, 0, 128)  # 半透明黑色
    
    def add_message(self, message):
        """添加消息"""
        self.messages.append(message)
        # 保持消息数量在最大限制内
        if len(self.messages) > self.max_messages:
            self.messages = self.messages[-self.max_messages:]
    
    def clear(self):
        """清除所有消息"""
        self.messages = []
    
    def draw(self, surface):
        """绘制消息框"""
        # 绘制背景
        bg_surface = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        bg_surface.fill(self.bg_color)
        surface.blit(bg_surface, self.rect)
        
        # 绘制边框
        pygame.draw.rect(surface, WHITE, self.rect, 1)
        
        # 绘制消息
        line_height = 22
        margin = 10
        for i, message in enumerate(self.messages):
            y = self.rect.y + margin + i * line_height
            if y + line_height > self.rect.y + self.rect.height - margin:
                break
                
            text_surface = self.font.render(message, True, WHITE)
            surface.blit(text_surface, (self.rect.x + margin, y))

class SkillButton(Button):
    """技能按钮：显示技能信息和状态"""
    def __init__(self, x, y, width, height, skill, **kwargs):
        super().__init__(x, y, width, height, text=skill.name, **kwargs)
        self.skill = skill
        self.font_description = get_font(16)
        self.available = True
        
    def update(self, chakra=None, mouse_pos=None):
        """更新技能可用状态"""
        # 检查查克拉是否足够
        if chakra is not None and hasattr(self.skill, "chakra_cost"):
            self.available = chakra >= self.skill.chakra_cost and (not hasattr(self.skill, "current_cooldown") or self.skill.current_cooldown == 0)
            self.color = GREY if self.available else (100, 0, 0)
            self.hover_color = tuple(max(0, min(255, c + 30)) for c in self.color)
        
        # 更新悬停状态
        if mouse_pos is not None:
            self.is_hovered = self.rect.collidepoint(mouse_pos)
        
    def draw(self, surface):
        """绘制技能按钮"""
        super().draw(surface)  # 绘制基本按钮
        
        # 如果鼠标悬停，显示技能描述
        if self.is_hovered:
            if hasattr(self.skill, "description"):
                # 创建描述面板
                desc_surface = self.font_description.render(self.skill.description, True, WHITE)
                desc_rect = desc_surface.get_rect(midtop=(self.rect.centerx, self.rect.top - 30))
                
                # 添加背景
                bg_rect = desc_rect.copy()
                bg_rect.inflate_ip(20, 10)
                pygame.draw.rect(surface, (0, 0, 0, 180), bg_rect, border_radius=5)
                
                # 绘制描述文本
                surface.blit(desc_surface, desc_rect)
            
            if hasattr(self.skill, "chakra_cost") and self.skill.chakra_cost > 0:
                # 显示查克拉消耗
                chakra_text = f"查克拉: {self.skill.chakra_cost}"
                chakra_surface = self.font_description.render(chakra_text, True, (0, 100, 255))
                chakra_rect = chakra_surface.get_rect(midbottom=(self.rect.centerx, self.rect.top - 35))
                surface.blit(chakra_surface, chakra_rect) 