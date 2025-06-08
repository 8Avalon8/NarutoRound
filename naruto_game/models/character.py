"""
角色与战队模块：定义角色和战队的基本功能
"""
import random
import pygame
import math
from naruto_game.utils.helpers import create_simple_character_image

class Character:
    """角色基类：定义一个忍者角色的基本属性和方法"""
    def __init__(self, id, name, max_hp, attack, defense, ninja_tech, resistance, speed, crit_rate=0.1, crit_damage=1.5, position=1):
        # 基本属性
        self.id = id
        self.name = name
        self.max_hp = max_hp
        self.current_hp = max_hp
        self.attack = attack
        self.defense = defense
        self.ninja_tech = ninja_tech
        self.resistance = resistance
        self.speed = speed
        self.crit_rate = crit_rate
        self.crit_damage = crit_damage
        self.position = position  # 手位(1-4)
        
        # 战场位置
        self.battle_position = (0, 0)  # 当前位置
        self.target_position = (0, 0)  # 目标位置
        self.move_speed = 5           # 移动速度
        self.is_moving = False        # 是否正在移动
        
        # 技能
        self.normal_attack = None  # 普攻
        self.mystery_art = None    # 奥义
        self.chase_skills = []     # 追打技能
        self.passive_skills = []   # 被动技能
        self.skills = []           # 所有技能的统一列表
        
        # 状态
        self.status_effects = []   # 状态效果列表
        self.is_alive = True       # 是否存活
        self.can_act = True        # 是否可以行动
        
        # 标签：用于识别角色属性、流派等
        self.tags = []
        
        # 创建简单的角色图像
        self.image = create_simple_character_image(name, (100, 100, 100))
    
    def move_towards_target(self):
        """向目标位置移动"""
        if not self.is_moving:
            return
            
        # 计算与目标的距离
        dx = self.target_position[0] - self.battle_position[0]
        dy = self.target_position[1] - self.battle_position[1]
        distance = math.sqrt(dx*dx + dy*dy)
        
        # 如果已经足够接近目标，直接到达
        if distance < self.move_speed:
            self.battle_position = self.target_position
            self.is_moving = False
            return
            
        # 否则，向目标移动
        move_ratio = self.move_speed / distance
        move_x = dx * move_ratio
        move_y = dy * move_ratio
        
        # 更新位置
        x, y = self.battle_position
        self.battle_position = (x + move_x, y + move_y)
    
    def start_move_to(self, target_pos):
        """开始移动到目标位置"""
        self.target_position = target_pos
        self.is_moving = True
    
    def take_damage(self, amount, source, damage_type="physical"):
        """受到伤害"""
        # 根据伤害类型和防御属性计算实际伤害
        actual_damage = amount
        
        if damage_type == "physical":
            actual_damage = self.calculate_physical_damage(amount, source)
        elif damage_type == "ninjutsu":
            actual_damage = self.calculate_ninjutsu_damage(amount, source)
            
        # 应用伤害
        self.current_hp -= actual_damage
        
        # 检查是否死亡
        if self.current_hp <= 0:
            self.current_hp = 0
            self.is_alive = False
            self.can_act = False
            
        return actual_damage
    
    def calculate_physical_damage(self, raw_damage, source=None):
        """计算物理伤害"""
        # 简单的伤害计算公式：伤害 * (100 / (100 + 防御力))
        damage_reduction = 100 / (100 + self.defense)
        return int(raw_damage * damage_reduction)
    
    def calculate_ninjutsu_damage(self, raw_damage, source=None):
        """计算忍术伤害"""
        # 简单的伤害计算公式：伤害 * (100 / (100 + 忍术防御))
        damage_reduction = 100 / (100 + self.resistance)
        return int(raw_damage * damage_reduction)
    
    def heal(self, amount):
        """治疗"""
        if not self.is_alive:
            return 0  # 无法治疗死亡角色
            
        old_hp = self.current_hp
        self.current_hp = min(self.current_hp + amount, self.max_hp)
        
        # 如果被治疗的角色之前没有生命值（例如复活），将其标记为活着
        if old_hp == 0 and self.current_hp > 0:
            self.is_alive = True
            self.can_act = True
            
        return self.current_hp - old_hp
    
    def add_status_effect(self, effect_definition, source, current_turn):
        """添加状态效果"""
        # 检查是否已有相同ID的效果
        existing_effect = next((effect for effect in self.status_effects if effect.id == effect_definition.id), None)
        
        if existing_effect:
            # 如果已存在且可叠加，增加层数
            if existing_effect.stacks < effect_definition.max_stacks:
                existing_effect.add_stack()
            # 刷新持续时间
            existing_effect.reset_duration()
        else:
            # 创建新的效果实例
            from naruto_game.models.status_effects import ActiveStatusEffect
            active_effect = ActiveStatusEffect(effect_definition, source, self, current_turn)
            
            # 应用状态效果
            effect_definition.on_apply(self, source)
            effect_definition.apply_stat_modifiers(self)
            
            # 检查是否有阻止行动的效果
            if effect_definition.prevents_action:
                self.can_act = False
                
            self.status_effects.append(active_effect)
    
    def remove_status_effect(self, effect):
        """移除状态效果"""
        if effect in self.status_effects:
            # 移除效果时触发
            effect.definition.on_remove(self, effect.source_character)
            effect.definition.remove_stat_modifiers(self)
            
            # 如果该效果阻止行动，检查是否恢复行动能力
            if effect.definition.prevents_action:
                # 检查是否还有其他阻止行动的效果
                has_other_preventing_effects = any(e.definition.prevents_action for e in self.status_effects if e != effect)
                if not has_other_preventing_effects:
                    self.can_act = True
                    
            self.status_effects.remove(effect)
    
    def update_status_effects(self, is_turn_start, current_turn):
        """更新状态效果"""
        # 复制列表，因为在迭代过程中可能会移除元素
        effects_to_update = self.status_effects.copy()
        
        for effect in effects_to_update:
            if is_turn_start:
                effect.update_turn_start()
            else:
                effect.update_turn_end()
                
            # 检查效果是否已过期
            if effect.is_expired():
                self.remove_status_effect(effect)
    
    def reset_for_new_turn(self):
        """为新回合准备角色状态"""
        # 重置行动状态（如果没有阻止行动的效果）
        if not any(effect.definition.prevents_action for effect in self.status_effects):
            self.can_act = True
            
        # 更新技能冷却
        for skill in self.skills:
            skill.update_cooldown()


class BattleTeam:
    """战斗队伍"""
    def __init__(self, player_id, characters, shared_chakra=0, max_chakra=100, chakra_per_turn=20):
        self.player_id = player_id              # 玩家ID
        self.characters = characters            # 角色列表
        self.shared_chakra = shared_chakra      # 共享查克拉
        self.max_chakra = max_chakra            # 最大查克拉
        self.chakra_per_turn = chakra_per_turn  # 每回合回复查克拉量
        self.team_buffs = []                    # 队伍增益效果
        
        # 按手位排序角色
        self.characters.sort(key=lambda char: char.position)
    
    def update_chakra_per_turn(self):
        """每回合更新查克拉"""
        self.shared_chakra = min(self.shared_chakra + self.chakra_per_turn, self.max_chakra)
        
    def is_team_alive(self):
        """检查队伍是否还有存活角色"""
        return any(char.is_alive for char in self.characters)
    
    def get_characters_by_position(self):
        """按照手位返回排序后的角色列表"""
        return sorted([char for char in self.characters if char.is_alive], key=lambda x: x.position)
    
    def get_frontmost_character(self):
        """获取最前排的活着的角色"""
        alive_chars = [char for char in self.characters if char.is_alive]
        if alive_chars:
            return min(alive_chars, key=lambda char: char.position)
        return None
    
    def get_character_by_id(self, char_id):
        """通过ID获取角色"""
        for char in self.characters:
            if char.id == char_id:
                return char
        return None
    
    def reset_for_new_turn(self):
        """为新回合准备队伍状态"""
        for character in self.characters:
            if character.is_alive:
                character.reset_for_new_turn()


# 预定义角色创建函数
def create_naruto():
    """创建漩涡鸣人角色"""
    from naruto_game.models.skills import create_naruto_skills
    
    naruto = Character(
        id="naruto",
        name="漩涡鸣人",
        max_hp=1200,
        attack=85,
        defense=70,
        ninja_tech=75,
        resistance=65,
        speed=80,
        position=1  # 第一手位
    )
    
    # 设置角色标签和颜色
    naruto.tags = ["第七班", "木叶", "九尾人柱力"]
    # 设置角色图像
    naruto.image = create_simple_character_image("漩涡鸣人", (255, 165, 0))  # 橙色
    
    # 设置技能
    skills = create_naruto_skills()
    naruto.normal_attack = skills["normal_attack"]
    naruto.mystery_art = skills["mystery_art"]
    naruto.chase_skills = skills["chase_skills"]
    naruto.passive_skills = skills["passive_skills"]
    naruto.skills = skills["skills"]
    
    return naruto

def create_sasuke():
    """创建宇智波佐助角色"""
    from naruto_game.models.skills import create_sasuke_skills
    
    sasuke = Character(
        id="sasuke",
        name="宇智波佐助",
        max_hp=1050,
        attack=95,
        defense=65,
        ninja_tech=90,
        resistance=80,
        speed=85,
        position=2  # 第二手位
    )
    
    # 设置角色标签和颜色
    sasuke.tags = ["第七班", "木叶", "写轮眼", "带刀"]
    # 设置角色图像
    sasuke.image = create_simple_character_image("宇智波佐助", (0, 0, 255))  # 蓝色
    
    # 设置技能
    skills = create_sasuke_skills()
    sasuke.normal_attack = skills["normal_attack"]
    sasuke.mystery_art = skills["mystery_art"]
    sasuke.chase_skills = skills["chase_skills"]
    sasuke.passive_skills = skills["passive_skills"]
    sasuke.skills = skills["skills"]
    
    return sasuke

def create_sakura():
    """创建春野樱角色"""
    from naruto_game.models.skills import create_sakura_skills
    
    sakura = Character(
        id="sakura",
        name="春野樱",
        max_hp=950,
        attack=65,
        defense=60,
        ninja_tech=85,
        resistance=75,
        speed=75,
        position=3  # 第三手位
    )
    
    # 设置角色标签和颜色
    sakura.tags = ["第七班", "木叶", "医疗忍者"]
    # 设置角色图像
    sakura.image = create_simple_character_image("春野樱", (255, 105, 180))  # 粉色
    
    # 设置技能
    skills = create_sakura_skills()
    sakura.normal_attack = skills["normal_attack"]
    sakura.mystery_art = skills["mystery_art"]
    sakura.chase_skills = skills["chase_skills"]
    sakura.passive_skills = skills["passive_skills"]
    sakura.skills = skills["skills"]
    
    return sakura

def create_kakashi():
    """创建旗木卡卡西角色"""
    from naruto_game.models.skills import create_kakashi_skills
    
    kakashi = Character(
        id="kakashi",
        name="旗木卡卡西",
        max_hp=1100,
        attack=80,
        defense=75,
        ninja_tech=90,
        resistance=85,
        speed=90,
        position=4  # 第四手位
    )
    
    # 设置角色标签和颜色
    kakashi.tags = ["第七班", "木叶", "上忍", "写轮眼"]
    # 设置角色图像
    kakashi.image = create_simple_character_image("旗木卡卡西", (192, 192, 192))  # 银色
    
    # 设置技能
    skills = create_kakashi_skills()
    kakashi.normal_attack = skills["normal_attack"]
    kakashi.mystery_art = skills["mystery_art"]
    kakashi.chase_skills = skills["chase_skills"]
    kakashi.passive_skills = skills["passive_skills"]
    kakashi.skills = skills["skills"]
    
    return kakashi

def create_shikamaru():
    """创建奈良鹿丸角色"""
    from naruto_game.models.skills import create_shikamaru_skills
    
    shikamaru = Character(
        id="shikamaru",
        name="奈良鹿丸",
        max_hp=950,
        attack=70,
        defense=65,
        ninja_tech=95,
        resistance=80,
        speed=75,
        position=1  # 第一手位
    )
    
    # 设置角色标签和颜色
    shikamaru.tags = ["第十班", "木叶", "奈良一族"]
    # 设置角色图像
    shikamaru.image = create_simple_character_image("奈良鹿丸", (50, 50, 50))  # 暗灰色
    
    # 设置技能
    skills = create_shikamaru_skills()
    shikamaru.normal_attack = skills["normal_attack"]
    shikamaru.mystery_art = skills["mystery_art"]
    shikamaru.chase_skills = skills["chase_skills"]
    shikamaru.passive_skills = skills["passive_skills"]
    shikamaru.skills = skills["skills"]
    
    return shikamaru

def create_choji():
    """创建秋道丁次角色"""
    from naruto_game.models.skills import create_choji_skills
    
    choji = Character(
        id="choji",
        name="秋道丁次",
        max_hp=1300,
        attack=90,
        defense=85,
        ninja_tech=60,
        resistance=70,
        speed=65,
        position=2  # 第二手位
    )
    
    # 设置角色标签和颜色
    choji.tags = ["第十班", "木叶", "秋道一族"]
    # 设置角色图像
    choji.image = create_simple_character_image("秋道丁次", (165, 42, 42))  # 棕色
    
    # 设置技能
    skills = create_choji_skills()
    choji.normal_attack = skills["normal_attack"]
    choji.mystery_art = skills["mystery_art"]
    choji.chase_skills = skills["chase_skills"]
    choji.passive_skills = skills["passive_skills"]
    choji.skills = skills["skills"]
    
    return choji

def create_ino():
    """创建山中井野角色"""
    from naruto_game.models.skills import create_ino_skills
    
    ino = Character(
        id="ino",
        name="山中井野",
        max_hp=900,
        attack=65,
        defense=60,
        ninja_tech=90,
        resistance=75,
        speed=80,
        position=3  # 第三手位
    )
    
    # 设置角色标签和颜色
    ino.tags = ["第十班", "木叶", "山中一族"]
    # 设置角色图像
    ino.image = create_simple_character_image("山中井野", (173, 216, 230))  # 浅蓝色
    
    # 设置技能
    skills = create_ino_skills()
    ino.normal_attack = skills["normal_attack"]
    ino.mystery_art = skills["mystery_art"]
    ino.chase_skills = skills["chase_skills"]
    ino.passive_skills = skills["passive_skills"]
    ino.skills = skills["skills"]
    
    return ino

def create_team7():
    """创建第七班小队"""
    team7 = BattleTeam(
        player_id="player",
        characters=[create_naruto(), create_sasuke(), create_sakura(), create_kakashi()],
        shared_chakra=50
    )
    return team7

def create_team10():
    """创建第十班小队（鹿丸班）"""
    team10 = BattleTeam(
        player_id="enemy",
        characters=[create_shikamaru(), create_choji(), create_ino()],
        shared_chakra=50
    )
    return team10 