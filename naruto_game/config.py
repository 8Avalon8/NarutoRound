"""
配置文件：定义游戏中使用的常量和配置
"""

# 屏幕设置
SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080
GAME_TITLE = "火影忍者OL战斗原型"
FPS = 60

# 颜色定义
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
ORANGE = (255, 165, 0)
PURPLE = (128, 0, 128)
GREY = (128, 128, 128)
LIGHT_GREY = (200, 200, 200)
TRANSPARENT = (0, 0, 0, 0)

# 战斗设置
MAX_CHAKRA = 100
CHAKRA_PER_TURN = 20
MAX_TEAM_SIZE = 4

# 状态效果
STATUS_EFFECT_TYPES = {
    'SMALL_FLOAT': '小浮空',
    'BIG_FLOAT': '大浮空',
    'KNOCKDOWN': '倒地',
    'REPEL': '击退',
    'IGNITE': '点燃',
    'POISON': '中毒',
    'SEAL': '封穴',
    'IMMOBILIZE': '定身',
    'CONFUSION': '混乱',
    'BLIND': '目盲',
    'PARALYZE': '麻痹',
    'SLEEP': '睡眠'
}

# 技能类型
SKILL_TYPES = {
    'NORMAL': '普攻',
    'MYSTERY': '奥义',
    'CHASE': '追打',
    'PASSIVE': '被动'
}

# 追打状态和相应技能的映射
CHASE_STATE_MAPPING = {
    'SMALL_FLOAT': '追打小浮空',
    'BIG_FLOAT': '追打大浮空',
    'KNOCKDOWN': '追打倒地',
    'REPEL': '追打击退'
}

# 战场位置
FIELD_POSITIONS = {
    'PLAYER_1': (200, 450),
    'PLAYER_2': (300, 500),
    'PLAYER_3': (400, 550),
    'PLAYER_4': (500, 600),
    'ENEMY_1': (800, 450),
    'ENEMY_2': (700, 500),
    'ENEMY_3': (600, 550),
    'ENEMY_4': (500, 600)
}

# 动画设置
ANIMATION_SPEED = 5
SKILL_ANIMATION_DURATION = 1.0  # 秒

# UI元素尺寸
BUTTON_WIDTH = 200
BUTTON_HEIGHT = 50
CHAR_CARD_WIDTH = 150
CHAR_CARD_HEIGHT = 200
HP_BAR_WIDTH = 100
HP_BAR_HEIGHT = 10 