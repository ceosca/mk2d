import pygame
import os

# --- Constantes ---
SOUND_VOLUME = 0.7; SCREEN_WIDTH = 320; SCREEN_HEIGHT = 240; FPS = 60

# --- Constantes del Juego ---
SCENARIO_LIMIT_LEFT = -100.0; SCENARIO_LIMIT_RIGHT = 100.0; BASE_MOVEMENT_SPEED = 100.0 

from character import (Character, Projectile, STANCE_IDLE, STANCE_JUMPING, STANCE_ATTACKING, 
                       STANCE_ATTACKING_SPECIAL, STANCE_GETTING_HIT, STANCE_DEAD, STANCE_CROUCHING, STANCE_XRAY_ACTIVE,
                       ATTACK_TYPE_MEDIUM_PUNCH, ATTACK_TYPE_HIGH_PUNCH, ATTACK_TYPE_LOW_PUNCH,
                       ATTACK_TYPE_MEDIUM_KICK, ATTACK_TYPE_HIGH_KICK, ATTACK_TYPE_LOW_KICK)

# --- Definición de Controles ---
PLAYER_1_CONTROLS = {
    "LEFT": pygame.K_a, "RIGHT": pygame.K_d, "JUMP": pygame.K_w, "CROUCH": pygame.K_s,
    "MEDIUM_PUNCH": pygame.K_t, "HIGH_PUNCH": pygame.K_u, "MEDIUM_KICK": pygame.K_g, "HIGH_KICK": pygame.K_j,
    "SPECIAL_1": pygame.K_r, "SPECIAL_2": pygame.K_f, "XRAY_ACTIVATE": pygame.K_x,
}
PLAYER_2_CONTROLS = {
    "LEFT": pygame.K_LEFT, "RIGHT": pygame.K_RIGHT, "JUMP": pygame.K_UP, "CROUCH": pygame.K_DOWN,
    "MEDIUM_PUNCH": pygame.K_KP_4, "HIGH_PUNCH": pygame.K_KP_5, "MEDIUM_KICK": pygame.K_KP_1, "HIGH_KICK": pygame.K_KP_2,
    "SPECIAL_1": pygame.K_KP_7, "SPECIAL_2": pygame.K_KP_8, "XRAY_ACTIVATE": pygame.K_KP_ENTER,
}
INPUT_ACTION_TO_ATTACK_TYPE = { "MEDIUM_PUNCH": ATTACK_TYPE_MEDIUM_PUNCH, "HIGH_PUNCH": ATTACK_TYPE_HIGH_PUNCH,
                                "MEDIUM_KICK": ATTACK_TYPE_MEDIUM_KICK, "HIGH_KICK": ATTACK_TYPE_HIGH_KICK,}
INPUT_ACTION_TO_SPECIAL_ACTION_KEY = { "SPECIAL_1": "SPECIAL_1", "SPECIAL_2": "SPECIAL_2",}
# XRAY_ACTIVATE no necesita mapeo aquí, se llama directamente a attempt_xray_move.

pygame.mixer.pre_init(44100,-16,2,1024); pygame.init(); pygame.mixer.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT)); pygame.display.set_caption("Mortal Kombat Audio")

GLOBAL_SFX = {}
SOUNDS_BASE_PATH="sounds"; CHARS_SOUND_PATH=os.path.join(SOUNDS_BASE_PATH,"chars")
SFX_SOUND_PATH=os.path.join(SOUNDS_BASE_PATH,"sfx"); SFX_FIGHT_PATH=os.path.join(SFX_SOUND_PATH,"Fight")
SFX_FOLEY_PATH=os.path.join(SFX_SOUND_PATH,"Foley")

def load_sound(path,volume=SOUND_VOLUME):
    if not os.path.exists(path):return None
    try: sound=pygame.mixer.Sound(path);sound.set_volume(volume);return sound
    except pygame.error as e:print(f"Err cargando {path}:{e}");return None

def global_play_sound_handler(sound_object,loops=0,pan_left=0.5,pan_right=0.5):
    if sound_object:
        channel=sound_object.play(loops=loops)
        if channel:channel.set_volume(pan_left*SOUND_VOLUME,pan_right*SOUND_VOLUME)
        return channel
    return None

def load_sfx_from_folder(folder_path,sfx_dict_target,prefix=""):
    if not os.path.isdir(folder_path):print(f"Adv: SFX Dir no: {folder_path}");return
    for filename in os.listdir(folder_path):
        if filename.lower().endswith((".wav",".ogg",".mp3")):
            sound_path=os.path.join(folder_path,filename);sound_object=load_sound(sound_path)
            if sound_object:
                base_name=os.path.splitext(filename)[0].lower()
                key=f"{prefix}{base_name}" if prefix else base_name
                if key not in sfx_dict_target:sfx_dict_target[key]=sound_object

def game_loop():
    running=True;clock=pygame.time.Clock();game_over_state=False
    game_over_display_time=3.0;round_over_sound_played=False;all_projectiles=[]
    print("\n--- Cargando SFX Generales ---")
    GLOBAL_SFX.clear();load_sfx_from_folder(SFX_FIGHT_PATH,GLOBAL_SFX,prefix="fight_")
    load_sfx_from_folder(SFX_FOLEY_PATH,GLOBAL_SFX,prefix="foley_")
    print(f"Total SFX generales: {len(GLOBAL_SFX)}")

    print("\n--- Selección de Personajes ---")
    if not os.path.isdir(CHARS_SOUND_PATH):print(f"Err:Dir chars'{CHARS_SOUND_PATH}'no existe.");pygame.quit();return
    available_char_names=[d for d in os.listdir(CHARS_SOUND_PATH) if os.path.isdir(os.path.join(CHARS_SOUND_PATH,d))]
    if not available_char_names:print(f"Err:No hay chars en'{CHARS_SOUND_PATH}'.");pygame.quit();return
    for i,name in enumerate(available_char_names):print(f"  {i+1}. {name}")
    selected_chars_names={"P1":None,"P2":None}
    for player_id_num in [1,2]:
        player_key=f"P{player_id_num}"
        while selected_chars_names[player_key] is None:
            try:
                choice_str=input(f"Jugador {player_id_num}(nombre o num):").strip()
                if not choice_str:continue;chosen_char_name=None
                try:
                    choice_num=int(choice_str)
                    if 1<=choice_num<=len(available_char_names):chosen_char_name=available_char_names[choice_num-1]
                    else:print("Num.fuera de rango.")
                except ValueError:
                    for char_name_in_list in available_char_names:
                        if char_name_in_list.lower().startswith(choice_str.lower()):chosen_char_name=char_name_in_list;break
                    if not chosen_char_name:print(f"'{choice_str}' no encontrado.")
                if chosen_char_name:
                    selected_chars_names[player_key]=chosen_char_name
                    cs_sound=GLOBAL_SFX.get("fight_confirm01");
                    if cs_sound:global_play_sound_handler(cs_sound,pan_left=0.6,pan_right=0.6)
                    print(f"P{player_id_num} seleccionó: {chosen_char_name}")
            except(EOFError,KeyboardInterrupt):print("\nSelección cancelada.");pygame.quit();return
    
    player1=Character(selected_chars_names["P1"],1,True,CHARS_SOUND_PATH,global_play_sound_handler)
    player2=Character(selected_chars_names["P2"],2,False,CHARS_SOUND_PATH,global_play_sound_handler)
    active_players=[player1,player2]
    fs_sound=GLOBAL_SFX.get("fight_fight")
    if fs_sound:global_play_sound_handler(fs_sound,pan_left=1.0,pan_right=1.0)
    else:print("Adv:Sonido'FIGHT'no hallado(clave'fight_fight').")
    print("\n--- Mortal Kombat Audio - ¡COMIENZA EL COMBATE! ---")

    while running:
        dt=clock.tick(FPS)/1000.0
        for event in pygame.event.get():
            if event.type==pygame.QUIT:running=False
            if event.type==pygame.KEYDOWN:
                if event.key==pygame.K_ESCAPE:running=False
                if not game_over_state:
                    # P1 Actions
                    if player1.state!=STANCE_DEAD:
                        if event.key==PLAYER_1_CONTROLS["JUMP"]:player1.jump()
                        elif event.key==PLAYER_1_CONTROLS.get("XRAY_ACTIVATE"): player1.attempt_xray_move(GLOBAL_SFX)
                        else:
                            for action_name,keycode in PLAYER_1_CONTROLS.items():
                                if event.key==keycode:
                                    if action_name in INPUT_ACTION_TO_ATTACK_TYPE:
                                        player1.attempt_attack(INPUT_ACTION_TO_ATTACK_TYPE[action_name]);break
                                    elif action_name in INPUT_ACTION_TO_SPECIAL_ACTION_KEY:
                                        player1.attempt_special_move(INPUT_ACTION_TO_SPECIAL_ACTION_KEY[action_name],all_projectiles,GLOBAL_SFX);break
                    # P2 Actions
                    if player2.state!=STANCE_DEAD:
                        if event.key==PLAYER_2_CONTROLS["JUMP"]:player2.jump()
                        elif event.key==PLAYER_2_CONTROLS.get("XRAY_ACTIVATE"): player2.attempt_xray_move(GLOBAL_SFX)
                        else:
                            for action_name,keycode in PLAYER_2_CONTROLS.items():
                                if event.key==keycode:
                                    if action_name in INPUT_ACTION_TO_ATTACK_TYPE:
                                        player2.attempt_attack(INPUT_ACTION_TO_ATTACK_TYPE[action_name]);break
                                    elif action_name in INPUT_ACTION_TO_SPECIAL_ACTION_KEY:
                                        player2.attempt_special_move(INPUT_ACTION_TO_SPECIAL_ACTION_KEY[action_name],all_projectiles,GLOBAL_SFX);break
        
        if game_over_state:
            game_over_display_time-=dt
            if game_over_display_time<=0:running=False
            pygame.display.flip();continue

        keys_pressed=pygame.key.get_pressed()
        current_move_speed=BASE_MOVEMENT_SPEED*dt

        if player1.state!=STANCE_DEAD: # P1 Movement & Crouch
            p1_moved_lr=False
            if keys_pressed[PLAYER_1_CONTROLS["LEFT"]]:player1.move(-1,(SCENARIO_LIMIT_LEFT,SCENARIO_LIMIT_RIGHT),current_move_speed);p1_moved_lr=True
            if keys_pressed[PLAYER_1_CONTROLS["RIGHT"]]:player1.move(1,(SCENARIO_LIMIT_LEFT,SCENARIO_LIMIT_RIGHT),current_move_speed);p1_moved_lr=True
            player1.crouch(keys_pressed[PLAYER_1_CONTROLS["CROUCH"]])
            if not p1_moved_lr and not keys_pressed[PLAYER_1_CONTROLS["CROUCH"]]:player1.stop_walking();player1.idle_action()

        if player2.state!=STANCE_DEAD: # P2 Movement & Crouch
            p2_moved_lr=False
            if keys_pressed[PLAYER_2_CONTROLS["LEFT"]]:player2.move(-1,(SCENARIO_LIMIT_LEFT,SCENARIO_LIMIT_RIGHT),current_move_speed);p2_moved_lr=True
            if keys_pressed[PLAYER_2_CONTROLS["RIGHT"]]:player2.move(1,(SCENARIO_LIMIT_LEFT,SCENARIO_LIMIT_RIGHT),current_move_speed);p2_moved_lr=True
            player2.crouch(keys_pressed[PLAYER_2_CONTROLS["CROUCH"]])
            if not p2_moved_lr and not keys_pressed[PLAYER_2_CONTROLS["CROUCH"]]:player2.stop_walking();player2.idle_action()

        # Game Updates
        for i,player in enumerate(active_players):
            if player.state==STANCE_DEAD:continue
            player.update_physics(dt);player.update_attack_state(dt)
            opponent=active_players[1-i]
            if opponent.state!=STANCE_DEAD:player.update_facing_direction(opponent.x)
            if player.state in [STANCE_ATTACKING,STANCE_ATTACKING_SPECIAL,STANCE_XRAY_ACTIVE] and \
               player.current_attack_type and not player.attack_already_hit_opponent:
                if opponent and opponent.state!=STANCE_DEAD:
                    # Pasar GLOBAL_SFX a check_attack_collision para los sonidos de impacto del X-Ray
                    player.check_attack_collision(opponent, GLOBAL_SFX if player.current_attack_type == "xray_attack" else None)
            if player.state==STANCE_GETTING_HIT:player.set_state_idle()
            if opponent.state==STANCE_DEAD and not game_over_state:
                game_over_state=True;print(f"\n!!! Jugador {player.player_num} GANA! !!!")
                ws_key=f"fight_player_{player.player_num}_wins";ws=GLOBAL_SFX.get(ws_key)
                if ws:global_play_sound_handler(ws,pan_left=1.0,pan_right=1.0)
                finish_sound=GLOBAL_SFX.get("fight_finish_him")
                if finish_sound and not round_over_sound_played:global_play_sound_handler(finish_sound,pan_left=1.0,pan_right=1.0)
                round_over_sound_played=True;break
        
        # Projectile Updates
        active_projectiles_this_frame=[]
        for proj in all_projectiles:
            proj.update(dt,(SCENARIO_LIMIT_LEFT,SCENARIO_LIMIT_RIGHT))
            if proj.active:
                target=player2 if proj.owner==player1 else player1
                if target and target.state!=STANCE_DEAD:
                    proj.check_collision(target) 
                if proj.active:active_projectiles_this_frame.append(proj)
        all_projectiles=active_projectiles_this_frame
        
        if game_over_state:pygame.display.flip();continue
        pygame.display.flip()
    print("\nJuego terminado.");pygame.quit()

if __name__=='__main__':
    required_paths={"sounds":SOUNDS_BASE_PATH,"chars":CHARS_SOUND_PATH,"sfx_fight":SFX_FIGHT_PATH,"sfx_foley":SFX_FOLEY_PATH}
    all_paths_found=True
    for key,path_val in required_paths.items():
        if not os.path.isdir(path_val):print(f"Error:Carpeta'{key}'no en:{path_val}");all_paths_found=False
    if not all_paths_found:print("Asegura estructura de carpetas correcta.")
    else:print("Estructura de carpetas de sonido OK.");game_loop()
