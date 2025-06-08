"""
状态效果模块：包含Buff和Debuff定义
"""

class StatusEffectDefinition:
    """状态效果的定义类"""
    def __init__(self, 
                 id, 
                 name, 
                 type='buff', 
                 max_stacks=1, 
                 duration_turns=1, 
                 is_permanent=False,
                 prevents_action=False,
                 description=""):
        self.id = id                                    # 状态唯一ID
        self.name = name                                # 状态名称，如"点燃"
        self.type = type                                # 类型："buff"或"debuff"
        self.max_stacks = max_stacks                    # 最大叠加层数
        self.duration_turns = duration_turns            # 持续回合数
        self.is_permanent = is_permanent                # 是否永久(不会自然消失的)
        self.prevents_action = prevents_action          # 是否阻止行动
        self.description = description                  # 描述文本
        
        # 效果函数，子类应覆盖这些方法
        self.on_apply_effects = []                      # 施加时立即触发的效果
        self.on_turn_start_effects = []                 # 每回合开始时触发的效果
        self.on_turn_end_effects = []                   # 每回合结束时触发的效果
        self.on_remove_effects = []                     # 移除时触发的效果
        self.stat_modifiers = []                        # 属性修改器
        
    def on_apply(self, target, source):
        """当状态被施加时"""
        for effect in self.on_apply_effects:
            effect(target, source, self)
            
    def on_turn_start(self, target, source):
        """回合开始时触发"""
        for effect in self.on_turn_start_effects:
            effect(target, source, self)
            
    def on_turn_end(self, target, source):
        """回合结束时触发"""
        for effect in self.on_turn_end_effects:
            effect(target, source, self)
            
    def on_remove(self, target, source):
        """当状态被移除时"""
        for effect in self.on_remove_effects:
            effect(target, source, self)
            
    def apply_stat_modifiers(self, target):
        """应用属性修改"""
        for modifier in self.stat_modifiers:
            modifier.apply(target)
            
    def remove_stat_modifiers(self, target):
        """移除属性修改"""
        for modifier in self.stat_modifiers:
            modifier.remove(target)
            
    def is_chase_state(self):
        """是否是可被追打的状态"""
        chase_states = ['小浮空', '大浮空', '倒地', '击退']
        return self.name in chase_states
        

class ActiveStatusEffect:
    """激活的状态效果实例"""
    def __init__(self, definition, source_character, target_character, applied_turn, stacks=1):
        self.definition = definition            # StatusEffectDefinition实例
        self.source_character = source_character # 施加效果的角色
        self.target_character = target_character # 接受效果的角色
        self.remaining_turns = definition.duration_turns   # 剩余回合数
        self.applied_turn = applied_turn        # 施加时的回合数
        self.stacks = stacks                    # 当前叠加层数
        
        # 方便访问的属性
        self.id = definition.id
        self.name = definition.name
        self.type = definition.type
        
    def is_expired(self):
        """检查效果是否已过期"""
        return self.remaining_turns <= 0 and not self.definition.is_permanent
        
    def update_turn_start(self):
        """回合开始时更新"""
        if not self.definition.is_permanent:
            self.definition.on_turn_start(self.target_character, self.source_character)
        
    def update_turn_end(self):
        """回合结束时更新"""
        if not self.definition.is_permanent:
            self.definition.on_turn_end(self.target_character, self.source_character)
            self.remaining_turns -= 1
            
    def add_stack(self):
        """增加一层叠加"""
        if self.stacks < self.definition.max_stacks:
            self.stacks += 1
            return True
        return False
        
    def reset_duration(self):
        """重置持续时间"""
        self.remaining_turns = self.definition.duration_turns


class StatModifier:
    """属性修改器"""
    def __init__(self, stat_name, value, is_percentage=False):
        self.stat_name = stat_name        # 要修改的属性名称
        self.value = value                # 修改值
        self.is_percentage = is_percentage # 是否是百分比修改
        
    def apply(self, target):
        """应用属性修改"""
        if hasattr(target, self.stat_name):
            # 保存原始值以便之后恢复
            if not hasattr(target, f"_original_{self.stat_name}"):
                setattr(target, f"_original_{self.stat_name}", getattr(target, self.stat_name))
                
            original_value = getattr(target, f"_original_{self.stat_name}")
            
            if self.is_percentage:
                # 百分比修改
                new_value = original_value * (1 + self.value / 100)
            else:
                # 固定值修改
                new_value = original_value + self.value
                
            setattr(target, self.stat_name, new_value)
            
    def remove(self, target):
        """移除属性修改，恢复原始值"""
        if hasattr(target, f"_original_{self.stat_name}"):
            original_value = getattr(target, f"_original_{self.stat_name}")
            setattr(target, self.stat_name, original_value)
            

# 预定义的状态效果
def create_attack_up(value=20, duration=2):
    """创建攻击力提升效果"""
    effect = StatusEffectDefinition(
        id="attack_up",
        name="攻击提升",
        type="buff",
        duration_turns=duration,
        description=f"提升攻击力{value}%"
    )
    effect.stat_modifiers.append(StatModifier("attack", value, is_percentage=True))
    return effect

def create_defense_up(value=20, duration=2):
    """创建防御力提升效果"""
    effect = StatusEffectDefinition(
        id="defense_up",
        name="防御提升",
        type="buff",
        duration_turns=duration,
        description=f"提升防御力{value}%"
    )
    effect.stat_modifiers.append(StatModifier("defense", value, is_percentage=True))
    return effect

def create_small_float(duration=1):
    """创建小浮空状态"""
    effect = StatusEffectDefinition(
        id="small_float",
        name="小浮空",
        type="debuff",
        duration_turns=duration,
        description="目标处于小浮空状态，可被特定追打攻击"
    )
    effect.is_chase_state_flag = True
    return effect

def create_big_float(duration=1):
    """创建大浮空状态"""
    effect = StatusEffectDefinition(
        id="big_float",
        name="大浮空",
        type="debuff",
        duration_turns=duration,
        description="目标处于大浮空状态，可被特定追打攻击"
    )
    effect.is_chase_state_flag = True
    return effect

def create_knockdown(duration=1):
    """创建倒地状态"""
    effect = StatusEffectDefinition(
        id="knockdown",
        name="倒地",
        type="debuff",
        duration_turns=duration,
        description="目标处于倒地状态，可被特定追打攻击"
    )
    effect.is_chase_state_flag = True
    return effect

def create_repel(duration=1):
    """创建击退状态"""
    effect = StatusEffectDefinition(
        id="repel",
        name="击退",
        type="debuff",
        duration_turns=duration,
        description="目标处于击退状态，可被特定追打攻击"
    )
    effect.is_chase_state_flag = True
    return effect

def create_ignite(damage_per_turn=10, duration=2):
    """创建点燃状态"""
    effect = StatusEffectDefinition(
        id="ignite",
        name="点燃",
        type="debuff",
        duration_turns=duration,
        description=f"每回合受到{damage_per_turn}点伤害"
    )
    
    # 定义每回合造成伤害的效果函数
    def dot_damage(target, source, effect_def):
        damage = damage_per_turn
        if target.current_hp > 0:
            target.take_damage(damage, source, "fire")
            print(f"{target.name}受到{damage}点点燃伤害")
            
    effect.on_turn_start_effects.append(dot_damage)
    return effect

def create_poison(damage_per_turn=8, duration=3):
    """创建中毒状态"""
    effect = StatusEffectDefinition(
        id="poison",
        name="中毒",
        type="debuff",
        duration_turns=duration,
        max_stacks=3,
        description=f"每回合受到{damage_per_turn}点伤害，最高叠加3层"
    )
    
    # 定义每回合造成伤害的效果函数
    def dot_damage(target, source, effect_def):
        # 伤害根据叠加层数增加
        active_effect = next((e for e in target.status_effects if e.id == "poison"), None)
        if active_effect:
            damage = damage_per_turn * active_effect.stacks
            if target.current_hp > 0:
                target.take_damage(damage, source, "poison")
                print(f"{target.name}受到{damage}点中毒伤害")
            
    effect.on_turn_start_effects.append(dot_damage)
    return effect

def create_seal(duration=1):
    """创建封穴状态"""
    effect = StatusEffectDefinition(
        id="seal",
        name="封穴",
        type="debuff",
        duration_turns=duration,
        description="无法使用奥义技能"
    )
    return effect

def create_immobilize(duration=1):
    """创建定身状态"""
    effect = StatusEffectDefinition(
        id="immobilize",
        name="定身",
        type="debuff",
        duration_turns=duration,
        prevents_action=True,
        description="无法行动"
    )
    return effect

def create_blind(duration=2, miss_chance=50):
    """创建目盲状态"""
    effect = StatusEffectDefinition(
        id="blind",
        name="目盲",
        type="debuff",
        duration_turns=duration,
        description=f"普通攻击有{miss_chance}%的几率失败"
    )
    return effect

def create_bleed(duration=2):
    """创建流血状态"""
    effect = StatusEffectDefinition(
        id="bleed",
        name="流血",
        type="debuff",
        duration_turns=duration
    )
    return effect

def create_stun(duration=1):
    """创建眩晕状态"""
    effect = StatusEffectDefinition(
        id="stun",
        name="眩晕",
        type="debuff",
        duration_turns=duration,
        prevents_action=True
    )
    return effect

def create_slow(duration=2):
    """创建减速状态"""
    effect = StatusEffectDefinition(
        id="slow",
        name="减速",
        type="debuff",
        duration_turns=duration
    )
    return effect

def create_mind_control(duration=2):
    """创建精神控制状态"""
    effect = StatusEffectDefinition(
        id="mind_control",
        name="精神控制",
        type="debuff",
        duration_turns=duration,
        prevents_action=True
    )
    return effect

def create_confusion(duration=1):
    """创建混乱状态"""
    effect = StatusEffectDefinition(
        id="confusion",
        name="混乱",
        type="debuff",
        duration_turns=duration
    )
    return effect 