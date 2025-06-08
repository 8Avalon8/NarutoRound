"""
技能模块：包含普攻、奥义、追打等各种技能的定义
"""
import random
from naruto_game.models.status_effects import *

class Skill:
    """技能基类"""
    def __init__(self, 
                 id, 
                 name, 
                 type, 
                 description="",
                 chakra_cost=0,
                 cooldown_turns=0):
        self.id = id                          # 技能ID
        self.name = name                      # 技能名称
        self.type = type                      # 类型：'NORMAL' | 'MYSTERY' | 'CHASE' | 'PASSIVE'
        self.description = description        # 描述
        self.chakra_cost = chakra_cost        # 查克拉消耗
        self.cooldown_turns = cooldown_turns  # 冷却回合
        self.current_cooldown = 0             # 当前剩余冷却
        
        # 目标选择类型
        self.target_type = "single_enemy"     # 默认为单体敌人
        self.target_count = 1                 # 目标数量
        
        # 技能效果列表
        self.effects = []                     # 技能效果
        
    def use(self, user, targets, battle_state):
        """使用技能的通用逻辑"""
        # 检查查克拉是否足够
        if battle_state.current_team.shared_chakra < self.chakra_cost:
            return False, f"{user.name}的查克拉不足，无法使用{self.name}"
        
        # 消耗查克拉
        battle_state.current_team.shared_chakra -= self.chakra_cost
        
        # 设置冷却
        self.current_cooldown = self.cooldown_turns
        
        # 应用技能效果
        results = []
        for target in targets:
            result = self.apply_effects(user, target, battle_state)
            results.append(result)
            
        # 触发追打链（如果适用）
        chase_result = self.trigger_chase_attacks(user, targets, battle_state)
        if chase_result:
            results.extend(chase_result)
            
        return True, results
    
    def apply_effects(self, user, target, battle_state):
        """应用技能效果，应当由子类覆盖"""
        return f"{user.name}对{target.name}使用了{self.name}，但没有效果"
    
    def trigger_chase_attacks(self, user, targets, battle_state):
        """检查并触发追打链"""
        results = []
        
        # 只有非追打技能才能触发追打
        if self.type == 'CHASE':
            return results
        
        for target in targets:
            # 查找目标身上是否有可被追打的状态
            chase_states = [effect for effect in target.status_effects if effect.definition.is_chase_state()]
            
            if chase_states:
                # 如果有可追打状态，按手位顺序查找可以追打的角色
                for character in battle_state.current_team.get_characters_by_position():
                    # 跳过当前使用技能的角色
                    if character == user:
                        continue
                    
                    # 跳过已经失去行动能力的角色
                    if not character.can_act or not character.is_alive:
                        continue
                    
                    # 查找角色拥有的追打技能
                    for skill in character.skills:
                        if skill.type == 'CHASE' and skill.can_chase(target, chase_states):
                            # 执行追打
                            chase_success, chase_result = skill.use(character, [target], battle_state)
                            if chase_success:
                                results.append(chase_result)
                                # 更新目标状态，如果目标已经死亡则停止追打链
                                if not target.is_alive:
                                    return results
                                # 检查追打是否产生了新的可追打状态
                                break  # 每个角色只能追打一次
        
        return results
    
    def update_cooldown(self):
        """更新冷却回合"""
        if self.current_cooldown > 0:
            self.current_cooldown -= 1
    
    def get_valid_targets(self, user, battle_state):
        """根据目标类型获取有效目标列表"""
        player_team = battle_state.player_team
        enemy_team = battle_state.enemy_team
        
        # 确定当前队伍和敌对队伍
        current_team = player_team if user in player_team.characters else enemy_team
        opponent_team = enemy_team if current_team == player_team else player_team
        
        valid_targets = []
        
        if self.target_type == "single_enemy":
            # 单个敌人，默认选择正面敌人
            valid_targets = [opponent_team.get_frontmost_character()]
        elif self.target_type == "single_enemy_manual":
            # 手动选择一个敌人
            valid_targets = [char for char in opponent_team.characters if char.is_alive]
        elif self.target_type == "single_enemy_lowest_hp":
            # 选择生命值最低的敌人
            valid_targets = [min([char for char in opponent_team.characters if char.is_alive], key=lambda x: x.current_hp)]
        elif self.target_type == "all_enemies":
            # 所有敌人
            valid_targets = [char for char in opponent_team.characters if char.is_alive]
        elif self.target_type == "random_n_enemies":
            # 随机n个敌人
            alive_enemies = [char for char in opponent_team.characters if char.is_alive]
            count = min(self.target_count, len(alive_enemies))
            valid_targets = random.sample(alive_enemies, count)
        elif self.target_type == "self":
            # 自身
            valid_targets = [user]
        elif self.target_type == "single_ally":
            # 单个友方，默认选择自己
            valid_targets = [user]
        elif self.target_type == "all_allies":
            # 所有友方
            valid_targets = [char for char in current_team.characters if char.is_alive]
            
        return valid_targets
        

class NormalAttack(Skill):
    """普通攻击技能"""
    def __init__(self, 
                 id, 
                 name, 
                 damage_factor=1.0, 
                 description="",
                 status_effects=None,
                 causes_chase_state=None,
                 chase_state_chance=0.0):
        super().__init__(id, name, 'NORMAL', description, chakra_cost=0)
        self.damage_factor = damage_factor              # 伤害系数
        self.status_effects = status_effects or []      # 可能附带的状态效果
        self.causes_chase_state = causes_chase_state    # 可能造成的追打状态 (None | 'SMALL_FLOAT' | 'BIG_FLOAT' | 'KNOCKDOWN' | 'REPEL')
        self.chase_state_chance = chase_state_chance    # 触发追打状态的几率
        
    def apply_effects(self, user, target, battle_state):
        """应用普攻效果"""
        # 检查目标是否有目盲状态，影响命中率
        blind_effect = next((effect for effect in user.status_effects if effect.name == "目盲"), None)
        miss_chance = 0
        if blind_effect:
            miss_chance = 50  # 目盲状态使普攻有50%几率失败
            
        if random.random() < (miss_chance / 100):
            return f"{user.name}的{self.name}未命中{target.name}"
        
        # 计算伤害
        base_damage = user.attack * self.damage_factor
        damage = target.calculate_physical_damage(base_damage, user)
        
        # 应用伤害
        target.take_damage(damage, user, "physical")
        result = f"{user.name}对{target.name}使用{self.name}造成{damage}点伤害"
        
        # 应用状态效果
        for effect in self.status_effects:
            if random.random() < 0.7:  # 70%概率应用状态
                target.add_status_effect(effect, user, battle_state.turn_count)
                result += f"，并施加了{effect.name}"
        
        # 检查是否触发追打状态
        if self.causes_chase_state and random.random() < self.chase_state_chance:
            chase_state = None
            if self.causes_chase_state == 'SMALL_FLOAT':
                chase_state = create_small_float()
            elif self.causes_chase_state == 'BIG_FLOAT':
                chase_state = create_big_float()
            elif self.causes_chase_state == 'KNOCKDOWN':
                chase_state = create_knockdown()
            elif self.causes_chase_state == 'REPEL':
                chase_state = create_repel()
                
            if chase_state:
                target.add_status_effect(chase_state, user, battle_state.turn_count)
                result += f"，触发了{chase_state.name}状态"
        
        return result


class MysterySkill(Skill):
    """奥义技能"""
    def __init__(self,
                 id,
                 name,
                 chakra_cost,
                 damage_factor=1.5,
                 description="",
                 cooldown_turns=0,
                 status_effects=None,
                 causes_chase_state=None,
                 chase_state_chance=0.0,
                 is_interruptible=True,
                 is_instant=False):
        super().__init__(id, name, 'MYSTERY', description, chakra_cost, cooldown_turns)
        self.damage_factor = damage_factor              # 伤害系数
        self.status_effects = status_effects or []      # 可能附带的状态效果
        self.causes_chase_state = causes_chase_state    # 可能造成的追打状态
        self.chase_state_chance = chase_state_chance    # 触发追打状态的几率
        self.is_interruptible = is_interruptible        # 是否可被打断
        self.is_instant = is_instant                    # 是否瞬发
        
    def apply_effects(self, user, target, battle_state):
        """应用奥义效果"""
        # 检查是否被封穴
        seal_effect = next((effect for effect in user.status_effects if effect.name == "封穴"), None)
        if seal_effect:
            return f"{user.name}被封穴，无法释放奥义{self.name}"
            
        # 检查是否被打断（如果可被打断）
        if self.is_interruptible and battle_state.check_interrupt(user):
            return f"{user.name}的{self.name}被打断"
        
        # 计算伤害
        base_damage = user.attack * self.damage_factor + user.ninja_tech * 0.5
        damage = target.calculate_ninjutsu_damage(base_damage, user)
        
        # 应用伤害
        target.take_damage(damage, user, "ninjutsu")
        result = f"{user.name}释放奥义{self.name}对{target.name}造成{damage}点伤害"
        
        # 应用状态效果
        for effect in self.status_effects:
            target.add_status_effect(effect, user, battle_state.turn_count)
            result += f"，并施加了{effect.name}"
        
        # 检查是否触发追打状态
        if self.causes_chase_state and random.random() < self.chase_state_chance:
            chase_state = None
            if self.causes_chase_state == 'SMALL_FLOAT':
                chase_state = create_small_float()
            elif self.causes_chase_state == 'BIG_FLOAT':
                chase_state = create_big_float()
            elif self.causes_chase_state == 'KNOCKDOWN':
                chase_state = create_knockdown()
            elif self.causes_chase_state == 'REPEL':
                chase_state = create_repel()
                
            if chase_state:
                target.add_status_effect(chase_state, user, battle_state.turn_count)
                result += f"，触发了{chase_state.name}状态"
        
        return result


class ChaseSkill(Skill):
    """追打技能"""
    def __init__(self,
                 id,
                 name,
                 requires_chase_state,  # 需要的追打状态类型
                 damage_factor=0.8,
                 description="",
                 causes_chase_state=None,
                 chase_state_chance=0.0,
                 status_effects=None):
        super().__init__(id, name, 'CHASE', description)
        self.requires_chase_state = requires_chase_state  # 需要的追打状态 ('SMALL_FLOAT' | 'BIG_FLOAT' | 'KNOCKDOWN' | 'REPEL')
        self.damage_factor = damage_factor                # 伤害系数
        self.causes_chase_state = causes_chase_state      # 可能造成的追打状态
        self.chase_state_chance = chase_state_chance      # 触发追打状态的几率
        self.status_effects = status_effects or []        # 可能附带的状态效果
    
    def can_chase(self, target, chase_states):
        """检查是否可以对目标执行追打"""
        required_state_name = ""
        if self.requires_chase_state == 'SMALL_FLOAT':
            required_state_name = "小浮空"
        elif self.requires_chase_state == 'BIG_FLOAT':
            required_state_name = "大浮空"
        elif self.requires_chase_state == 'KNOCKDOWN':
            required_state_name = "倒地"
        elif self.requires_chase_state == 'REPEL':
            required_state_name = "击退"
            
        return any(effect.name == required_state_name for effect in chase_states)
    
    def apply_effects(self, user, target, battle_state):
        """应用追打效果"""
        # 检查目标是否有正确的状态
        required_state_name = ""
        if self.requires_chase_state == 'SMALL_FLOAT':
            required_state_name = "小浮空"
        elif self.requires_chase_state == 'BIG_FLOAT':
            required_state_name = "大浮空"
        elif self.requires_chase_state == 'KNOCKDOWN':
            required_state_name = "倒地"
        elif self.requires_chase_state == 'REPEL':
            required_state_name = "击退"
            
        # 查找并移除原有的追打状态
        chase_state = next((effect for effect in target.status_effects if effect.name == required_state_name), None)
        if chase_state:
            target.remove_status_effect(chase_state)
        else:
            return f"{user.name}尝试追打{target.name}，但目标没有{required_state_name}状态"
        
        # 计算伤害
        base_damage = user.attack * self.damage_factor
        damage = target.calculate_physical_damage(base_damage, user)
        
        # 应用伤害
        target.take_damage(damage, user, "physical")
        result = f"{user.name}追打{target.name}的{required_state_name}，造成{damage}点伤害"
        
        # 应用状态效果
        for effect in self.status_effects:
            if random.random() < 0.7:  # 70%概率应用状态
                target.add_status_effect(effect, user, battle_state.turn_count)
                result += f"，并施加了{effect.name}"
        
        # 检查是否触发新的追打状态
        if self.causes_chase_state and random.random() < self.chase_state_chance:
            chase_state = None
            if self.causes_chase_state == 'SMALL_FLOAT':
                chase_state = create_small_float()
            elif self.causes_chase_state == 'BIG_FLOAT':
                chase_state = create_big_float()
            elif self.causes_chase_state == 'KNOCKDOWN':
                chase_state = create_knockdown()
            elif self.causes_chase_state == 'REPEL':
                chase_state = create_repel()
                
            if chase_state:
                target.add_status_effect(chase_state, user, battle_state.turn_count)
                result += f"，触发了{chase_state.name}状态"
        
        return result


class PassiveSkill(Skill):
    """被动技能"""
    def __init__(self,
                 id,
                 name,
                 description="",
                 trigger_condition=None,
                 trigger_effects=None):
        super().__init__(id, name, 'PASSIVE', description)
        self.trigger_condition = trigger_condition    # 触发条件
        self.trigger_effects = trigger_effects or []  # 触发效果
    
    def check_trigger(self, user, battle_state, **kwargs):
        """检查是否触发被动效果"""
        # 这个方法应该在适当的时机被调用，如回合开始、受到伤害时等
        if self.trigger_condition and self.trigger_condition(user, battle_state, **kwargs):
            for effect in self.trigger_effects:
                effect(user, battle_state, **kwargs)
            return True
        return False


# 预定义一些技能实例
def create_normal_punch():
    """创建基本拳击技能"""
    return NormalAttack(
        id="normal_punch",
        name="普通拳击",
        damage_factor=1.0,
        description="对目标造成100%攻击力的伤害"
    )

def create_naruto_skills():
    """创建漩涡鸣人的技能集"""
    # 普通攻击: 螺旋拳
    normal_attack = NormalAttack(
        id="naruto_normal",
        name="螺旋拳",
        damage_factor=1.0,
        description="鸣人使用体术进行攻击，有小几率使敌人进入小浮空状态",
        causes_chase_state="SMALL_FLOAT",
        chase_state_chance=0.3
    )
    
    # 奥义: 螺旋丸
    mystery_art = MysterySkill(
        id="naruto_mystery",
        name="螺旋丸",
        chakra_cost=30,
        damage_factor=1.8,
        description="鸣人使用螺旋丸攻击敌人，造成较大伤害并有高几率使敌人进入大浮空状态",
        causes_chase_state="BIG_FLOAT",
        chase_state_chance=0.7
    )
    
    # 追打: 影分身术连打
    shadow_clone_chase = ChaseSkill(
        id="naruto_chase_1",
        name="影分身术连打",
        requires_chase_state="SMALL_FLOAT",
        damage_factor=0.8,
        description="鸣人使用影分身术追打处于小浮空状态的敌人",
        causes_chase_state="KNOCKDOWN",
        chase_state_chance=0.5
    )
    
    # 被动: 九尾查克拉
    nine_tails_chakra = PassiveSkill(
        id="naruto_passive_1",
        name="九尾查克拉",
        description="鸣人在生命值低于30%时，攻击力提高20%"
    )
    
    # 所有技能列表
    skills = [normal_attack, mystery_art, shadow_clone_chase, nine_tails_chakra]
    
    # 返回技能字典
    return {
        "normal_attack": normal_attack,
        "mystery_art": mystery_art,
        "chase_skills": [shadow_clone_chase],
        "passive_skills": [nine_tails_chakra],
        "skills": skills
    }

def create_sasuke_skills():
    """创建宇智波佐助的技能集"""
    # 普通攻击: 手里剑术
    normal_attack = NormalAttack(
        id="sasuke_normal",
        name="手里剑术",
        damage_factor=1.1,
        description="佐助投掷手里剑攻击敌人，有小几率造成流血效果",
        status_effects=[create_bleed()]
    )
    
    # 奥义: 千鸟
    mystery_art = MysterySkill(
        id="sasuke_mystery",
        name="千鸟",
        chakra_cost=35,
        damage_factor=2.0,
        description="佐助使用千鸟直刺敌人，造成大量伤害并有几率使敌人进入击退状态",
        causes_chase_state="REPEL",
        chase_state_chance=0.6
    )
    
    # 追打: 狮子连弹
    lion_combo_chase = ChaseSkill(
        id="sasuke_chase_1",
        name="狮子连弹",
        requires_chase_state="BIG_FLOAT",
        damage_factor=0.9,
        description="佐助对处于大浮空状态的敌人使用连续攻击",
        causes_chase_state="KNOCKDOWN",
        chase_state_chance=0.8
    )
    
    # 所有技能列表
    skills = [normal_attack, mystery_art, lion_combo_chase]
    
    # 返回技能字典
    return {
        "normal_attack": normal_attack,
        "mystery_art": mystery_art,
        "chase_skills": [lion_combo_chase],
        "passive_skills": [],
        "skills": skills
    }

def create_sakura_skills():
    """创建春野樱的技能集"""
    # 普通攻击: 怪力拳
    normal_attack = NormalAttack(
        id="sakura_normal",
        name="怪力拳",
        damage_factor=0.9,
        description="小樱使用怪力拳攻击敌人，有几率造成敌人进入击退状态",
        causes_chase_state="KNOCKDOWN",
        chase_state_chance=0.4
    )
    
    # 奥义: 百印解放
    mystery_art = MysterySkill(
        id="sakura_mystery",
        name="百印解放",
        chakra_cost=40,
        damage_factor=0.0,  # 治疗技能没有伤害
        description="小樱解放额头的印记，恢复全队生命值"
    )
    mystery_art.target_type = "all_allies"
    
    # 治疗之触 - 自定义奥义效果
    def healing_touch_apply_effects(self, user, target, battle_state):
        # 移除目标的击退状态
        repel_effect = next((effect for effect in target.status_effects if effect.name == "击退"), None)
        if repel_effect:
            target.remove_status_effect(repel_effect)
        
        # 治疗目标
        heal_amount = user.ninja_tech * 0.8
        target.heal(heal_amount)
        
        return f"{user.name}使用{self.name}治疗了{target.name}，回复了{heal_amount}点生命值"
    
    # 替换原有的apply_effects方法
    mystery_art.apply_effects = healing_touch_apply_effects.__get__(mystery_art)
    
    # 追打: 治愈之手
    healing_touch_chase = ChaseSkill(
        id="sakura_chase_1",
        name="治愈之手",
        requires_chase_state="REPEL",
        damage_factor=0.0,  # 治疗技能没有伤害
        description="小樱对被击退的队友使用医疗忍术，移除击退状态并回复生命"
    )
    
    # 所有技能列表
    skills = [normal_attack, mystery_art, healing_touch_chase]
    
    # 返回技能字典
    return {
        "normal_attack": normal_attack,
        "mystery_art": mystery_art,
        "chase_skills": [healing_touch_chase],
        "passive_skills": [],
        "skills": skills
    }

def create_kakashi_skills():
    """创建旗木卡卡西的技能集"""
    # 普通攻击: 苦无投掷
    normal_attack = NormalAttack(
        id="kakashi_normal",
        name="苦无投掷",
        damage_factor=1.0,
        description="卡卡西投掷苦无攻击敌人"
    )
    
    # 奥义: 雷切
    mystery_art = MysterySkill(
        id="kakashi_mystery",
        name="雷切",
        chakra_cost=35,
        damage_factor=1.9,
        description="卡卡西使用雷切攻击敌人，造成大量伤害并有几率使敌人进入小浮空状态",
        causes_chase_state="SMALL_FLOAT",
        chase_state_chance=0.5
    )
    
    # 追打: 写轮眼复制
    sharingan_chase = ChaseSkill(
        id="kakashi_chase_1",
        name="写轮眼复制",
        requires_chase_state="KNOCKDOWN",
        damage_factor=1.0,
        description="卡卡西对倒地的敌人使用复制的忍术进行追击",
        status_effects=[create_stun(1)]  # 可能会附带眩晕效果
    )
    
    # 所有技能列表
    skills = [normal_attack, mystery_art, sharingan_chase]
    
    # 返回技能字典
    return {
        "normal_attack": normal_attack,
        "mystery_art": mystery_art,
        "chase_skills": [sharingan_chase],
        "passive_skills": [],
        "skills": skills
    }

def create_shikamaru_skills():
    """创建奈良鹿丸的技能集"""
    # 普通攻击: 影子模仿术
    normal_attack = NormalAttack(
        id="shikamaru_normal",
        name="影子模仿术",
        damage_factor=0.8,
        description="鹿丸使用影子束缚敌人，有几率造成减速效果",
        status_effects=[create_slow(2)]
    )
    
    # 奥义: 影子绞杀术
    mystery_art = MysterySkill(
        id="shikamaru_mystery",
        name="影子绞杀术",
        chakra_cost=30,
        damage_factor=1.6,
        description="鹿丸将影子延伸至敌人并绞杀，造成中等伤害并有几率使敌人进入倒地状态",
        causes_chase_state="KNOCKDOWN",
        chase_state_chance=0.6
    )
    
    # 追打: 影子缝合术
    shadow_sewing_chase = ChaseSkill(
        id="shikamaru_chase_1",
        name="影子缝合术",
        requires_chase_state="REPEL",
        damage_factor=0.7,
        description="鹿丸对被击退的敌人使用影子缝合术进行追击",
        status_effects=[create_immobilize(1)]
    )
    
    # 所有技能列表
    skills = [normal_attack, mystery_art, shadow_sewing_chase]
    
    # 返回技能字典
    return {
        "normal_attack": normal_attack,
        "mystery_art": mystery_art,
        "chase_skills": [shadow_sewing_chase],
        "passive_skills": [],
        "skills": skills
    }

def create_choji_skills():
    """创建秋道丁次的技能集"""
    # 普通攻击: 部分倍化
    normal_attack = NormalAttack(
        id="choji_normal",
        name="部分倍化",
        damage_factor=1.2,
        description="丁次使用倍化术增大手臂攻击敌人，有几率使敌人进入击退状态",
        causes_chase_state="REPEL",
        chase_state_chance=0.3
    )
    
    # 奥义: 肉弹战车
    mystery_art = MysterySkill(
        id="choji_mystery",
        name="肉弹战车",
        chakra_cost=35,
        damage_factor=1.7,
        description="丁次变身为肉弹冲向敌人，造成范围伤害并有几率使敌人进入倒地状态",
        causes_chase_state="KNOCKDOWN",
        chase_state_chance=0.5
    )
    mystery_art.target_type = "all_enemies"
    
    # 追打: 蝶化冲击
    butterfly_impact_chase = ChaseSkill(
        id="choji_chase_1",
        name="蝶化冲击",
        requires_chase_state="BIG_FLOAT",
        damage_factor=1.1,
        description="丁次对处于大浮空状态的敌人使用蝶化模式冲击",
        causes_chase_state="KNOCKDOWN",
        chase_state_chance=0.7
    )
    
    # 所有技能列表
    skills = [normal_attack, mystery_art, butterfly_impact_chase]
    
    # 返回技能字典
    return {
        "normal_attack": normal_attack,
        "mystery_art": mystery_art,
        "chase_skills": [butterfly_impact_chase],
        "passive_skills": [],
        "skills": skills
    }

def create_ino_skills():
    """创建山中井野的技能集"""
    # 普通攻击: 花卉投掷
    normal_attack = NormalAttack(
        id="ino_normal",
        name="花卉投掷",
        damage_factor=0.9,
        description="井野投掷特制花卉攻击敌人，有几率造成中毒效果",
        status_effects=[create_poison(2)]
    )
    
    # 奥义: 心转身之术
    mystery_art = MysterySkill(
        id="ino_mystery",
        name="心转身之术",
        chakra_cost=25,
        damage_factor=0.0,  # 控制技能没有伤害
        description="井野使用家族秘术暂时控制敌人的精神，使敌人无法行动",
        status_effects=[create_mind_control(2)]
    )
    
    # 追打: 精神冲击
    mind_shock_chase = ChaseSkill(
        id="ino_chase_1",
        name="精神冲击",
        requires_chase_state="SMALL_FLOAT",
        damage_factor=0.8,
        description="井野对处于小浮空状态的敌人进行精神冲击，有几率造成混乱状态",
        status_effects=[create_confusion(1)]
    )
    
    # 所有技能列表
    skills = [normal_attack, mystery_art, mind_shock_chase]
    
    # 返回技能字典
    return {
        "normal_attack": normal_attack,
        "mystery_art": mystery_art,
        "chase_skills": [mind_shock_chase],
        "passive_skills": [],
        "skills": skills
    } 