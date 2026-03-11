import pygame
import imgui
import sys
from imgui.integrations.pygame import PygameRenderer
import OpenGL.GL as gl
import os

#ไทยโว้ยยยยยย

def main():
    pygame.init()
    size = 1400,800

    pygame.display.set_mode(size, pygame.DOUBLEBUF | pygame.OPENGL)
    pygame.display.set_caption("Pygame ImGui Example")

    imgui.create_context()
    renderer = PygameRenderer()

    io = imgui.get_io()
    io.display_size = size
    
    flags = imgui.WINDOW_MENU_BAR

    # Construct an absolute path to the font file
    # This is more reliable than a relative path
    script_dir = os.path.dirname(__file__)
    font_path = os.path.join(script_dir, "font", "Chandler42 Regular.otf")

    # Load the Thai font with the correct glyph ranges
    # and check if the file exists first
    if os.path.exists(font_path):
        io.fonts.add_font_from_file_ttf(
            font_path, 20, io.fonts.get_glyph_ranges_thai()
        )
        renderer.rebuild_font_atlas()
    else:
        print(f"Font file not found at: {font_path}")
        # Continue without the custom font
        pass

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            renderer.process_event(event)
        
        renderer.process_inputs()

        imgui.new_frame()

        with imgui.begin_main_menu_bar() as main_menu_bar:
            if main_menu_bar.opened:
                with imgui.begin_menu('File', True) as file_menu:
                    if file_menu.opened:
                        imgui.menu_item('New', 'Ctrl+N', False, True)
                        imgui.menu_item('Open ...', 'Ctrl+O', False, True)
                        with imgui.begin_menu('Open Recent', True) as open_recent_menu:
                            if open_recent_menu.opened:
                                imgui.menu_item('doc.txt', None, False, True)

        imgui.begin("Example: item groups")

        imgui.begin_group()
        imgui.text("First group (buttons):")
        imgui.button("Button A")
        imgui.button("Button B")
        imgui.end_group()

        imgui.same_line(spacing=50)

        imgui.begin_group()
        imgui.text("Second group (text and bullet texts):")
        imgui.bullet_text("Bullet A")
        imgui.bullet_text("Bullet B")
        imgui.COLOR_EDIT_FLOAT = 16777216
        imgui.end_group()

        with imgui.begin("Open File", flags=flags):
            with imgui.begin_menu_bar() as menu_bar:
                if menu_bar.opened:
                    with imgui.begin_menu('File') as file_menu:
                        if file_menu.opened:
                            imgui.menu_item('Close')
                    draw_list = imgui.get_window_draw_list()
            imgui.arrow_button("Button", imgui.DIRECTION_RIGHT)
    
        style = imgui.get_style()
        imgui.columns(4)
        for color in range(0, imgui.COLOR_COUNT):
            imgui.text("Color: {}".format(color))
            imgui.color_button("color#{}".format(color), *style.colors[color])
            imgui.next_column()

        with imgui.begin("WHERE IS SOURCE"):
            imgui.button('source')
            if imgui.begin_drag_drop_source():
                imgui.set_drag_drop_payload('itemtype', b'payload')
                imgui.button('dragged source')
                imgui.end_drag_drop_source()

            imgui.button('dest')
            if imgui.begin_drag_drop_target():
                payload = imgui.accept_drag_drop_payload('itemtype')
                if payload is not None:
                    print('Received:', payload)
                imgui.end_drag_drop_target()

            imgui.button("Click me!")
            if imgui.is_item_hovered():
                with imgui.begin_tooltip():
                    imgui.text("This button is clickable.")
                    imgui.text("This button has full window tooltip.")
                    texture_id = imgui.get_io().fonts.texture_id
                    imgui.image(texture_id, 512, 64, border_color=(1, 0, 0, 1))
        
        with imgui.begin("Example: popup context view"):
            imgui.text("Right-click to set value.")
            with imgui.begin_popup_context_item("Item Context Menu", mouse_button=0) as popup:
                if popup.opened:
                    imgui.selectable("Set toก Zero")

        
     
        with imgui.begin("Example: popup context view"):
            draw_list = imgui.get_window_draw_list()
            draw_list.path_clear()
            draw_list.path_line_to(80, 80)
            draw_list.path_arc_to(80, 80, 30, 0.5, 5.5)
            draw_list.path_stroke(imgui.get_color_u32_rgba(1,1,0,1),
                flags=imgui.DRAW_CLOSED, thickness=10)

            draw_list.path_clear()
            draw_list.path_line_to(240, 80)
            draw_list.path_arc_to(240, 80, 30, 0.5, 5.5)
            draw_list.path_stroke(imgui.get_color_u32_rgba(1,1,0,1),
                flags=imgui.DRAW_NONE, thickness=10)

            draw_list.add_rect(20, 135, 60, 190,
                imgui.get_color_u32_rgba(1,1,0,1), rounding=5,
                flags=imgui.DRAW_ROUND_CORNERS_ALL, thickness=10)
            draw_list.add_rect(100, 135, 140, 190,
                imgui.get_color_u32_rgba(1,1,0,1), rounding=5,
                flags=imgui.DRAW_ROUND_CORNERS_NONE, thickness=10)
            draw_list.add_rect(180, 135, 220, 190,
                imgui.get_color_u32_rgba(1,1,0,1), rounding=5,
                flags=imgui.DRAW_ROUND_CORNERS_LEFT, thickness=10)
            draw_list.add_rect(260, 135, 300, 190,
                imgui.get_color_u32_rgba(1,1,0,1), rounding=5,
                flags=imgui.DRAW_ROUND_CORNERS_BOTTOM_RIGHT, thickness=10)
        

                
        imgui.end()

        gl.glClearColor(0, 0, 0, 1)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)

        imgui.render()
        renderer.render(imgui.get_draw_data())
    
        pygame.display.flip()

    renderer.shutdown()
    pygame.quit()

if __name__ == "__main__":
    main()
