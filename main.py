import pygame
import sys
from game_manager import GameManager
from audio        import audio_init


def main():
    pygame.init()
    pygame.display.set_caption("Cell Wars — Defend the Human Body")
    screen = pygame.display.set_mode((1200, 750), pygame.RESIZABLE)
    clock  = pygame.time.Clock()
    audio_init()
    GameManager(screen).run(clock)
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
