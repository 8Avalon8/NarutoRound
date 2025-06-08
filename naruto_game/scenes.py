"""
游戏场景模块：管理不同游戏场景和状态
"""
import pygame
import sys
import random
from naruto_game.config import *
from naruto_game.utils.ui import Button, CharacterCard, MessageBox, SkillButton
from naruto_game.utils.helpers import get_font, draw_text
from naruto_game.models.character import create_team7, create_team10
from naruto_game.models.battle import BattleSystem

class Scene:
    """场景基类"""
    def __init__(self, game):
        self.game = game
        self.next_scene = None
    
    def handle_event(self, event):
        """处理事件"""
        pass
    
    def update(self):
        """更新场景状态"""
        pass
    
    def render(self, screen):
        """渲染场景"""
        pass
        
    def switch_to_scene(self, scene_class, *args, **kwargs):
        """切换到新场景"""
        self.next_scene = scene_class(self.game, *args, **kwargs)


class TitleScene(Scene):
    """标题场景"""
    def __init__(self, game):
        super().__init__(game)
        
        # 设置背景色
        self.bg_color = (50, 50, 80)
        
        # 标题文本
        self.title_font = get_font(72, bold=True)
        self.subtitle_font = get_font(36)
        
        # 开始按钮
        button_x = SCREEN_WIDTH // 2 - BUTTON_WIDTH // 2
        button_y = SCREEN_HEIGHT * 0.6
        self.start_button = Button(
            x=button_x, 
            y=button_y,
            text="开始战斗",
            action=self._on_start_battle_click
        )
        
        # 退出按钮
        self.exit_button = Button(
            x=button_x, 
            y=button_y + BUTTON_HEIGHT + 20,
            text="退出游戏",
            action=self._on_exit_click
        )
    
    def render(self, screen):
        """渲染标题场景"""
        # 填充背景
        screen.fill(self.bg_color)
        
        # 绘制主标题
        title_text = "火影忍者OL"
        title_surface = self.title_font.render(title_text, True, (255, 150, 0))
        title_rect = title_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 4))
        screen.blit(title_surface, title_rect)
        
        # 绘制副标题
        subtitle_text = "战斗原型"
        subtitle_surface = self.subtitle_font.render(subtitle_text, True, (200, 200, 200))
        subtitle_rect = subtitle_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 4 + 80))
        screen.blit(subtitle_surface, subtitle_rect)
        
        # 绘制按钮
        self.start_button.draw(screen)
        self.exit_button.draw(screen)
    
    def handle_event(self, event):
        """处理标题场景的事件"""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = pygame.mouse.get_pos()
            
            # 检查开始按钮
            if self.start_button.rect.collidepoint(mouse_pos):
                self._on_start_battle_click()
            
            # 检查退出按钮
            elif self.exit_button.rect.collidepoint(mouse_pos):
                self._on_exit_click()
    
    def update(self):
        """更新标题场景状态"""
        # 更新按钮悬停状态
        mouse_pos = pygame.mouse.get_pos()
        self.start_button.update(mouse_pos)
        self.exit_button.update(mouse_pos)
    
    def _on_start_battle_click(self):
        """点击开始战斗按钮的处理"""
        self.switch_to_scene(BattleScene)
    
    def _on_exit_click(self):
        """点击退出按钮的处理"""
        pygame.quit()
        sys.exit()


class BattleScene(Scene):
    """战斗场景"""
    def __init__(self, game):
        super().__init__(game)
        
        # 创建队伍和战斗系统
        self.player_team = create_team7()
        self.enemy_team = create_team10()
        self.battle_system = BattleSystem()
        self.battle_state = self.battle_system.create_battle(self.player_team, self.enemy_team)
        
        # 设置角色位置
        self._setup_battle_positions()
        
        # 创建UI元素
        self._create_ui_elements()
        
        # 当前选择的技能和目标
        self.selected_skill = None
        self.available_targets = []
        self.selected_target = None
        
        # 战斗状态
        self.is_battle_started = False
        self.is_player_turn = False
        self.is_waiting_for_action = False
        
        # 背景色
        self.bg_color = (30, 30, 50)
        
        # 添加引导效果相关变量
        self.highlight_timer = 0
        self.highlight_max = 30  # 闪烁周期
        
        # 开始战斗
        self.start_battle()
    
    def _setup_battle_positions(self):
        """设置战斗位置"""
        # 玩家队伍位置 - 在左侧排成一行
        player_x_start = SCREEN_WIDTH * 0.15  # 从屏幕左侧15%位置开始
        player_x_spacing = SCREEN_WIDTH * 0.1  # 角色间隔为屏幕宽度的10%
        player_y_base = SCREEN_HEIGHT * 0.6    # 在屏幕60%高度处
        
        # 敌人队伍位置 - 在右侧排成一行
        enemy_x_start = SCREEN_WIDTH * 0.65  # 从屏幕右侧65%位置开始
        enemy_x_spacing = SCREEN_WIDTH * 0.1  # 角色间隔为屏幕宽度的10%
        enemy_y_base = SCREEN_HEIGHT * 0.6    # 在屏幕60%高度处
        
        # 设置玩家角色位置
        player_positions = []
        for i in range(4):
            player_positions.append((
                player_x_start + i * player_x_spacing,
                player_y_base
            ))
        
        # 设置敌人角色位置
        enemy_positions = []
        for i in range(3):
            enemy_positions.append((
                enemy_x_start + i * enemy_x_spacing,
                enemy_y_base
            ))
        
        # 输出实际坐标值，便于调试
        print("玩家队伍位置:")
        for pos in player_positions:
            print(f"  ({pos[0]}, {pos[1]})")
        print("敌人队伍位置:")
        for pos in enemy_positions:
            print(f"  ({pos[0]}, {pos[1]})")
        
        # 设置玩家角色位置
        for i, character in enumerate(self.player_team.characters):
            if i < len(player_positions):
                character.battle_position = player_positions[i]
                character.target_position = player_positions[i]
        
        # 设置敌人角色位置
        for i, character in enumerate(self.enemy_team.characters):
            if i < len(enemy_positions):
                character.battle_position = enemy_positions[i]
                character.target_position = enemy_positions[i]
    
    def _create_ui_elements(self):
        """创建UI元素"""
        # 角色卡片 - 减小尺寸以避免重叠
        card_width = SCREEN_WIDTH * 0.12  # 从0.15减小到0.12
        card_height = SCREEN_HEIGHT * 0.2  # 从0.25减小到0.2
        card_spacing = card_width * 0.2  # 增加间距从0.1到0.2
        
        # 玩家角色卡片 - 底部左侧
        self.player_cards = []
        start_x = SCREEN_WIDTH * 0.02  # 屏幕左侧2%处开始
        start_y = SCREEN_HEIGHT - card_height - SCREEN_HEIGHT * 0.02  # 底部上方2%
        
        for i, character in enumerate(self.player_team.characters):
            card = CharacterCard(
                start_x + i * (card_width + card_spacing), 
                start_y, 
                card_width, 
                card_height, 
                character
            )
            self.player_cards.append(card)
        
        # 敌人角色卡片 - 底部右侧
        self.enemy_cards = []
        start_x = SCREEN_WIDTH - len(self.enemy_team.characters) * (card_width + card_spacing) + card_spacing - SCREEN_WIDTH * 0.02
        
        for i, character in enumerate(self.enemy_team.characters):
            card = CharacterCard(
                start_x + i * (card_width + card_spacing), 
                start_y, 
                card_width, 
                card_height, 
                character
            )
            self.enemy_cards.append(card)
        
        # 战斗日志 - 屏幕中央上方
        self.battle_log = MessageBox(
            SCREEN_WIDTH * 0.3,
            SCREEN_HEIGHT * 0.15,
            SCREEN_WIDTH * 0.4,
            SCREEN_HEIGHT * 0.2
        )
        self.battle_log.add_message("战斗开始！")
        
        # 技能按钮 - 会在更新时动态创建
        self.skill_buttons = []
        
        # 返回按钮（战斗结束时显示） - 屏幕中央偏下
        self.back_to_title_button = Button(
            x=SCREEN_WIDTH * 0.4,
            y=SCREEN_HEIGHT * 0.7,
            width=SCREEN_WIDTH * 0.2,
            height=SCREEN_HEIGHT * 0.08,
            text="返回标题界面"
        )
        
        print("界面元素创建完成:")
        print(f"  玩家卡片: {len(self.player_cards)}张，位于({start_x}, {start_y})")
        print(f"  敌人卡片: {len(self.enemy_cards)}张")
        print(f"  战斗日志: 位于({self.battle_log.rect.x}, {self.battle_log.rect.y})")
    
    def _update_skill_buttons(self):
        """更新技能按钮"""
        current_character = self.battle_state.current_character
        if not current_character:
            return
            
        # 清空当前的技能按钮列表
        self.skill_buttons = []
        
        # 如果角色没有技能属性，尝试处理
        if not hasattr(current_character, 'normal_attack') or not current_character.normal_attack:
            print(f"警告：角色{current_character.name}没有普通攻击技能")
            return
            
        if not hasattr(current_character, 'mystery_art') or not current_character.mystery_art:
            print(f"警告：角色{current_character.name}没有奥义技能")
            return
        
        # 计算按钮尺寸和位置 - 大按钮占据屏幕底部中央
        button_width = SCREEN_WIDTH * 0.25  # 屏幕宽度的25%
        button_height = SCREEN_HEIGHT * 0.08  # 屏幕高度的8%
        button_y = SCREEN_HEIGHT * 0.88  # 屏幕底部12%处
        
        # 普通攻击按钮 - 放在底部中央左侧
        normal_attack = Button(
            x=SCREEN_WIDTH * 0.25 - button_width/2,
            y=button_y,
            width=button_width,
            height=button_height,
            text=f"普攻: {current_character.normal_attack.name}",
            color=(50, 100, 255)
        )
        normal_attack.skill = current_character.normal_attack
        normal_attack.available = True
        
        # 奥义按钮 - 放在底部中央右侧
        mystery_art = Button(
            x=SCREEN_WIDTH * 0.75 - button_width/2,
            y=button_y,
            width=button_width,
            height=button_height,
            text=f"奥义: {current_character.mystery_art.name}",
            color=(255, 50, 50)
        )
        mystery_art.skill = current_character.mystery_art
        # 检查查克拉是否足够
        mystery_art.available = self.player_team.shared_chakra >= current_character.mystery_art.chakra_cost
        if not mystery_art.available:
            mystery_art.color = (100, 50, 50)
        
        # 添加到按钮列表
        self.skill_buttons = [normal_attack, mystery_art]
        
        # 添加操作提示信息
        self.battle_log.clear()
        self.battle_log.add_message(f"{current_character.name}的回合，请选择行动")
        self.battle_log.add_message("提示：点击下方蓝色或红色按钮选择技能")
        
        print(f"已创建技能按钮:")
        print(f"  普通攻击: {normal_attack.rect.x},{normal_attack.rect.y} 大小:{normal_attack.rect.width}x{normal_attack.rect.height}")
        print(f"  奥义攻击: {mystery_art.rect.x},{mystery_art.rect.y} 大小:{mystery_art.rect.width}x{mystery_art.rect.height}")
    
    def _on_end_turn_click(self):
        """结束回合按钮点击事件"""
        pass
    
    def _on_use_skill_click(self):
        """使用技能按钮点击事件"""
        if not self.selected_skill or not self.selected_target:
            return
            
        # 使用技能
        result = self.battle_system.use_skill(
            self.battle_state, 
            self.battle_state.current_character,
            self.selected_skill, 
            self.selected_target
        )
        
        # 记录战斗日志
        self.battle_log.add_message(result)
        
        # 清除选择
        self.selected_skill = None
        self.selected_target = None
        self.available_targets = []
        
        # 移除使用技能按钮
        if hasattr(self, 'use_skill_button'):
            delattr(self, 'use_skill_button')
        
        # 如果战斗结束，跳出
        if self.battle_state.is_battle_over:
            return
        
        # 手动切换到下一个角色行动    
        self.battle_state.next_character()
            
        # 准备下一个角色的回合
        self.prepare_next_turn()
    
    def prepare_next_turn(self):
        """准备下一个角色的回合"""
        # 获取下一个行动角色
        next_character = self.battle_system.get_next_acting_character(self.battle_state)
        
        if next_character:
            # 更新当前角色
            self.battle_state.current_character = next_character
            
            # 判断下一个角色属于哪个队伍
            if next_character in self.player_team.characters:
                self.battle_state.current_team = self.player_team
                self.is_player_turn = True
                self.is_waiting_for_action = True
                self.battle_log.add_message(f"{next_character.name}的回合，请选择行动")
                # 更新技能按钮
                self._update_skill_buttons()
            else:
                self.battle_state.current_team = self.enemy_team
                self.is_player_turn = False
                self.is_waiting_for_action = False
                self.battle_log.add_message(f"{next_character.name}的回合")
                # 执行AI行动
                self._execute_ai_action()
        else:
            # 如果没有下一个行动角色，可能战斗结束了
            self._check_battle_end()
    
    def _execute_ai_action(self):
        """执行AI行动"""
        current_character = self.battle_state.current_character
        if not current_character or current_character.is_alive == False:
            self.prepare_next_turn()
            return
            
        # 简单AI：选择普通攻击或奥义
        # 有30%概率使用奥义，如果查克拉足够
        use_mystery = (
            self.enemy_team.shared_chakra >= current_character.mystery_art.chakra_cost and 
            random.random() < 0.3
        )
        
        skill = current_character.mystery_art if use_mystery else current_character.normal_attack
        
        # 选择一个随机的有效目标
        valid_targets = self.battle_system.get_valid_targets(self.battle_state, current_character, skill)
        
        if valid_targets:
            target = random.choice(valid_targets)
            
            # 使用技能
            result = self.battle_system.use_skill(
                self.battle_state, 
                current_character, 
                skill, 
                target
            )
            
            # 添加到战斗日志
            skill_type = "奥义" if use_mystery else "普攻"
            self.battle_log.add_message(f"敌方{current_character.name}使用{skill_type}{skill.name}!")
            self.battle_log.add_message(result)
            
            # 如果战斗结束，跳出
            if self.battle_state.is_battle_over:
                return
            
            # 等待一会儿以便玩家可以看到AI的动作
            pygame.time.wait(800)
            
            # 准备下一个角色的回合
            self.prepare_next_turn()
        else:
            # 如果没有有效目标，直接准备下一个角色
            self.prepare_next_turn()
    
    def _check_battle_end(self):
        """检查战斗是否结束"""
        if not self.player_team.is_team_alive() or not self.enemy_team.is_team_alive():
            self.battle_state.is_battle_over = True
            
            # 显示战斗结果
            if self.player_team.is_team_alive():
                self.battle_log.add_message("战斗胜利！你的队伍获胜！")
            else:
                self.battle_log.add_message("战斗失败！敌方队伍获胜！")
    
    def handle_event(self, event):
        """处理事件"""
        # 先处理更新悬停状态
        mouse_pos = pygame.mouse.get_pos()
        
        # 更新按钮悬停状态
        if hasattr(self, 'skill_buttons'):
            for button in self.skill_buttons:
                button.update(chakra=None, mouse_pos=mouse_pos)
        
        if hasattr(self, 'use_skill_button'):
            self.use_skill_button.update(chakra=None, mouse_pos=mouse_pos)
        
        if hasattr(self, 'back_to_title_button'):
            self.back_to_title_button.update(chakra=None, mouse_pos=mouse_pos)
            
        # 如果战斗已结束，只处理返回按钮
        if self.battle_state.is_battle_over:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.back_to_title_button.rect.collidepoint(event.pos):
                    self._on_back_to_title_click()
            return
            
        # 如果不是玩家回合或者不需要等待玩家操作，不处理输入
        if not self.is_waiting_for_action:
            return
            
        # 处理鼠标按钮点击
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = event.pos
            
            # 如果用户还没选择技能，检查技能按钮点击
            if not self.selected_skill:
                # 技能按钮点击
                for button in self.skill_buttons:
                    if button.rect.collidepoint(mouse_pos) and button.available:
                        self.selected_skill = button.skill
                        # 调用battle_state的select_skill方法
                        self.available_targets = self.battle_system.get_valid_targets(
                            self.battle_state, 
                            self.battle_state.current_character,
                            self.selected_skill
                        )
                        # 清除之前的日志，显示新的选择信息
                        self.battle_log.clear()
                        self.battle_log.add_message(f"选择了技能: {self.selected_skill.name}")
                        self.battle_log.add_message(f"描述: {self.selected_skill.description}")
                        self.battle_log.add_message(f"请点击敌方角色(右侧红色区域)作为目标")
                        
                        # 测试输出按钮点击信息
                        print(f"技能按钮被点击: {self.selected_skill.name}")
                        print(f"有效目标数量: {len(self.available_targets)}")
                        return
            
            # 如果已选择技能但没选择目标，检查目标点击
            elif self.selected_skill and not self.selected_target:
                # 优先检查战场上的角色图像
                for character in self.available_targets:
                    # 检查角色的战场坐标
                    char_size = 64
                    char_rect = pygame.Rect(
                        character.battle_position[0] - char_size // 2,
                        character.battle_position[1] - char_size // 2,
                        char_size,
                        char_size
                    )
                    if char_rect.collidepoint(mouse_pos):
                        self.selected_target = character
                        self.battle_state.select_targets([self.selected_target])
                        self._create_use_skill_button()
                        return
                    
                # 检查角色卡片
                for card in self.player_cards + self.enemy_cards:
                    if card.character in self.available_targets and card.rect.collidepoint(mouse_pos):
                        self.selected_target = card.character
                        # 调用battle_state的select_targets方法
                        self.battle_state.select_targets([self.selected_target])
                        self._create_use_skill_button()
                        return
            
            # 如果已选择技能和目标，检查使用技能按钮点击
            elif self.selected_skill and self.selected_target and hasattr(self, 'use_skill_button'):
                if self.use_skill_button.rect.collidepoint(mouse_pos):
                    self._on_use_skill_click()
                    return
                    
            # 点击了其他区域，重置选择状态（取消当前选择）
            if self.selected_skill:
                self.battle_log.clear()
                self.battle_log.add_message("已取消选择")
                self.battle_log.add_message("请重新选择技能")
                self.selected_skill = None
                self.selected_target = None
                self.available_targets = []
                if hasattr(self, 'use_skill_button'):
                    delattr(self, 'use_skill_button')
                return
    
    def _on_back_to_title_click(self):
        """返回标题按钮点击事件"""
        self.switch_to_scene(TitleScene)
    
    def _on_character_card_click(self, character):
        """角色卡片点击事件"""
        # 如果有选择技能且角色是有效目标
        if self.selected_skill and character in self.available_targets:
            self.selected_target = character
    
    def _update_ui_from_battle_state(self):
        """从战斗状态更新UI"""
        # 更新角色卡片
        for card in self.player_cards:
            card.update()
        
        for card in self.enemy_cards:
            card.update()
        
        # 更新战斗日志
        for log in self.battle_state.battle_log[-8:]:  # 只显示最近的8条日志
            if log not in self.battle_log.messages:
                self.battle_log.add_message(log)
        
        # 检查是否是玩家回合
        self.is_player_turn = (
            self.battle_state.current_team == self.player_team and 
            not self.battle_state.is_battle_over
        )
        
        # 检查是否需要玩家选择行动
        self.is_waiting_for_action = (
            self.is_player_turn and 
            self.battle_state.phase == "CHARACTER_ACTION" and
            self.battle_state.current_character is not None
        )
        
        # 如果是玩家回合，更新技能按钮
        if self.is_waiting_for_action and not self.selected_skill:
            self._update_skill_buttons()
            print("已更新技能按钮")
            print(f"当前角色: {self.battle_state.current_character.name}")
            print(f"技能按钮数量: {len(self.skill_buttons)}")
            print(f"技能按钮位置: ({self.skill_buttons[0].rect.x}, {self.skill_buttons[0].rect.y})")
            print(f"技能按钮大小: {self.skill_buttons[0].rect.width}x{self.skill_buttons[0].rect.height}")
    
    def start_battle(self):
        """开始战斗"""
        # 清空之前的日志
        self.battle_log.clear()
        
        # 初始化战斗系统
        self.battle_state = self.battle_system.create_battle(self.player_team, self.enemy_team)
        
        # 添加初始消息
        self.battle_log.add_message("战斗开始！")
        self.battle_log.add_message(f"第七班 VS 第十班")
        
        # 确定先手
        first_team = self.battle_system.determine_first_team(self.battle_state)
        if first_team == self.player_team:
            self.battle_log.add_message("你方先手！")
            self.battle_state.current_team = self.player_team
            self.is_player_turn = True
        else:
            self.battle_log.add_message("敌方先手！")
            self.battle_state.current_team = self.enemy_team
            self.is_player_turn = False
        
        # 获取当前行动角色并设置标志
        self.battle_state.current_character = self.battle_system.get_next_acting_character(self.battle_state)
        
        if self.is_player_turn:
            self.is_waiting_for_action = True
            self._update_skill_buttons()
            self.battle_log.add_message(f"{self.battle_state.current_character.name}的回合，请选择行动")
        else:
            self.is_waiting_for_action = False
    
    def update(self):
        """更新场景状态"""
        # 更新闪烁效果计时器
        self.highlight_timer = (self.highlight_timer + 1) % self.highlight_max
        
        # 获取鼠标位置
        mouse_pos = pygame.mouse.get_pos()
        
        # 更新按钮悬停状态
        if hasattr(self, 'skill_buttons'):
            for button in self.skill_buttons:
                button.update(chakra=None, mouse_pos=mouse_pos)
        
        if hasattr(self, 'use_skill_button'):
            self.use_skill_button.update(chakra=None, mouse_pos=mouse_pos)
            
        if hasattr(self, 'back_to_title_button'):
            self.back_to_title_button.update(chakra=None, mouse_pos=mouse_pos)
        
        # 如果战斗已结束，只更新返回按钮
        if self.battle_state.is_battle_over:
            return
        
        # 如果不是玩家回合，执行AI行动
        if not self.is_player_turn and not self.is_waiting_for_action:
            # 如果战斗未结束且有敌方角色待行动，开始AI行动
            if not self.battle_state.is_battle_over and self.battle_state.current_character in self.enemy_team.characters:
                self._execute_ai_action()
        
        # 更新角色移动
        for character in self.player_team.characters + self.enemy_team.characters:
            if character.is_moving:
                character.move_towards_target()
        
        # 更新角色卡片
        for card in self.player_cards + self.enemy_cards:
            card.update()
            card.update_hover(mouse_pos)
        
        # 更新UI状态
        self._update_ui_from_battle_state()
    
    def render(self, screen):
        """渲染场景"""
        # 填充背景
        screen.fill((30, 30, 50))  # 深蓝色背景
        
        # 绘制战场
        self._draw_battlefield(screen)
        
        # 绘制角色
        for character in self.player_team.characters + self.enemy_team.characters:
            if character.is_alive:
                # 缩放调整角色图像
                char_size = 64
                scaled_image = pygame.transform.scale(character.image, (char_size, char_size))
                screen.blit(scaled_image, (character.battle_position[0] - char_size // 2, character.battle_position[1] - char_size // 2))
                
                # 绘制简单的生命条
                hp_percent = character.current_hp / character.max_hp
                hp_width = 50
                hp_height = 5
                hp_x = character.battle_position[0] - hp_width // 2
                hp_y = character.battle_position[1] - char_size // 2 - 10
                
                # HP背景
                pygame.draw.rect(screen, RED, (hp_x, hp_y, hp_width, hp_height))
                # HP值
                if hp_percent > 0:
                    pygame.draw.rect(screen, GREEN, (hp_x, hp_y, int(hp_width * hp_percent), hp_height))
                
                # 显示角色名
                font = get_font(16)
                name_surface = font.render(character.name, True, WHITE)
                name_rect = name_surface.get_rect(center=(character.battle_position[0], character.battle_position[1] - char_size // 2 - 20))
                screen.blit(name_surface, name_rect)
        
        # 绘制角色卡片
        for card in self.player_cards + self.enemy_cards:
            card.draw(screen)
        
        # 绘制战斗日志
        self.battle_log.draw(screen)
        
        # 绘制查克拉
        self._draw_chakra_bars(screen)
        
        # 绘制当前行动角色信息
        self._draw_current_character_info(screen)
        
        # 绘制调试信息
        self._draw_debug_info(screen)
        
        # 如果是玩家回合，绘制技能按钮和目标选择UI
        if self.battle_state.phase == "CHARACTER_ACTION" and self.is_waiting_for_action:
            # 绘制操作指引
            font = get_font(28)
            guide_text = ""
            if not self.selected_skill:
                guide_text = "请点击下方蓝色或红色按钮选择技能"
            elif not self.selected_target:
                guide_text = "请点击敌方角色选择目标"
            else:
                guide_text = "点击绿色按钮确认使用技能"
                
            guide_surface = font.render(guide_text, True, YELLOW)
            guide_rect = guide_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 150))
            screen.blit(guide_surface, guide_rect)
            
            # 绘制技能按钮
            if hasattr(self, 'skill_buttons'):
                # 添加技能按钮背景框，使其更醒目
                for button in self.skill_buttons:
                    # 先绘制一个红色的背景框增强可见性
                    bg_rect = button.rect.inflate(20, 20)
                    pygame.draw.rect(screen, (150, 0, 0), bg_rect, border_radius=10)
                    button.draw(screen)
                    
                # 闪烁效果计算
                is_highlight_visible = self.highlight_timer < self.highlight_max / 2
                highlight_color = YELLOW
                    
                # 在按钮周围绘制一个醒目的边框
                if not self.selected_skill:
                    for button in self.skill_buttons:
                        # 绘制闪烁高亮框
                        if is_highlight_visible:
                            highlight_rect = button.rect.copy()
                            highlight_rect.inflate_ip(10, 10)
                            pygame.draw.rect(screen, highlight_color, highlight_rect, 3)
                        
                        # 绘制提示箭头
                        arrow_y = button.rect.y - 30
                        arrow_points = [
                            (button.rect.centerx, arrow_y),
                            (button.rect.centerx - 15, arrow_y - 15),
                            (button.rect.centerx + 15, arrow_y - 15)
                        ]
                        pygame.draw.polygon(screen, highlight_color, arrow_points)
            
            # 如果选择了技能但未选择目标，高亮可选目标
            if self.selected_skill and not self.selected_target:
                for character in self.available_targets:
                    # 高亮战场角色图像
                    if is_highlight_visible:
                        char_size = 70
                        highlight_rect = pygame.Rect(
                            character.battle_position[0] - char_size // 2,
                            character.battle_position[1] - char_size // 2,
                            char_size,
                            char_size
                        )
                        pygame.draw.rect(screen, highlight_color, highlight_rect, 3)
                    
                    # 添加"点击选择"提示
                    target_font = get_font(18)
                    target_text = "点击选择"
                    target_surface = target_font.render(target_text, True, highlight_color)
                    target_rect = target_surface.get_rect(center=(character.battle_position[0], character.battle_position[1] - 40))
                    screen.blit(target_surface, target_rect)
                    
                    # 绘制指向目标的箭头
                    arrow_y = character.battle_position[1] + 40
                    arrow_points = [
                        (character.battle_position[0], arrow_y),
                        (character.battle_position[0] - 15, arrow_y + 15),
                        (character.battle_position[0] + 15, arrow_y + 15)
                    ]
                    pygame.draw.polygon(screen, highlight_color, arrow_points)
                    
                    # 找到对应的卡片
                    for card in self.player_cards + self.enemy_cards:
                        if card.character == character:
                            # 绘制一个高亮框
                            if is_highlight_visible:
                                highlight_rect = card.rect.copy()
                                highlight_rect.inflate_ip(10, 10)
                                pygame.draw.rect(screen, highlight_color, highlight_rect, 3)
            
            # 如果选择了技能和目标，绘制使用技能按钮并高亮显示
            if self.selected_skill and self.selected_target and hasattr(self, 'use_skill_button'):
                # 先绘制一个绿色的背景框增强可见性
                bg_rect = self.use_skill_button.rect.inflate(20, 20)
                pygame.draw.rect(screen, (0, 150, 0), bg_rect, border_radius=10)
                self.use_skill_button.draw(screen)
                
                # 绘制高亮边框
                if is_highlight_visible:
                    highlight_rect = self.use_skill_button.rect.copy()
                    highlight_rect.inflate_ip(10, 10)
                    pygame.draw.rect(screen, highlight_color, highlight_rect, 3)
                
                # 绘制箭头指向使用技能按钮
                arrow_y = self.use_skill_button.rect.y - 20
                arrow_points = [
                    (self.use_skill_button.rect.centerx, arrow_y),
                    (self.use_skill_button.rect.centerx - 15, arrow_y - 15),
                    (self.use_skill_button.rect.centerx + 15, arrow_y - 15)
                ]
                pygame.draw.polygon(screen, highlight_color, arrow_points)
        
        # 如果战斗结束，绘制结果和返回按钮
        if self.battle_state.is_battle_over:
            # 创建半透明覆盖
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 128))
            screen.blit(overlay, (0, 0))
            
            # 绘制战斗结果文本
            result_text = "战斗胜利！" if not self.enemy_team.is_team_alive() else "战斗失败！"
            font = get_font(72, bold=True)
            result_surface = font.render(result_text, True, WHITE)
            result_rect = result_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 100))
            screen.blit(result_surface, result_rect)
            
            # 绘制返回按钮
            self.back_to_title_button.draw(screen)
    
    def _draw_battlefield(self, screen):
        """绘制战场"""
        # 简单的地面
        pygame.draw.rect(screen, (100, 100, 100), (0, 500, SCREEN_WIDTH, SCREEN_HEIGHT - 500))
        
        # 分隔线
        pygame.draw.line(screen, WHITE, (SCREEN_WIDTH // 2, 400), (SCREEN_WIDTH // 2, 500), 2)
        
        # 绘制对战场地标识
        font = get_font(36)
        player_text = "第七班"
        enemy_text = "第十班"
        
        player_surface = font.render(player_text, True, (100, 100, 255))
        enemy_surface = font.render(enemy_text, True, (255, 100, 100))
        
        player_rect = player_surface.get_rect(center=(SCREEN_WIDTH // 4, 450))
        enemy_rect = enemy_surface.get_rect(center=(SCREEN_WIDTH * 3 // 4, 450))
        
        screen.blit(player_surface, player_rect)
        screen.blit(enemy_surface, enemy_rect)
    
    def _draw_chakra_bars(self, screen):
        """绘制查克拉条"""
        # 玩家查克拉条
        player_chakra_percent = self.player_team.shared_chakra / self.player_team.max_chakra
        chakra_width = 200
        chakra_height = 20
        chakra_x = 50
        chakra_y = 50
        
        # 背景
        pygame.draw.rect(screen, (50, 50, 100), (chakra_x, chakra_y, chakra_width, chakra_height))
        # 查克拉值
        if player_chakra_percent > 0:
            pygame.draw.rect(screen, (0, 100, 255), (chakra_x, chakra_y, int(chakra_width * player_chakra_percent), chakra_height))
        # 边框
        pygame.draw.rect(screen, WHITE, (chakra_x, chakra_y, chakra_width, chakra_height), 1)
        
        # 显示数值
        font = get_font(24)
        chakra_text = f"查克拉: {self.player_team.shared_chakra}/{self.player_team.max_chakra}"
        chakra_surface = font.render(chakra_text, True, WHITE)
        chakra_rect = chakra_surface.get_rect(center=(chakra_x + chakra_width // 2, chakra_y + chakra_height // 2))
        screen.blit(chakra_surface, chakra_rect)
        
        # 敌人查克拉条
        enemy_chakra_percent = self.enemy_team.shared_chakra / self.enemy_team.max_chakra
        enemy_chakra_x = SCREEN_WIDTH - chakra_width - 50
        
        # 背景
        pygame.draw.rect(screen, (100, 50, 50), (enemy_chakra_x, chakra_y, chakra_width, chakra_height))
        # 查克拉值
        if enemy_chakra_percent > 0:
            pygame.draw.rect(screen, (255, 100, 0), (enemy_chakra_x, chakra_y, int(chakra_width * enemy_chakra_percent), chakra_height))
        # 边框
        pygame.draw.rect(screen, WHITE, (enemy_chakra_x, chakra_y, chakra_width, chakra_height), 1)
        
        # 显示数值
        enemy_chakra_text = f"查克拉: {self.enemy_team.shared_chakra}/{self.enemy_team.max_chakra}"
        enemy_chakra_surface = font.render(enemy_chakra_text, True, WHITE)
        enemy_chakra_rect = enemy_chakra_surface.get_rect(center=(enemy_chakra_x + chakra_width // 2, chakra_y + chakra_height // 2))
        screen.blit(enemy_chakra_surface, enemy_chakra_rect)
    
    def _draw_current_character_info(self, screen):
        """绘制当前行动角色信息"""
        if not self.battle_state.current_character:
            return
            
        # 显示当前行动角色名称
        font = get_font(30)
        
        # 确定文本颜色
        text_color = GREEN if self.battle_state.current_team == self.player_team else RED
        
        info_text = f"当前行动: {self.battle_state.current_character.name}"
        info_surface = font.render(info_text, True, text_color)
        info_rect = info_surface.get_rect(center=(SCREEN_WIDTH // 2, 20))
        screen.blit(info_surface, info_rect)

    def _create_use_skill_button(self):
        """创建使用技能按钮"""
        self.battle_log.clear()
        self.battle_log.add_message(f"选择了目标: {self.selected_target.name}")
        self.battle_log.add_message(f"点击下方绿色按钮使用技能")
        
        # 创建使用技能按钮 - 放在屏幕底部正中央
        button_width = SCREEN_WIDTH * 0.3
        button_height = SCREEN_HEIGHT * 0.08
        self.use_skill_button = SkillButton(
            x=SCREEN_WIDTH * 0.5 - button_width/2,
            y=SCREEN_HEIGHT * 0.88,
            width=button_width,
            height=button_height,
            skill=self.selected_skill,
            color=(50, 200, 50)
        )
        
        print(f"已选择目标: {self.selected_target.name}")
        print(f"已创建使用技能按钮: {self.use_skill_button.rect.x},{self.use_skill_button.rect.y} 大小:{self.use_skill_button.rect.width}x{self.use_skill_button.rect.height}")

    def _draw_debug_info(self, screen):
        """绘制调试信息"""
        font = get_font(18)
        
        # 绘制鼠标位置信息
        mouse_pos = pygame.mouse.get_pos()
        mouse_text = font.render(f"鼠标位置: {mouse_pos}", True, (255, 255, 255))
        screen.blit(mouse_text, (10, 10))
        
        # 绘制当前战斗状态
        state_text = f"战斗状态: {self.battle_state.phase}"
        state_surface = font.render(state_text, True, (255, 255, 255))
        screen.blit(state_surface, (10, 40))
        
        # 如果有技能按钮，显示它们的位置
        if self.skill_buttons and self.battle_state.phase == "CHARACTER_ACTION":
            for i, btn in enumerate(self.skill_buttons):
                btn_text = f"按钮{i+1}: {btn.text} 位置:{btn.rect}"
                btn_surface = font.render(btn_text, True, (255, 255, 0))
                screen.blit(btn_surface, (10, 70 + i * 25))
        
        # 如果正在确认技能，显示使用技能按钮位置
        if hasattr(self, 'use_skill_button') and self.selected_target:
            btn_text = f"使用技能按钮: {self.use_skill_button.rect}"
            btn_surface = font.render(btn_text, True, (255, 255, 0))
            screen.blit(btn_surface, (10, 70))


class Game:
    """游戏主类"""
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption(GAME_TITLE)
        self.clock = pygame.time.Clock()
        self.current_scene = None
    
    def run(self):
        """运行游戏主循环"""
        self.current_scene = TitleScene(self)
        
        running = True
        while running:
            # 处理事件
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                self.current_scene.handle_event(event)
            
            # 更新场景
            self.current_scene.update()
            
            # 检查场景切换
            if self.current_scene.next_scene:
                self.current_scene = self.current_scene.next_scene
                self.current_scene.next_scene = None
            
            # 渲染场景
            self.current_scene.render(self.screen)
            
            pygame.display.flip()
            self.clock.tick(FPS)
        
        pygame.quit()
        sys.exit() 