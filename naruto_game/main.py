import pygame
import sys
from naruto_game.config import SCREEN_WIDTH, SCREEN_HEIGHT, FPS, GAME_TITLE
from naruto_game.scenes import TitleScene, BattleScene

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption(GAME_TITLE)
        self.clock = pygame.time.Clock()
        self.running = True
        self.current_scene = None
    
    def change_scene(self, scene):
        self.current_scene = scene
    
    def run(self):
        # Start with title scene
        self.current_scene = TitleScene(self)
        
        # Main game loop
        while self.running:
            # Process events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                if self.current_scene:
                    self.current_scene.handle_event(event)
            
            # Update scene
            if self.current_scene:
                self.current_scene.update()
                
                # Check for scene change
                if self.current_scene.next_scene:
                    self.current_scene = self.current_scene.next_scene
            
            # Render scene
            if self.current_scene:
                self.current_scene.render(self.screen)
            
            # Update display
            pygame.display.flip()
            
            # Cap frame rate
            self.clock.tick(FPS)
        
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    game = Game()
    game.run() 