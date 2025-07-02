import pygame
import os
import random

# --- Constantes Globales para la Clase Character ---
MK9_MAX_HEALTH = 1000
DEFAULT_SPECIAL_BAR_MAX = 3 # 3 niveles para X-Ray

# Estados del personaje
STANCE_IDLE = "idle"; STANCE_WALKING_FORWARD = "walking_forward"; STANCE_WALKING_BACKWARD = "walking_backward"
STANCE_JUMPING = "jumping"; STANCE_CROUCHING = "crouching"; STANCE_ATTACKING = "attacking"
STANCE_ATTACKING_SPECIAL = "attacking_special"; STANCE_GETTING_HIT = "getting_hit"
STANCE_BLOCKING = "blocking"; STANCE_DIZZY = "dizzy"; STANCE_DEAD = "dead"
STANCE_XRAY_ACTIVE = "xray_active" # Estado durante la ejecución del X-Ray

# Física del Salto
JUMP_INITIAL_Y_VELOCITY = 22.0  
GRAVITY_ACCELERATION = -65.0 

# Tipos de Ataque Normal
ATTACK_TYPE_HIGH_PUNCH = "high_punch"; ATTACK_TYPE_MEDIUM_PUNCH = "medium_punch"; ATTACK_TYPE_LOW_PUNCH = "low_punch"
ATTACK_TYPE_HIGH_KICK = "high_kick"; ATTACK_TYPE_MEDIUM_KICK = "medium_kick"; ATTACK_TYPE_LOW_KICK = "low_kick"

class Character:
    def __init__(self, name, player_num, is_player_one, character_sound_path_prefix, global_sound_player_func):
        self.name = name; self.player_num = player_num; self.is_player_one = is_player_one
        self.global_play_sound = global_sound_player_func
        self.health = MK9_MAX_HEALTH; self.max_health = MK9_MAX_HEALTH
        self.special_bar = 0; self.special_bar_max = DEFAULT_SPECIAL_BAR_MAX
        self.x = -75.0 if is_player_one else 75.0; self.y = 0.0
        self.facing_right = is_player_one; self.state = STANCE_IDLE
        self.y_velocity = 0.0; self.is_grounded = True
        self.current_attack_type = None; self.attack_timer = 0.0; self.attack_damage = 0
        self.attack_hitbox = None; self.attack_already_hit_opponent = False
        self.sounds = {}; self.character_sound_path_prefix = character_sound_path_prefix
        self.special_moves = {}
        self._load_character_sounds() 
        self._define_normal_attacks()
        self._define_special_moves_and_xray() # Renombrado para incluir X-Ray

    def _define_normal_attacks(self):
        self.attack_definitions = {
            ATTACK_TYPE_MEDIUM_PUNCH: {"dmg": 50, "hbx_rx": 15, "hbx_ry": 45, "hbx_w": 25, "hbx_h": 15, "dur_ms": 300, "snd_c": "grunt_attack_1", "snd_f": "foley_woosh_medium_01"},
            ATTACK_TYPE_HIGH_PUNCH:   {"dmg": 60, "hbx_rx": 18, "hbx_ry": 65, "hbx_w": 25, "hbx_h": 15, "dur_ms": 350, "snd_c": "grunt_attack_2", "snd_f": "foley_woosh_strong_01"},
            ATTACK_TYPE_LOW_PUNCH:    {"dmg": 40, "hbx_rx": 12, "hbx_ry": 15, "hbx_w": 20, "hbx_h": 12, "dur_ms": 250, "snd_c": "grunt_attack_low", "snd_f": "foley_woosh_fast_01"},
            ATTACK_TYPE_MEDIUM_KICK:  {"dmg": 70, "hbx_rx": 20, "hbx_ry": 35, "hbx_w": 30, "hbx_h": 18, "dur_ms": 400, "snd_c": "grunt_kick_1", "snd_f": "foley_woosh_medium_02"},
            ATTACK_TYPE_HIGH_KICK:    {"dmg": 80, "hbx_rx": 22, "hbx_ry": 70, "hbx_w": 30, "hbx_h": 18, "dur_ms": 450, "snd_c": "grunt_kick_2", "snd_f": "foley_woosh_strong_02"},
            ATTACK_TYPE_LOW_KICK:     {"dmg": 60, "hbx_rx": 25, "hbx_ry": 10, "hbx_w": 35, "hbx_h": 15, "dur_ms": 380, "snd_c": "grunt_kick_low", "snd_f": "foley_woosh_fast_02"},
        }
        self.impact_sound_keys = { "light": "foley_hit_body_sm_01", "medium": "foley_hit_body_md_01", "heavy": "foley_hit_body_lg_01" }

    def _define_special_moves_and_xray(self):
        # Poderes Especiales (ejemplos)
        if self.name == "Kung Lao":
            self.special_moves["hat_throw"] = { "display_name": "Hat Throw", "sound_key": "hat_throw", "input_action": "SPECIAL_1", "damage": 80,
                "is_projectile": True, "projectile_speed": 280.0, "projectile_sound_travel": "hat_doppler", "projectile_sound_impact": "hat_impact01",
                "duration_ms": 600, "special_cost": 0, "foley_sound": None  }
            self.special_moves["spin"] = { "display_name": "Spin", "sound_key": "spin", "input_action": "SPECIAL_2", "damage": 70,
                "is_projectile": False, "duration_ms": 800, "special_cost": 0, "foley_sound": "spin_whoosh", 
                "hitbox_area": {"type": "area", "rx":0, "ry":35, "w":70, "h":70} } # Hitbox para el spin
        elif self.name == "Liu Kang":
            self.special_moves["fireball"] = { "display_name": "Fireball", "sound_key": "fire_shot01", "input_action": "SPECIAL_1", "damage": 75,
                "is_projectile": True, "projectile_speed": 320.0, "projectile_sound_travel": None, "projectile_sound_impact": "fire_impact01",
                "duration_ms": 500, "special_cost": 0, "foley_sound": "hand_fire01" }
            self.special_moves["bicycle_kick"] = { "display_name": "Bicycle Kick", "sound_key": "bicycle_kick01", "input_action": "SPECIAL_2", "damage": 90,
                "is_projectile": False, "duration_ms": 1000, "special_cost": 0, "foley_sound": None, "moves_character": True } # Indica que el personaje se mueve

        # Definición del X-Ray (común o específico del personaje)
        self.special_moves["xray_attack"] = {
            "display_name": f"{self.name} X-Ray", "sound_key": "xray_activation_vo", # ej. KungLao_XRay_VO.wav
            "input_action": "XRAY_ACTIVATE", "damage": 300, "duration_ms": 4000, "special_cost": self.special_bar_max,
            "is_projectile": False, "hitbox_area": {"type": "area", "rx":0, "ry":40, "w":50, "h":80}, # Hitbox para iniciar el XRay
            "sfx_start_key": "fight_xray_start", # Sonido global de inicio de secuencia XRay
            "sfx_hit_sequence_keys": ["fight_xray_hit01", "fight_bone_snap_01", "fight_xray_hit02", "fight_bone_break_01"], # Sonidos globales
        }
        if self.special_moves: print(f"Poderes/XRay definidos para {self.name}: {list(self.special_moves.keys())}")

    def _load_character_sounds(self):
        char_folder_name_original=self.name; char_folder_name_no_space=self.name.replace(" ","")
        possible_char_dirs=[os.path.join(self.character_sound_path_prefix,char_folder_name_original), os.path.join(self.character_sound_path_prefix,char_folder_name_no_space)]
        char_sounds_dir=None
        for path_option in possible_char_dirs:
            if os.path.isdir(path_option):char_sounds_dir=path_option;break
        if not char_sounds_dir:print(f"Adv:Dir sonidos no para {self.name} en {possible_char_dirs}");return
        print(f"Cargando sonidos para {self.name} desde {char_sounds_dir}...")
        count=0
        for filename in os.listdir(char_sounds_dir):
            if filename.lower().endswith((".wav",".ogg",".mp3")):
                sound_path=os.path.join(char_sounds_dir,filename);sound_object=pygame.mixer.Sound(sound_path)
                base_name=os.path.splitext(filename)[0];key_name=base_name
                if key_name.lower().startswith("sfx_"):key_name=key_name[4:]
                char_name_ns_l=self.name.replace(" ","").lower()+"_";char_fn_l=self.name.split(" ")[0].lower()+"_"
                if not key_name.lower().startswith("fol_"):
                    if key_name.lower().startswith(char_name_ns_l):key_name=key_name[len(char_name_ns_l):]
                    elif key_name.lower().startswith(char_fn_l):key_name=key_name[len(char_fn_l):]
                self.sounds[key_name.lower()]=sound_object;count+=1
        print(f"Cargados {count} sonidos para {self.name}. Claves ej: {list(self.sounds.keys())[:5]}")

    def play_char_sound(self,sound_key,loops=0,pan_override=None,use_global_sfx=False, sfx_dict_global=None):
        if not sound_key: return
        sound_key_lower=sound_key.lower(); sound_object=None
        if not use_global_sfx: sound_object=self.sounds.get(sound_key_lower)
        elif sfx_dict_global: sound_object=sfx_dict_global.get(sound_key_lower)
        
        if sound_object:
            scene_width_half=100.0;t=(self.x+scene_width_half)/(2*scene_width_half);t=max(0.0,min(1.0,t))
            left_pan,right_pan=(1.0-t),t;min_pan_volume=0.05
            if t<0.01:right_pan=min_pan_volume;left_pan=1.0
            elif t>0.99:left_pan=min_pan_volume;right_pan=1.0
            if pan_override:left_pan,right_pan=pan_override
            self.global_play_sound(sound_object,loops=loops,pan_left=left_pan,pan_right=right_pan)

    def gain_special_meter(self, amount):
        if self.state == STANCE_DEAD or self.special_bar == self.special_bar_max : return
        self.special_bar += amount
        if self.special_bar >= self.special_bar_max:
            self.special_bar = self.special_bar_max
            print(f"¡{self.name} X-RAY LISTO!")
            self.play_char_sound("xray_ready_vo") # Sonido VO si existe
            # O un sonido global: self.play_char_sound("fight_xray_meter_full", use_global_sfx=True, sfx_dict_global=THE_GLOBAL_SFX_DICT_REF)
        elif self.special_bar < 0: self.special_bar = 0
        # print(f"{self.name} barra: {self.special_bar}/{self.special_bar_max}")


    def update_physics(self, dt):
        if not self.is_grounded:
            self.y_velocity+=GRAVITY_ACCELERATION*dt;self.y+=self.y_velocity*dt
            if self.y<=0:self.y=0;self.y_velocity=0;self.is_grounded=True
            if self.state==STANCE_JUMPING:self.set_state_idle();self.play_char_sound("land")
        else:self.y=0;self.y_velocity=0

    def update_attack_state(self, dt):
        if self.state in [STANCE_ATTACKING, STANCE_ATTACKING_SPECIAL, STANCE_XRAY_ACTIVE]:
            self.attack_timer -= dt
            if self.attack_timer <= 0:
                # Si era X-Ray, reproducir sonido de fin de secuencia X-Ray
                if self.state == STANCE_XRAY_ACTIVE and self.current_attack_type == "xray_attack":
                    xray_data = self.special_moves.get("xray_attack", {})
                    # self.play_char_sound(xray_data.get("sfx_end_key"), use_global_sfx=True, sfx_dict_global=...)
                    print(f"{self.name} terminó X-Ray.")

                self.current_attack_type=None;self.attack_timer=0;self.attack_already_hit_opponent=False
                self.set_state_idle()

    def set_state_idle(self):
        if self.state==STANCE_CROUCHING and not self.is_grounded:self.state=STANCE_JUMPING;return
        if self.state==STANCE_CROUCHING and self.is_grounded:return
        if self.state not in [STANCE_ATTACKING,STANCE_ATTACKING_SPECIAL,STANCE_XRAY_ACTIVE,STANCE_GETTING_HIT,STANCE_DEAD,STANCE_BLOCKING]:
            self.state=STANCE_IDLE

    def move(self,direction,scenario_limits,speed_value): # speed_value es speed*dt
        if self.state not in [STANCE_IDLE,STANCE_WALKING_FORWARD,STANCE_WALKING_BACKWARD,STANCE_CROUCHING,STANCE_JUMPING]:return
        actual_move_val=speed_value
        if self.state==STANCE_JUMPING:actual_move_val*=0.7
        is_fwd=(self.facing_right and direction>0)or(not self.facing_right and direction<0)
        if self.is_grounded:
            if self.state==STANCE_CROUCHING:self.state=STANCE_IDLE
            if self.state in [STANCE_IDLE,STANCE_WALKING_FORWARD,STANCE_WALKING_BACKWARD]:
                self.state=STANCE_WALKING_FORWARD if is_fwd else STANCE_WALKING_BACKWARD
        new_x=self.x+(direction*actual_move_val);self.x=max(scenario_limits[0],min(scenario_limits[1],new_x))

    def jump(self):
        if self.is_grounded and self.state not in [STANCE_JUMPING,STANCE_ATTACKING,STANCE_ATTACKING_SPECIAL,STANCE_XRAY_ACTIVE,STANCE_GETTING_HIT,STANCE_CROUCHING]:
            self.state=STANCE_JUMPING;self.is_grounded=False;self.y_velocity=JUMP_INITIAL_Y_VELOCITY
            self.play_char_sound("jump")

    def crouch(self,is_crouching):
        if not self.is_grounded:return
        if is_crouching:
            if self.state not in [STANCE_CROUCHING,STANCE_JUMPING,STANCE_ATTACKING,STANCE_ATTACKING_SPECIAL,STANCE_XRAY_ACTIVE,STANCE_GETTING_HIT]:
                self.state=STANCE_CROUCHING
        elif self.state==STANCE_CROUCHING:self.state=STANCE_IDLE
    
    def stop_walking(self):
        if self.state in [STANCE_WALKING_FORWARD,STANCE_WALKING_BACKWARD]:self.state=STANCE_IDLE

    def idle_action(self):
        if self.is_grounded and self.state not in [STANCE_ATTACKING,STANCE_ATTACKING_SPECIAL,STANCE_XRAY_ACTIVE,STANCE_GETTING_HIT,STANCE_DEAD,STANCE_BLOCKING,STANCE_CROUCHING]:
            self.state=STANCE_IDLE

    def update_facing_direction(self,opponent_x):
        if self.x<opponent_x:self.facing_right=True
        elif self.x>opponent_x:self.facing_right=False

    def attempt_attack(self,attack_key_input):
        if self.state not in [STANCE_IDLE,STANCE_WALKING_FORWARD,STANCE_WALKING_BACKWARD,STANCE_CROUCHING,STANCE_JUMPING] or self.attack_timer>0:return False
        actual_atk_type=attack_key_input
        if self.state==STANCE_CROUCHING:
            if attack_key_input==ATTACK_TYPE_MEDIUM_PUNCH:actual_atk_type=ATTACK_TYPE_LOW_PUNCH
            elif attack_key_input==ATTACK_TYPE_HIGH_PUNCH:actual_atk_type=ATTACK_TYPE_LOW_PUNCH
            elif attack_key_input==ATTACK_TYPE_MEDIUM_KICK:actual_atk_type=ATTACK_TYPE_LOW_KICK
            elif attack_key_input==ATTACK_TYPE_HIGH_KICK:actual_atk_type=ATTACK_TYPE_LOW_KICK
        if actual_atk_type in self.attack_definitions:
            atk_data=self.attack_definitions[actual_atk_type]
            self.state=STANCE_ATTACKING;self.current_attack_type=actual_atk_type
            self.attack_timer=atk_data["dur_ms"]/1000.0;self.attack_damage=atk_data["dmg"];self.attack_already_hit_opponent=False
            hbx_cxo=atk_data["hbx_rx"] if self.facing_right else -atk_data["hbx_rx"]
            hbx_ax=self.x+hbx_cxo;hbx_ay=self.y+atk_data["hbx_ry"]
            self.attack_hitbox={"x":hbx_ax-atk_data["hbx_w"]/2,"y":hbx_ay-atk_data["hbx_h"]/2,"width":atk_data["hbx_w"],"height":atk_data["hbx_h"]}
            self.play_char_sound(atk_data.get("snd_c"));self.play_char_sound(atk_data.get("snd_f"),pan_override=(0.6,0.6))
            return True
        return False

    def attempt_special_move(self,input_action_key,all_projectiles_list, global_sfx_ref): # Pass GLOBAL_SFX
        if self.state in [STANCE_DEAD,STANCE_GETTING_HIT,STANCE_ATTACKING,STANCE_ATTACKING_SPECIAL,STANCE_XRAY_ACTIVE] or self.attack_timer>0:return False
        power_to_exec=None;power_name=None
        for name,details in self.special_moves.items():
            if details.get("input_action")==input_action_key:power_to_exec=details;power_name=name;break
        if not power_to_exec:return False
        
        self.state=STANCE_ATTACKING_SPECIAL;self.current_attack_type=power_name
        self.attack_timer=power_to_exec["duration_ms"]/1000.0; self.attack_damage=power_to_exec["damage"]
        self.attack_already_hit_opponent=False
        print(f"{self.name} usa PODER: {power_to_exec.get('display_name',power_name)}!")
        self.play_char_sound(power_to_exec["sound_key"])
        if power_to_exec.get("foley_sound"):self.play_char_sound(power_to_exec["foley_sound"],pan_override=(0.6,0.6))
        
        if power_to_exec.get("is_projectile",False):
            proj_x=self.x+(20 if self.facing_right else -20);proj_y=self.y+(15 if self.state==STANCE_CROUCHING else 40)
            new_proj=Projectile(proj_x,proj_y,power_to_exec["projectile_speed"],self.facing_right,self,power_to_exec["damage"],
                                power_to_exec.get("projectile_sound_travel"),power_to_exec.get("projectile_sound_impact"),
                                self.sounds,self.global_play_sound, global_sfx_ref) # Pass global_sfx_ref
            all_projectiles_list.append(new_proj);self.attack_damage=0
        elif power_to_exec.get("hitbox_area"): # Para especiales no proyectil con hitbox definida
            hb_data = power_to_exec["hitbox_area"]
            hbx_cxo = hb_data["rx"] if self.facing_right else -hb_data["rx"] # rx relativo al personaje
            hbx_ax = self.x + hbx_cxo; hbx_ay = self.y + hb_data["ry"]
            self.attack_hitbox = {"x":hbx_ax-hb_data["w"]/2, "y":hbx_ay-hb_data["h"]/2, "width":hb_data["w"], "height":hb_data["h"]}
        return True

    def attempt_xray_move(self, global_sfx_ref): # Pass GLOBAL_SFX
        if self.state in [STANCE_DEAD,STANCE_GETTING_HIT,STANCE_ATTACKING,STANCE_ATTACKING_SPECIAL,STANCE_XRAY_ACTIVE] or self.attack_timer>0:return False
        if self.special_bar<self.special_bar_max:print(f"{self.name} XRay sin barra ({self.special_bar}/{self.special_bar_max})");return False
        
        xray_data=self.special_moves.get("xray_attack")
        if not xray_data:print(f"Adv: {self.name} no tiene def de XRay.");return False
        
        print(f"¡¡¡{self.name} activa X-RAY!!!"); self.state=STANCE_XRAY_ACTIVE
        self.current_attack_type="xray_attack"; self.attack_timer=xray_data["duration_ms"]/1000.0
        self.attack_damage=xray_data["damage"]; self.attack_already_hit_opponent=False
        
        self.play_char_sound(xray_data.get("sound_key")) # VO del personaje
        self.play_char_sound(xray_data.get("sfx_start_key"), use_global_sfx=True, sfx_dict_global=global_sfx_ref) # Sonido global
        
        hb_data = xray_data.get("hitbox_area") # Hitbox para iniciar el XRay
        if hb_data:
            hbx_cxo = hb_data["rx"] if self.facing_right else -hb_data["rx"]
            hbx_ax = self.x + hbx_cxo; hbx_ay = self.y + hb_data["ry"]
            self.attack_hitbox = {"x":hbx_ax-hb_data["w"]/2, "y":hbx_ay-hb_data["h"]/2, "width":hb_data["w"], "height":hb_data["h"]}
        
        self.special_bar=0; print(f"{self.name} usó X-Ray. Barra reseteada.")
        return True

    def check_attack_collision(self,opponent, global_sfx_ref=None): # Pass GLOBAL_SFX for XRay hits
        if not self.current_attack_type or not opponent or self.attack_already_hit_opponent or not self.attack_hitbox:
            is_non_proj_special_without_hitbox = self.state == STANCE_ATTACKING_SPECIAL and \
                                              not self.special_moves.get(self.current_attack_type,{}).get("is_projectile") and \
                                              not self.attack_hitbox
            if not is_non_proj_special_without_hitbox : return False # Solo permitir continuar si es un especial no-proy sin hitbox definida explícitamente aún

        if not self.attack_hitbox: return False # Si realmente no hay hitbox, no colisiona
            
        atk_rect_x1=self.attack_hitbox["x"];atk_rect_y1=self.attack_hitbox["y"]
        atk_rect_x2=self.attack_hitbox["x"]+self.attack_hitbox["width"];atk_rect_y2=self.attack_hitbox["y"]+self.attack_hitbox["height"]
        opp_hurt_w=20.0;opp_h_std=70.0;opp_h_crch=40.0;opp_h_jmp=60.0
        opp_hurt_x1=opponent.x-opp_hurt_w/2;opp_hurt_x2=opponent.x+opp_hurt_w/2
        opp_curr_h=opp_h_std
        if opponent.state==STANCE_CROUCHING:opp_curr_h=opp_h_crch
        elif opponent.state==STANCE_JUMPING:opp_curr_h=opp_h_jmp
        opp_hurt_y1=opponent.y;opp_hurt_y2=opponent.y+opp_curr_h
        x_overlap=(atk_rect_x1<opp_hurt_x2 and atk_rect_x2>opp_hurt_x1)
        y_overlap=(atk_rect_y1<opp_hurt_y2 and atk_rect_y2>opp_hurt_y1)

        if x_overlap and y_overlap:
            print(f"¡COLISIÓN! {self.name}'s {self.current_attack_type} golpea a {opponent.name}")
            self.gain_special_meter(10+int(self.attack_damage/10)) # Atacante gana barra
            opponent.take_damage(self.attack_damage,self.current_attack_type,self.facing_right)
            self.attack_already_hit_opponent=True
            
            if self.current_attack_type == "xray_attack": # Si es un X-Ray, reproducir secuencia de sonidos
                print(f"¡¡¡X-RAY CONECTADO!!! {self.name} a {opponent.name}")
                xray_data = self.special_moves.get("xray_attack", {})
                for hit_sound_key in xray_data.get("sfx_hit_sequence_keys", []):
                    self.play_char_sound(hit_sound_key, use_global_sfx=True, sfx_dict_global=global_sfx_ref)
            else: # Impacto normal
                imp_snd_key=self.impact_sound_keys.get("medium")
                if self.attack_damage>70:imp_snd_key=self.impact_sound_keys.get("heavy")
                elif self.attack_damage<50:imp_snd_key=self.impact_sound_keys.get("light")
                self.play_char_sound(imp_snd_key, use_global_sfx=True, sfx_dict_global=global_sfx_ref) # Usar global SFX para impactos
            return True
        return False

    def take_damage(self,amount,attack_type_received=None,attacker_facing_right=True):
        is_blocking=False # TODO: Implementar lógica de bloqueo real
        if self.state==STANCE_BLOCKING:is_blocking=True # Simplificado
        
        if is_blocking:
            print(f"{self.name} bloqueó {attack_type_received}! Daño reducido.");amount*=0.2
            self.play_char_sound("block_hit"); self.gain_special_meter(5+int(amount/20))
        else:
            self.play_char_sound("grunt_hit"); self.gain_special_meter(15+int(amount/10))
            
        self.health-=int(amount)
        if self.health<0:self.health=0
        if self.health>0 and not is_blocking:self.state=STANCE_GETTING_HIT;self.y_velocity=0
        elif self.health==0:self.state=STANCE_DEAD;print(f"{self.name} derrotado.");self.play_char_sound("death_scream")

    def get_info(self):
        return (f"{self.name} (HP:{self.health}, SP:{self.special_bar}, X:{self.x:.1f},Y:{self.y:.1f},YVel:{self.y_velocity:.1f}, "
                f"Grounded:{self.is_grounded}, St:{self.state}, FaceR:{self.facing_right}, AtkTim:{self.attack_timer:.2f})")

# --- Clase Projectile ---
PROJECTILE_WIDTH=15;PROJECTILE_HEIGHT=10;PROJECTILE_LIFESPAN=2.5
class Projectile:
    def __init__(self,x,y,speed,facing_right,owner,damage,snd_travel,snd_impact,char_sounds,global_play_func, global_sfx_ref):
        self.x=x;self.y=y;self.speed=speed;self.facing_right=facing_right;self.owner=owner;self.damage=damage
        self.sound_travel_key=snd_travel;self.sound_impact_key=snd_impact
        self.character_sounds=char_sounds;self.global_play_sound=global_play_func; self.global_sfx = global_sfx_ref
        self.width=PROJECTILE_WIDTH;self.height=PROJECTILE_HEIGHT;self.active=True;self.lifespan=PROJECTILE_LIFESPAN
        self._play_sound_proj(self.sound_travel_key) # Reproducir sonido de viaje al crear

    def _play_sound_proj(self,sound_key,loops=0,pan_override=None,use_global_sfx=False): # Proyectil puede usar global SFX
        if not sound_key:return
        sound_key_lower=sound_key.lower();sound_object=None
        if not use_global_sfx:sound_object=self.character_sounds.get(sound_key_lower) # Sonidos del dueño
        elif self.global_sfx:sound_object=self.global_sfx.get(sound_key_lower) # Sonidos globales
        
        if sound_object:
            scene_width_half=100.0;t=(self.x+scene_width_half)/(2*scene_width_half);t=max(0.0,min(1.0,t))
            left_pan,right_pan=(1.0-t),t;min_pan_volume=0.05
            if t<0.01:right_pan=min_pan_volume;left_pan=1.0
            elif t>0.99:left_pan=min_pan_volume;right_pan=1.0
            if pan_override:left_pan,right_pan=pan_override
            self.global_play_sound(sound_object,loops=loops,pan_left=left_pan,pan_right=right_pan)

    def update(self,dt,scenario_limits):
        if not self.active:return
        move_amount=self.speed*dt
        self.x+=move_amount if self.facing_right else -move_amount;self.lifespan-=dt
        if self.lifespan<=0 or self.x<scenario_limits[0]-self.width*2 or self.x>scenario_limits[1]+self.width*2:self.active=False

    def check_collision(self,target_character):
        if not self.active or target_character.state==STANCE_DEAD or target_character==self.owner:return False
        tgt_hurt_w=20.0;tgt_h_std=70.0;tgt_h_crch=40.0;tgt_h_jmp=60.0
        tgt_hurt_x1=target_character.x-tgt_hurt_w/2;tgt_hurt_x2=target_character.x+tgt_hurt_w/2
        tgt_curr_h=tgt_h_std
        if target_character.state==STANCE_CROUCHING:tgt_curr_h=tgt_h_crch
        elif target_character.state==STANCE_JUMPING:tgt_curr_h=tgt_h_jmp
        tgt_hurt_y1=target_character.y;tgt_hurt_y2=target_character.y+tgt_curr_h
        proj_x1=self.x-self.width/2;proj_x2=self.x+self.width/2
        proj_y1=self.y-self.height/2;proj_y2=self.y+self.height/2
        x_overlap=(proj_x1<tgt_hurt_x2 and proj_x2>tgt_hurt_x1)
        y_overlap=(proj_y1<tgt_hurt_y2 and proj_y2>tgt_hurt_y1)
        if x_overlap and y_overlap:
            print(f"PROYECTIL IMPACTA! De {self.owner.name} a {target_character.name}")
            self.owner.gain_special_meter(10+int(self.damage/10)) # Dueño gana barra
            target_character.take_damage(self.damage,f"projectile_{self.owner.name}",self.owner.facing_right)
            self._play_sound_proj(self.sound_impact_key, use_global_sfx=True) # Impacto de proyectil usa global sfx
            self.active=False;return True
        return False

if __name__=='__main__':pygame.init();pygame.mixer.init();pygame.quit()
