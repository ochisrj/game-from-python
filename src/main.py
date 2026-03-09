import pygame
import imgui
import os
import random
import math
import time
from imgui.integrations.pygame import PygameRenderer
import OpenGL.GL as gl
import imgui_bundle

def main():
    pygame.init
    size = 1400,800

    pygame.display.set_mode(size,pygame.DOUBLEBUF | pygame.OPENGL)
    pygame.display.set_caption("VisGuiThon")

    imgui.create_context()
    renderer = PygameRenderer()
 
    io = imgui.get_io()
    io.display_size = size

    flag = imgui.WINDOW_MENU_BAR

    script_dir = os.path.dirname(__file__)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            renderer.process_event(event)

        renderer.process_inputs()

        imgui.new_frame()

        imgui.begin("TEST")
        imgui.text("lreoa")
        imgui.end()

        gl.glClearColor(0,0,0,1)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)

        imgui.render()
        renderer.render(imgui.get_draw_data())

        pygame.display.flip()
    
    renderer.shutdown()
    pygame.quit()

if __name__ == "__main__":
    main()


