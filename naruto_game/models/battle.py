"""
战斗系统模块：处理战斗的核心流程和逻辑
"""
import random
from naruto_game.models.status_effects import create_small_float, create_big_float, create_knockdown, create_repel

class BattleState:
    """战斗状态类：管理战斗流程和状态"""
    def __init__(self, player_team, enemy_team):
        self.player_team = player_team                # 玩家队伍
        self.enemy_team = enemy_team                  # 敌人队伍
        self.current_team = None                      # 当前行动的队伍
        self.current_character = None                 # 当前行动的角色
        self.turn_count = 0                           # 回合数
        self.battle_log = []                          # 战斗日志
        self.selected_skill = None                    # 选中的技能
        self.selected_targets = []                    # 选中的技能目标
        self.combo_count = 0                          # 当前连击数
        self.is_battle_over = False                   # 战斗是否结束
        
        # 战斗阶段
        self.phase = "BATTLE_START"  # 'BATTLE_START' | 'TURN_START' | 'CHARACTER_ACTION' | 'TURN_END' | 'BATTLE_END'
        
        # 初始状态下不要自动判定先攻，改由外部控制
    
    def start_battle(self):
        """开始战斗"""
        self.phase = "BATTLE_START"
        self.add_to_battle_log("战斗开始！")
        self.start_turn()
    
    def start_turn(self):
        """开始新回合"""
        self.phase = "TURN_START"
        self.turn_count += 1
        self.add_to_battle_log(f"第 {self.turn_count} 回合开始！")
        
        # 更新队伍状态（回复查克拉等）
        self.player_team.update_chakra_per_turn()
        self.enemy_team.update_chakra_per_turn()
        
        # 重置队伍状态
        self.player_team.reset_for_new_turn()
        self.enemy_team.reset_for_new_turn()
        
        # 处理回合开始时的状态效果
        self._process_turn_start_effects()
        
        # 开始角色行动
        self.start_character_action()
    
    def _process_turn_start_effects(self):
        """处理回合开始时的状态效果"""
        # 处理玩家队伍状态效果
        for character in self.player_team.characters:
            if character.is_alive:
                character.update_status_effects(is_turn_start=True, current_turn=self.turn_count)
                
        # 处理敌人队伍状态效果
        for character in self.enemy_team.characters:
            if character.is_alive:
                character.update_status_effects(is_turn_start=True, current_turn=self.turn_count)
    
    def _process_turn_end_effects(self):
        """处理回合结束时的状态效果"""
        # 处理玩家队伍状态效果
        for character in self.player_team.characters:
            if character.is_alive:
                character.update_status_effects(is_turn_start=False, current_turn=self.turn_count)
                
        # 处理敌人队伍状态效果
        for character in self.enemy_team.characters:
            if character.is_alive:
                character.update_status_effects(is_turn_start=False, current_turn=self.turn_count)
    
    def start_character_action(self):
        """开始角色行动阶段"""
        self.phase = "CHARACTER_ACTION"
        
        # 获取当前队伍中按手位排序的存活角色
        alive_characters = self.current_team.get_characters_by_position()
        
        if not alive_characters:
            self.end_team_turn()
            return
            
        # 找出第一个可以行动的角色
        for character in alive_characters:
            if character.can_act:
                self.current_character = character
                self.add_to_battle_log(f"{character.name} 行动！")
                
                # 如果是敌人，AI自动选择技能和目标
                if self.current_team == self.enemy_team:
                    self._ai_select_skill_and_targets()
                    self.use_current_skill()
                
                return
                
        # 如果没有角色可以行动，结束当前队伍的回合
        self.end_team_turn()
    
    def _ai_select_skill_and_targets(self):
        """AI自动选择技能和目标"""
        # 找出所有可用的技能（查克拉足够，没有在冷却）
        available_skills = []
        for skill in self.current_character.skills:
            if (skill.current_cooldown == 0 and 
                skill.type != 'PASSIVE' and 
                skill.type != 'CHASE' and
                self.current_team.shared_chakra >= skill.chakra_cost):
                available_skills.append(skill)
        
        if not available_skills:
            # 如果没有可用技能，选择第一个普攻
            for skill in self.current_character.skills:
                if skill.type == 'NORMAL':
                    self.selected_skill = skill
                    break
        else:
            # 优先选择奥义，其次是普攻
            # 有33%的概率选择奥义（如果有的话）
            mystery_skills = [s for s in available_skills if s.type == 'MYSTERY']
            normal_skills = [s for s in available_skills if s.type == 'NORMAL']
            
            if mystery_skills and random.random() < 0.33:
                self.selected_skill = random.choice(mystery_skills)
            elif normal_skills:
                self.selected_skill = random.choice(normal_skills)
            else:
                self.selected_skill = random.choice(available_skills)
        
        # 确保选择了技能
        if not self.selected_skill:
            # 如果意外没有选到技能，选择第一个普攻
            for skill in self.current_character.skills:
                if skill.type == 'NORMAL':
                    self.selected_skill = skill
                    break
        
        # 选择目标
        self.selected_targets = self.selected_skill.get_valid_targets(self.current_character, self)
    
    def select_skill(self, skill):
        """选择技能"""
        self.selected_skill = skill
        return skill.get_valid_targets(self.current_character, self)
    
    def select_targets(self, targets):
        """选择技能目标"""
        self.selected_targets = targets
    
    def use_current_skill(self):
        """使用当前选择的技能"""
        if not self.selected_skill or not self.selected_targets:
            self.add_to_battle_log("未选择技能或目标！")
            return False
        
        # 使用技能
        success, result = self.selected_skill.use(self.current_character, self.selected_targets, self)
        
        if success:
            if isinstance(result, list):
                for msg in result:
                    self.add_to_battle_log(msg)
            else:
                self.add_to_battle_log(result)
                
            # 检查战斗是否结束
            if self.check_battle_end():
                return True
                
            # 重置选择
            self.selected_skill = None
            self.selected_targets = []
            
            # 移动到下一个角色
            self.next_character()
            return True
        else:
            # 技能使用失败，比如查克拉不足
            self.add_to_battle_log(result)
            return False
    
    def next_character(self):
        """切换到下一个角色行动"""
        # 获取当前队伍中按手位排序的存活角色
        alive_characters = self.current_team.get_characters_by_position()
        
        # 找出当前角色的索引
        current_index = -1
        for i, character in enumerate(alive_characters):
            if character == self.current_character:
                current_index = i
                break
        
        # 查找下一个可以行动的角色
        next_character = None
        for i in range(current_index + 1, len(alive_characters)):
            if alive_characters[i].can_act:
                next_character = alive_characters[i]
                break
        
        if next_character:
            self.current_character = next_character
            self.add_to_battle_log(f"{next_character.name} 行动！")
            
            # 如果是敌人，AI自动选择技能和目标
            if self.current_team == self.enemy_team:
                self._ai_select_skill_and_targets()
                self.use_current_skill()
        else:
            # 当前队伍没有更多角色可以行动，结束该队伍的回合
            self.end_team_turn()
    
    def end_team_turn(self):
        """结束当前队伍的回合，切换到另一个队伍"""
        # 切换队伍
        if self.current_team == self.player_team:
            self.current_team = self.enemy_team
            self.add_to_battle_log("敌方队伍回合开始！")
        else:
            self.current_team = self.player_team
            self.add_to_battle_log("玩家队伍回合开始！")
            
            # 如果玩家队伍回合结束，也意味着整个回合的结束
            if self.current_team == self.player_team:
                self.end_turn()
                return
        
        # 开始新队伍的角色行动
        self.start_character_action()
    
    def end_turn(self):
        """结束当前回合"""
        self.phase = "TURN_END"
        self.add_to_battle_log(f"第 {self.turn_count} 回合结束！")
        
        # 处理回合结束效果
        self._process_turn_end_effects()
        
        # 检查战斗是否结束
        if self.check_battle_end():
            return
        
        # 开始新回合
        self.start_turn()
    
    def check_battle_end(self):
        """检查战斗是否结束"""
        player_alive = self.player_team.is_team_alive()
        enemy_alive = self.enemy_team.is_team_alive()
        
        if not player_alive:
            self.phase = "BATTLE_END"
            self.is_battle_over = True
            self.add_to_battle_log("玩家队伍全灭，战斗失败！")
            return True
        
        if not enemy_alive:
            self.phase = "BATTLE_END"
            self.is_battle_over = True
            self.add_to_battle_log("敌方队伍全灭，战斗胜利！")
            return True
        
        return False
    
    def check_interrupt(self, character):
        """检查技能是否被打断"""
        # 这里可以实现更复杂的打断逻辑
        # 简单起见，暂定有10%几率被打断
        return random.random() < 0.1
    
    def add_to_battle_log(self, message):
        """添加战斗日志"""
        self.battle_log.append(message)
        print(message)  # 调试用，实际应用中可以移除


class BattleSystem:
    """战斗系统：管理战斗的创建和流程控制"""
    
    def __init__(self):
        """初始化战斗系统"""
        self.battle_state = None
    
    def create_battle(self, player_team, enemy_team):
        """创建新的战斗并自动开始"""
        battle_state = BattleState(player_team, enemy_team)
        self.battle_state = battle_state
        self.determine_first_team(battle_state)  # 自动决定先攻
        self.start_battle(battle_state)  # 自动开始战斗
        return battle_state
        
    def determine_first_team(self, battle_state):
        """决定哪个队伍先行动"""
        # 简单地计算两个队伍的总先攻值
        player_initiative = sum(char.speed for char in battle_state.player_team.characters if char.is_alive)
        enemy_initiative = sum(char.speed for char in battle_state.enemy_team.characters if char.is_alive)
        
        # 添加一些随机性
        player_initiative += random.randint(1, 20)
        enemy_initiative += random.randint(1, 20)
        
        if player_initiative >= enemy_initiative:
            battle_state.current_team = battle_state.player_team
            return battle_state.player_team
        else:
            battle_state.current_team = battle_state.enemy_team
            return battle_state.enemy_team
    
    def get_next_acting_character(self, battle_state):
        """获取下一个可以行动的角色"""
        # 获取当前队伍中按手位排序的存活角色
        alive_characters = battle_state.current_team.get_characters_by_position()
        
        if not alive_characters:
            # 如果当前队伍没有存活角色，切换到另一个队伍
            if battle_state.current_team == battle_state.player_team:
                battle_state.current_team = battle_state.enemy_team
            else:
                battle_state.current_team = battle_state.player_team
                
            # 再次检查新队伍中的存活角色
            alive_characters = battle_state.current_team.get_characters_by_position()
            if not alive_characters:
                # 如果没有角色可以行动，可能战斗结束了
                return None
        
        # 找出第一个可以行动的角色
        for character in alive_characters:
            if character.can_act:
                return character
        
        # 如果没有角色可以行动，返回None
        return None
    
    def use_skill(self, battle_state, user, skill, target):
        """使用技能"""
        if not user.is_alive or not target.is_alive:
            return "无法使用技能，角色已倒下"
        
        # 检查查克拉是否足够
        current_team = battle_state.player_team if user in battle_state.player_team.characters else battle_state.enemy_team
        if current_team.shared_chakra < skill.chakra_cost:
            return f"{user.name}的查克拉不足，无法使用{skill.name}"
        
        # 消耗查克拉
        current_team.shared_chakra -= skill.chakra_cost
        
        # 计算伤害
        if hasattr(skill, "damage_factor") and skill.damage_factor > 0:
            if skill.type == "NORMAL" or skill.type == "CHASE":
                # 普通攻击和追打基于物理攻击
                raw_damage = user.attack * skill.damage_factor
                damage = target.calculate_physical_damage(raw_damage, user)
                target.take_damage(damage, user, "physical")
                result = f"{user.name}对{target.name}使用{skill.name}造成{damage}点伤害"
            elif skill.type == "MYSTERY":
                # 奥义基于忍术攻击
                raw_damage = user.ninja_tech * skill.damage_factor
                damage = target.calculate_ninjutsu_damage(raw_damage, user)
                target.take_damage(damage, user, "ninjutsu")
                result = f"{user.name}对{target.name}使用奥义{skill.name}造成{damage}点伤害"
        else:
            result = f"{user.name}对{target.name}使用{skill.name}"
            
        # 应用状态效果
        if hasattr(skill, "status_effects") and skill.status_effects:
            for effect in skill.status_effects:
                if random.random() < 0.7:  # 70%概率应用状态
                    target.add_status_effect(effect, user, battle_state.turn_count)
                    result += f"，并施加了{effect.name}"
        
        # 检查是否触发追打状态
        if hasattr(skill, "causes_chase_state") and skill.causes_chase_state and hasattr(skill, "chase_state_chance"):
            if random.random() < skill.chase_state_chance:
                chase_state = None
                if skill.causes_chase_state == 'SMALL_FLOAT':
                    chase_state = create_small_float()
                elif skill.causes_chase_state == 'BIG_FLOAT':
                    chase_state = create_big_float()
                elif skill.causes_chase_state == 'KNOCKDOWN':
                    chase_state = create_knockdown()
                elif skill.causes_chase_state == 'REPEL':
                    chase_state = create_repel()
                    
                if chase_state:
                    target.add_status_effect(chase_state, user, battle_state.turn_count)
                    result += f"，触发了{chase_state.name}状态"
        
        # 检查战斗是否结束
        if not target.is_alive:
            result += f"，{target.name}倒下了！"
            self._check_battle_end(battle_state)
        
        return result
    
    def get_valid_targets(self, battle_state, user, skill):
        """获取技能的有效目标"""
        current_team = battle_state.player_team if user in battle_state.player_team.characters else battle_state.enemy_team
        opponent_team = battle_state.enemy_team if current_team == battle_state.player_team else battle_state.player_team
        
        if skill.type == "NORMAL":
            # 普通攻击通常针对敌方单体
            return [char for char in opponent_team.characters if char.is_alive]
        elif skill.type == "MYSTERY":
            # 奥义根据target_type确定目标
            if hasattr(skill, "target_type"):
                if skill.target_type == "all_enemies":
                    return [char for char in opponent_team.characters if char.is_alive]
                elif skill.target_type == "all_allies":
                    return [char for char in current_team.characters if char.is_alive]
                else:
                    # 默认针对敌方单体
                    return [char for char in opponent_team.characters if char.is_alive]
            else:
                # 默认针对敌方单体
                return [char for char in opponent_team.characters if char.is_alive]
        elif skill.type == "CHASE":
            # 追打技能针对特定状态的敌人
            if not hasattr(skill, "requires_chase_state"):
                return []
                
            targets = []
            for char in opponent_team.characters:
                if not char.is_alive:
                    continue
                    
                # 检查是否有匹配的追打状态
                has_required_state = False
                for effect in char.status_effects:
                    effect_id = effect.definition.id if hasattr(effect, "definition") else ""
                    if skill.requires_chase_state == "SMALL_FLOAT" and effect_id == "small_float":
                        has_required_state = True
                        break
                    elif skill.requires_chase_state == "BIG_FLOAT" and effect_id == "big_float":
                        has_required_state = True
                        break
                    elif skill.requires_chase_state == "KNOCKDOWN" and effect_id == "knockdown":
                        has_required_state = True
                        break
                    elif skill.requires_chase_state == "REPEL" and effect_id == "repel":
                        has_required_state = True
                        break
                        
                if has_required_state:
                    targets.append(char)
            
            return targets
        
        # 默认返回空列表
        return []
    
    def _check_battle_end(self, battle_state):
        """检查战斗是否结束"""
        if not battle_state.player_team.is_team_alive():
            battle_state.is_battle_over = True
            return True
        
        if not battle_state.enemy_team.is_team_alive():
            battle_state.is_battle_over = True
            return True
        
        return False
    
    def start_battle(self, battle_state):
        """开始战斗"""
        battle_state.start_battle()
    
    def end_battle(self, battle_state):
        """结束战斗"""
        battle_state.is_battle_over = True 