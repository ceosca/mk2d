import pygame
import os

# --- Constantes ---
SOUNDS_BASE_PATH = "sounds"
CHARS_PATH = os.path.join(SOUNDS_BASE_PATH, "chars")
SFX_PATH = os.path.join(SOUNDS_BASE_PATH, "sfx")
ANNOUNCER_PATH = os.path.join(SFX_PATH, "Announcer")
FIGHT_SFX_PATH = os.path.join(SFX_PATH, "Fight")
FOLEY_SFX_PATH = os.path.join(SFX_PATH, "Foley")

# --- Clases ---

class SoundManager:
    def __init__(self):
        # Mixer should be pre-initialized before this class is instantiated
        self.sounds = {} # Not currently used, consider removing
        self.char_sounds = {}
        self.sfx_sounds = {} # Stores all sfx, including categorized ones
        self._load_all_sounds()

    def _load_all_sounds(self):
        # Cargar sonidos de personajes
        if os.path.exists(CHARS_PATH):
            for char_name in os.listdir(CHARS_PATH):
                char_folder_path = os.path.join(CHARS_PATH, char_name)
                if os.path.isdir(char_folder_path):
                    self.char_sounds[char_name] = {}
                    for sound_file in os.listdir(char_folder_path):
                        if sound_file.endswith((".wav", ".mp3")):
                            sound_key = os.path.splitext(sound_file)[0]
                            try:
                                self.char_sounds[char_name][sound_key] = pygame.mixer.Sound(os.path.join(char_folder_path, sound_file))
                            except pygame.error as e:
                                print(f"Error loading char sound {os.path.join(char_folder_path, sound_file)}: {e}")

        sfx_categories = {
            "Announcer": ANNOUNCER_PATH,
            "Fight": FIGHT_SFX_PATH,
            "Foley": FOLEY_SFX_PATH
        }
        for category, path in sfx_categories.items():
            if os.path.exists(path):
                self.sfx_sounds[category] = {}
                for item_in_path in os.listdir(path):
                    item_full_path = os.path.join(path, item_in_path)
                    if item_in_path.endswith((".wav", ".mp3")):
                        sound_key = os.path.splitext(item_in_path)[0]
                        try:
                            self.sfx_sounds[category][sound_key] = pygame.mixer.Sound(item_full_path)
                        except pygame.error as e:
                            print(f"Error loading sound {item_full_path}: {e}")
                    elif os.path.isdir(item_full_path): # Handle subdirectories like Announcer/names
                        sub_category_name = item_in_path # e.g. "names"
                        self.sfx_sounds[category][sub_category_name] = {}
                        for sub_sound_file in os.listdir(item_full_path):
                            if sub_sound_file.endswith((".wav", ".mp3")):
                                sub_sound_key = os.path.splitext(sub_sound_file)[0]
                                try:
                                    self.sfx_sounds[category][sub_category_name][sub_sound_key] = pygame.mixer.Sound(os.path.join(item_full_path, sub_sound_file))
                                except pygame.error as e:
                                    print(f"Error loading sound {os.path.join(item_full_path, sub_sound_file)}: {e}")

    def play_sound(self, sound_obj, loops=0, volume_left=1.0, volume_right=1.0, channel_num=None):
        if sound_obj:
            channel_to_use = None
            if channel_num is not None:
                if 0 <= channel_num < pygame.mixer.get_num_channels():
                    channel_to_use = pygame.mixer.Channel(channel_num)

            if channel_to_use and not channel_to_use.get_busy():
                channel_to_use.play(sound_obj, loops=loops)
                current_channel = channel_to_use
            else:
                current_channel = sound_obj.play(loops=loops)

            if current_channel:
                current_channel.set_volume(volume_left, volume_right)
            return current_channel
        return None

    def get_char_sound(self, char_name, sound_key):
        return self.char_sounds.get(char_name, {}).get(sound_key)

    def get_sfx_sound(self, category, sound_key, sub_key=None):
        if sub_key:
            return self.sfx_sounds.get(category, {}).get(sound_key, {}).get(sub_key)
        return self.sfx_sounds.get(category, {}).get(sound_key)

class Player:
    def __init__(self, char_name, sound_manager, is_player1=True):
        self.char_name = char_name
        self.sound_manager = sound_manager
        self.health = 1000
        self.is_player1 = is_player1
        self.position = -10 if is_player1 else 10
        self.action_state = "idle"

        # Movement & Jumping state
        self.is_walking = False
        self.is_jumping = False
        self.is_crouching = False
        self.position_y = 0
        self.y_velocity = 0
        self.ground_level = 0
        self.jump_power = 20
        self.gravity = 2

        # Attack state
        self.is_attacking = False # True if player is currently in an attack animation/active frames
        self.current_attack_type = None # e.g., "front_punch", "crouch_kick"
        self.attack_frame_timer = 0 # Countdown for how long an attack is "active" or in recovery
        self.attack_cooldown = 0 # Cooldown before another attack can be initiated

        # Attack properties (to be defined per attack type)
        self.attack_properties = {
            "front_punch": {"reach": 3, "damage": 50, "height": "high", "startup": 5, "active": 3, "recovery": 7, "sound_whoosh": "sfx_liuk_fire_punch01", "sound_vocal": "vo_atk_grunt_01"}, # Example for Liu Kang
            "back_punch":  {"reach": 3.5, "damage": 60, "height": "high", "startup": 7, "active": 4, "recovery": 9, "sound_whoosh": "sfx_liuk_fire_punch02", "sound_vocal": "vo_atk_grunt_02"},
            "front_kick":  {"reach": 4, "damage": 70, "height": "mid", "startup": 8, "active": 4, "recovery": 10, "sound_whoosh": "sfx_liuk_flykick01", "sound_vocal": "vo_shout_short_01"}, # flykick might be too specific, generic kick whoosh better
            "back_kick":   {"reach": 4.5, "damage": 80, "height": "mid", "startup": 10, "active": 5, "recovery": 12, "sound_whoosh": "sfx_liuk_flykick_xt01", "sound_vocal": "vo_shout_long_01"},
            # Crouching attacks would be different: e.g. "crouch_front_punch"
            "crouch_front_punch": {"reach": 2.5, "damage": 40, "height": "low", "startup": 4, "active": 3, "recovery": 6, "sound_whoosh": "sfx_liuk_fire_punch01", "sound_vocal": "vo_atk_grunt_low_01"},
            "crouch_front_kick": {"reach": 3.5, "damage": 60, "height": "low", "startup": 7, "active": 4, "recovery": 9, "sound_whoosh": "sfx_fol_Cloth_sm_01", "sound_vocal": "vo_atk_grunt_low_02"}, # Generic kick whoosh
        }
        # TODO: These sound keys (sound_whoosh, sound_vocal) need to be generalized or loaded from character specific data.

        self.dedicated_channel_id = None
        try:
            if pygame.mixer.get_init():
                num_chans = pygame.mixer.get_num_channels()
                if is_player1 and num_chans > 0: self.dedicated_channel_id = 0 # P1 uses channel 0
                elif not is_player1 and num_chans > 1: self.dedicated_channel_id = 1 # P2 uses channel 1
        except pygame.error:
            pass


    def _get_player_sound_channel_id(self):
        """Attempts to get the player's dedicated channel if it's not busy."""
        if self.dedicated_channel_id is not None:
            try:
                ch = pygame.mixer.Channel(self.dedicated_channel_id)
                if not ch.get_busy():
                    return self.dedicated_channel_id
            except pygame.error: # Channel might be invalid if mixer was uninitialized/reinitialized
                return None
        return None # Fallback to SoundManager choosing any free channel

    def update(self):
        """Called each frame by the Game loop to update player state (e.g., jump physics)."""
        # Update timers
        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1

        if self.is_attacking and self.attack_frame_timer > 0:
            self.attack_frame_timer -=1
            if self.attack_frame_timer == 0:
                self.is_attacking = False
                self.current_attack_type = None
                if not self.is_jumping and not self.is_crouching : self.action_state = "idle"
                # print(f"{self.char_name} attack finished.")

        # Jumping physics
        if self.is_jumping:
            self.position_y += self.y_velocity
            self.y_velocity -= self.gravity
            if self.position_y <= self.ground_level:
                self.position_y = self.ground_level
                self.is_jumping = False
                self.y_velocity = 0
                if not self.is_crouching:
                    self.action_state = "idle"
                land_sound = self._get_foley_sound("land", fallback_sfx_key="cloth_lg_02")
                self._play_sound_with_panning(land_sound,'land')

    def _get_foley_sound(self, action_key, fallback_sfx_key=None):
        char_specific_sound = None
        char_foley_prefixes = ["sfx_fol_cloth_sm_", "sfx_fol_leather_sm_", "sfx_fol_boot_"]

        if action_key == "step":
            import random
            potential_steps = [f"{prefix}{random.randint(1,3)}" for prefix in char_foley_prefixes[:2]]
            random.shuffle(potential_steps)
            for skey in potential_steps:
                char_specific_sound = self.sound_manager.get_char_sound(self.char_name, skey)
                if char_specific_sound: break
            if not char_specific_sound:
                char_specific_sound = self.sound_manager.get_sfx_sound("Foley", fallback_sfx_key or "cloth_sm_01")
        elif action_key == "jump":
            char_specific_sound = self.sound_manager.get_char_sound(self.char_name, "vo_grunt_short_01")
            if not char_specific_sound:
                 char_specific_sound = self.sound_manager.get_char_sound(self.char_name, "sfx_fol_cloth_lg_01")
            if not char_specific_sound:
                char_specific_sound = self.sound_manager.get_sfx_sound("Foley", fallback_sfx_key or "cloth_lg_01")
        elif action_key == "land":
            char_specific_sound = self.sound_manager.get_char_sound(self.char_name, "sfx_fol_cloth_lg_03")
            if not char_specific_sound:
                char_specific_sound = self.sound_manager.get_sfx_sound("Foley", fallback_sfx_key or "cloth_lg_03")
        elif action_key == "crouch_start":
            char_specific_sound = self.sound_manager.get_char_sound(self.char_name, "sfx_fol_cloth_sm_04")
            if not char_specific_sound:
                char_specific_sound = self.sound_manager.get_sfx_sound("Foley", fallback_sfx_key or "cloth_sm_04")
        elif action_key == "crouch_end":
            char_specific_sound = self.sound_manager.get_char_sound(self.char_name, "sfx_fol_cloth_sm_05")
            if not char_specific_sound:
                char_specific_sound = self.sound_manager.get_sfx_sound("Foley", fallback_sfx_key or "cloth_sm_05")
        return char_specific_sound

    def _play_sound_with_panning(self, sound_obj, sound_debug_name="player_action"):
        if sound_obj:
            pan_l, pan_r = self._calculate_panning()
            self.sound_manager.play_sound(sound_obj, volume_left=pan_l, volume_right=pan_r, channel_num=self._get_player_sound_channel_id())

    def move(self, direction):
        if self.is_jumping or self.is_crouching or self.is_attacking:
            self.is_walking = False
            return
        old_pos = self.position
        move_amount = 1 * direction
        new_pos = self.position + move_amount
        self.position = max(-10, min(10, new_pos))
        if self.position != old_pos:
            self.action_state = "walking"
            self.is_walking = True
            step_sound = self._get_foley_sound("step")
            self._play_sound_with_panning(step_sound, "step")
        else:
            self.is_walking = False

    def jump(self):
        if not self.is_jumping and not self.is_crouching and not self.is_attacking:
            self.is_jumping = True
            self.y_velocity = self.jump_power
            self.action_state = "jumping"
            jump_sfx = self._get_foley_sound("jump")
            self._play_sound_with_panning(jump_sfx, "jump")

    def crouch(self, start_crouching):
        if self.is_jumping or self.is_attacking: return

        if start_crouching and not self.is_crouching:
            self.is_crouching = True
            self.action_state = "crouching"
            self._play_sound_with_panning(self._get_foley_sound("crouch_start"), "crouch_start")
        elif not start_crouching and self.is_crouching:
            self.is_crouching = False
            if not self.is_jumping : self.action_state = "idle"
            self._play_sound_with_panning(self._get_foley_sound("crouch_end"), "crouch_end")

    def _start_attack(self, attack_name_key):
        if self.is_attacking or self.attack_cooldown > 0 or self.is_jumping: # Simple restrictions
             # Allow attacks while crouching, attack_name_key will be specific e.g. "crouch_front_punch"
            if not (self.is_crouching and "crouch" in attack_name_key): # Allow crouch attacks if crouching
                 return False # Cannot attack

        props = self.attack_properties.get(attack_name_key)
        if not props:
            print(f"Warning: Attack properties for '{attack_name_key}' not found.")
            return False

        self.is_attacking = True
        self.current_attack_type = attack_name_key # Store the type of attack being performed
        # Total duration of attack animation (startup + active + recovery frames)
        total_attack_frames = props["startup"] + props["active"] + props["recovery"]
        self.attack_frame_timer = total_attack_frames
        self.attack_cooldown = total_attack_frames + 5 # Small cooldown after attack finishes
        self.action_state = f"attacking_{attack_name_key}"

        print(f"{self.char_name} performs {attack_name_key}")

        # Play attack sounds (whoosh and vocal)
        whoosh_sound_key = props.get("sound_whoosh")
        vocal_sound_key = props.get("sound_vocal")

        if whoosh_sound_key:
            # Try char specific first, then generic SFX
            whoosh_sound = self.sound_manager.get_char_sound(self.char_name, whoosh_sound_key)
            if not whoosh_sound: # Fallback to a generic whoosh from Fight SFX if specific not found
                whoosh_sound = self.sound_manager.get_sfx_sound("Fight", "hit_whoosh_sm01") # Ensure this exists
            self._play_sound_with_panning(whoosh_sound, "attack_whoosh")

        if vocal_sound_key:
            vocal_sound = self.sound_manager.get_char_sound(self.char_name, vocal_sound_key)
            self._play_sound_with_panning(vocal_sound, "attack_vocal")
        return True


    # --- Basic Attack Methods ---
    def front_punch(self):
        attack_key = "crouch_front_punch" if self.is_crouching else "front_punch"
        self._start_attack(attack_key)

    def back_punch(self): # Assuming no crouch version for simplicity here, can be added
        if not self.is_crouching: self._start_attack("back_punch")
        # else: self._start_attack("crouch_back_punch") # if defined

    def front_kick(self):
        attack_key = "crouch_front_kick" if self.is_crouching else "front_kick"
        self._start_attack(attack_key)

    def back_kick(self): # Assuming no crouch version
         if not self.is_crouching: self._start_attack("back_kick")

    def _calculate_panning(self):
        normalized_pos = (self.position + 10) / 20.0
        pan_left = 1.0 - normalized_pos
        pan_right = normalized_pos
        pan_left = max(0.0, min(1.0, pan_left))
        pan_right = max(0.0, min(1.0, pan_right))
        return pan_left, pan_right

    def get_panning(self): # May not be needed if _play_sound_with_panning is used internally
        return self._calculate_panning()

class Game:
    def __init__(self):
        self.sound_manager = SoundManager()
        self.player1 = None
        self.player2 = None
        self.game_state = "char_select"
        self.running = True
        self.clock = pygame.time.Clock()

        self.announcer_channel = None
        self.menu_sfx_channel = None
        try:
            if pygame.mixer.get_init():
                num_chans = pygame.mixer.get_num_channels()
                if num_chans >= 4:
                    self.announcer_channel = pygame.mixer.Channel(2)
                    self.menu_sfx_channel = pygame.mixer.Channel(3)
                elif num_chans >= 1 :
                     self.announcer_channel = pygame.mixer.Channel(0) # Fallback for announcer
        except pygame.error as e:
            print(f"Error assigning dedicated game channels: {e}.")

        self.available_chars = self._get_available_chars()
        if not self.available_chars:
            print("ERROR: No characters found. Exiting.")
            self.running = False
            return

        self.p1_char_selection_index = 0
        self.p2_char_selection_index = 0
        self.current_selector = 1

        if self.running and self.available_chars:
            initial_char_p1 = self.available_chars[self.p1_char_selection_index]
            self._play_char_name_announcement(initial_char_p1)

    def _get_available_chars(self):
        if os.path.exists(CHARS_PATH):
            return sorted([d for d in os.listdir(CHARS_PATH) if os.path.isdir(os.path.join(CHARS_PATH, d))])
        return []

    def _get_char_anno_sound_key(self, char_name):
        name_lower = char_name.lower()
        abbreviation = ""
        if name_lower == "kung lao": abbreviation = "kung"
        elif name_lower == "liu kang": abbreviation = "liuk"
        else:
            parts = name_lower.split()
            abbreviation = parts[0][:4] if parts else name_lower[:4]
        return f"name_{abbreviation}_frnt01"

    def _play_char_name_announcement(self, char_name):
        anno_sound_key = self._get_char_anno_sound_key(char_name)
        char_anno_sound = self.sound_manager.get_sfx_sound("Announcer", "names", anno_sound_key)

        announcer_ch_id = None
        if self.announcer_channel and isinstance(self.announcer_channel, pygame.mixer.Channel):
            announcer_ch_id = self.announcer_channel.id
        elif pygame.mixer.get_init() and pygame.mixer.get_num_channels() > 0:
            if not pygame.mixer.Channel(0).get_busy(): announcer_ch_id = 0

        if char_anno_sound:
            self.sound_manager.play_sound(char_anno_sound, channel_num=announcer_ch_id)
        else:
            print(f"Warning: Announcer sound for {char_name} (key: {anno_sound_key}) not found.")

    def run(self):
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.USEREVENT + 1:
                     if self.game_state == "fighting":
                        fight_sound = self.sound_manager.get_sfx_sound("Announcer", "fight1")
                        if fight_sound:
                            self.sound_manager.play_sound(fight_sound, channel_num=self.announcer_channel.id if self.announcer_channel else None)
                        pygame.time.set_timer(pygame.USEREVENT + 1, 0)
                elif event.type == pygame.KEYDOWN:
                    self._handle_keydown(event.key)
                elif event.type == pygame.KEYUP:
                    self._handle_keyup(event.key)

            self._update()
            self.clock.tick(60)
        pygame.quit()

    def _handle_keydown(self, key):
        if not self.available_chars: return

        if self.game_state == "char_select":
            # Character selection input is typically KeyDown only.
            self._handle_char_select_input(key)
        elif self.game_state == "fighting":
            self._handle_fighting_input(key, is_keydown=True)

    def _handle_keyup(self, key):
        if not self.available_chars: return

        if self.game_state == "fighting":
            self._handle_fighting_input(key, is_keydown=False)
        # Potentially handle keyups for menu if any action depends on releasing a key.

    def _handle_char_select_input(self, key): # This method is only called on KEYDOWN
        selected_char_name_for_announcement = None
        active_selection_index = 0
        is_p1_selecting = self.current_selector == 1

        nav_sound = self.sound_manager.get_sfx_sound("Foley", "cloth_sm_01")
        menu_sfx_channel_id = None
        if self.menu_sfx_channel and isinstance(self.menu_sfx_channel, pygame.mixer.Channel):
            menu_sfx_channel_id = self.menu_sfx_channel.id
        elif pygame.mixer.get_init() and pygame.mixer.get_num_channels() > 1:
            if not pygame.mixer.Channel(1).get_busy(): menu_sfx_channel_id = 1

        current_char_list = self.available_chars
        if not current_char_list: return # Should not happen if initial check passed

        if is_p1_selecting: active_selection_index = self.p1_char_selection_index
        else: active_selection_index = self.p2_char_selection_index

        if key == pygame.K_w: # Up
            if nav_sound: self.sound_manager.play_sound(nav_sound, channel_num=menu_sfx_channel_id)
            active_selection_index = (active_selection_index - 1 + len(current_char_list)) % len(current_char_list)
            selected_char_name_for_announcement = current_char_list[active_selection_index]

        elif key == pygame.K_s: # Down
            if nav_sound: self.sound_manager.play_sound(nav_sound, channel_num=menu_sfx_channel_id)
            active_selection_index = (active_selection_index + 1) % len(current_char_list)
            selected_char_name_for_announcement = current_char_list[active_selection_index]

        elif key == pygame.K_t: # Front Punch to select
            selected_char_name = current_char_list[active_selection_index]
            # print(f"Player {self.current_selector} selected {selected_char_name}")

            confirm_sound = self.sound_manager.get_sfx_sound("Fight", "confirm01")
            if confirm_sound: self.sound_manager.play_sound(confirm_sound, channel_num=menu_sfx_channel_id)

            pygame.time.wait(100)
            self._play_char_name_announcement(selected_char_name)

            anno_sound_to_wait_for = self.sound_manager.get_sfx_sound("Announcer", "names", self._get_char_anno_sound_key(selected_char_name))
            if anno_sound_to_wait_for:
                pygame.time.wait(int(anno_sound_to_wait_for.get_length() * 700))
            else: pygame.time.wait(200)

            if is_p1_selecting:
                self.player1 = Player(selected_char_name, self.sound_manager, is_player1=True)
                self.p1_char_selection_index = active_selection_index
                self.current_selector = 2
                # print("Player 2, select your character.")
                p2_initial_char = current_char_list[self.p2_char_selection_index]
                self._play_char_name_announcement(p2_initial_char)
            else:
                self.player2 = Player(selected_char_name, self.sound_manager, is_player1=False)
                self.p2_char_selection_index = active_selection_index
                self._start_fight()

        if selected_char_name_for_announcement:
             self._play_char_name_announcement(selected_char_name_for_announcement)

        if is_p1_selecting: self.p1_char_selection_index = active_selection_index
        else: self.p2_char_selection_index = active_selection_index

    def _start_fight(self):
        # print("Starting fight!")
        self.game_state = "fighting"

        round1_sound = self.sound_manager.get_sfx_sound("Announcer", "round1")
        fight_sound = self.sound_manager.get_sfx_sound("Announcer", "fight1")

        announcer_ch_id = None
        if self.announcer_channel and isinstance(self.announcer_channel, pygame.mixer.Channel):
            announcer_ch_id = self.announcer_channel.id
        elif pygame.mixer.get_init() and pygame.mixer.get_num_channels() > 0:
            if not pygame.mixer.Channel(0).get_busy(): announcer_ch_id = 0

        if round1_sound:
            channel = self.sound_manager.play_sound(round1_sound, channel_num=announcer_ch_id)
            if channel:
                delay_ms = int(round1_sound.get_length() * 1000) + 300
                pygame.time.set_timer(pygame.USEREVENT + 1, delay_ms, loops=1)
            else:
                if fight_sound:
                    pygame.time.wait(200)
                    self.sound_manager.play_sound(fight_sound, channel_num=announcer_ch_id)
        elif fight_sound:
             self.sound_manager.play_sound(fight_sound, channel_num=announcer_ch_id)

    def _handle_fighting_input(self, key, is_keydown):
        # Player 1 controls
        if self.player1:
            if is_keydown:
                if key == pygame.K_a: self.player1.move(-1)
                elif key == pygame.K_d: self.player1.move(1)
                elif key == pygame.K_w: self.player1.jump()
                elif key == pygame.K_s: self.player1.crouch(True)
                elif key == pygame.K_t: self.player1.front_punch()
                elif key == pygame.K_u: self.player1.back_punch()
                elif key == pygame.K_g: self.player1.front_kick()
                elif key == pygame.K_j: self.player1.back_kick()
            else: # Key UP for P1
                if key == pygame.K_s: self.player1.crouch(False)
                elif key == pygame.K_a or key == pygame.K_d: self.player1.is_walking = False

        # Player 2 controls
        if self.player2:
            if is_keydown:
                if key == pygame.K_LEFT: self.player2.move(-1)
                elif key == pygame.K_RIGHT: self.player2.move(1)
                elif key == pygame.K_UP: self.player2.jump()
                elif key == pygame.K_DOWN: self.player2.crouch(True)
                # Example P2 attack keys (Using Numpad as often done)
                elif key == pygame.K_KP4: self.player2.front_punch() # Numpad 4
                elif key == pygame.K_KP5: self.player2.back_punch()  # Numpad 5
                elif key == pygame.K_KP1: self.player2.front_kick()  # Numpad 1
                elif key == pygame.K_KP2: self.player2.back_kick()   # Numpad 2
            else: # Key UP for P2
                if key == pygame.K_DOWN: self.player2.crouch(False)
                elif key == pygame.K_LEFT or key == pygame.K_RIGHT: self.player2.is_walking = False


    def _update(self):
        """Called every frame to update game logic."""
        if self.game_state == "fighting":
            # Update players (handles jumping physics, attack timers, etc.)
            if self.player1: self.player1.update()
            if self.player2: self.player2.update()

            # --- Attack Collision Detection ---
            # Check P1 attacking P2
            if self.player1 and self.player1.is_attacking and self.player2:
                self._check_attack_collision(self.player1, self.player2)

            # Check P2 attacking P1
            if self.player2 and self.player2.is_attacking and self.player1:
                 self._check_attack_collision(self.player2, self.player1)

    def _check_attack_collision(self, attacker, defender):
        if not attacker.current_attack_type: return

        props = attacker.attack_properties.get(attacker.current_attack_type)
        if not props: return

        # Check if within "active" frames of the attack
        # Assuming startup frames have passed, and now in active hit window
        # A more precise frame data system would track current_frame_of_attack vs props["startup"] and props["active"]
        # For now, if is_attacking, we assume it's potentially hitable during its attack_frame_timer > recovery_frames
        attack_total_duration = props["startup"] + props["active"] + props["recovery"]
        frames_into_attack = attack_total_duration - attacker.attack_frame_timer

        is_in_active_hit_frames = props["startup"] <= frames_into_attack < (props["startup"] + props["active"])

        if not is_in_active_hit_frames:
            return # Not in the part of the animation that can hit

        # 1. Check distance (horizontal reach)
        distance = abs(attacker.position - defender.position)
        # print(f"Checking collision: {attacker.char_name} vs {defender.char_name}. Dist: {distance}, Reach: {props['reach']}")

        if distance < props["reach"]:
            # 2. Check height compatibility
            attack_height = props["height"]
            vulnerable = True
            if attack_height == "high" and defender.is_crouching:
                vulnerable = False
                print(f"{attacker.char_name}'s high attack missed crouching {defender.char_name}")
            if attack_height == "low" and defender.is_jumping: # Low attacks shouldn't hit jumping opponents
                vulnerable = False
                print(f"{attacker.char_name}'s low attack missed jumping {defender.char_name}")
            # Mid attacks generally hit standing or crouching, but might miss jumping depending on hitbox.
            # For now, assume mid hits standing/crouching.
            if attack_height == "mid" and defender.is_jumping: # Simple: mid whiffs on jump for now
                vulnerable = False
                print(f"{attacker.char_name}'s mid attack missed jumping {defender.char_name}")


            if vulnerable: # and not defender.is_blocking (when implemented)
                print(f"HIT! {attacker.char_name}'s {attacker.current_attack_type} hits {defender.char_name}")
                defender.health -= props["damage"]
                print(f"{defender.char_name} health: {defender.health}")

                # --- Play Hit Effects ---
                # 1. Impact Sound (at defender's location, or midpoint)
                impact_sound_key = "hit_body01" # Default
                if "punch" in attacker.current_attack_type: impact_sound_key = "hit_face_punch01" # if high, etc.
                if "kick" in attacker.current_attack_type: impact_sound_key = "hit_kick_body01"

                impact_sound = self.sound_manager.get_sfx_sound("Fight", impact_sound_key)
                if impact_sound:
                    # Pan the impact sound to the defender's position
                    pan_l, pan_r = defender._calculate_panning()
                    # Use a non-dedicated channel for impact sounds
                    impact_channel_id = 4 if pygame.mixer.get_num_channels() > 4 else None
                    self.sound_manager.play_sound(impact_sound, volume_left=pan_l, volume_right=pan_r, channel_num=impact_channel_id)

                # 2. Defender's Pain Sound
                # Try to get a specific pain sound, e.g., vo_react_pain_lg_01, vo_react_pain_sm_01
                pain_sound_key_options = ["vo_react_pain_lg_01", "vo_react_pain_med_01", "vo_react_pain_sm_01"]
                pain_sound = None
                for ps_key in pain_sound_key_options:
                    pain_sound = self.sound_manager.get_char_sound(defender.char_name, ps_key)
                    if pain_sound: break
                if pain_sound:
                    defender._play_sound_with_panning(pain_sound, "pain_reaction") # Uses defender's panning & channel

                # 3. Blood sound (optional, if damage is high or certain attack type)
                if props["damage"] > 60: # Arbitrary threshold for blood
                    blood_sound = self.sound_manager.get_sfx_sound("Fight", "blood_spurt01")
                    if blood_sound:
                         # Pan to defender, use another non-dedicated channel
                        pan_l, pan_r = defender._calculate_panning()
                        blood_channel_id = 5 if pygame.mixer.get_num_channels() > 5 else None
                        self.sound_manager.play_sound(blood_sound, volume_left=pan_l, volume_right=pan_r, channel_num=blood_channel_id)

                # Prevent further hits from this same attack instance (important!)
                attacker.is_attacking = False
                attacker.attack_frame_timer = 0 # End this attack's active frames
                attacker.current_attack_type = None
                # Could also put defender in a brief "hit stun" state here.
                # defender.action_state = "hit_stun"
                # defender.hit_stun_timer = X_frames


if __name__ == "__main__":
    pygame.mixer.pre_init(44100, -16, 2, 512)
    pygame.init()

    if not pygame.mixer.get_init():
        print("Pygame mixer could not be initialized.")
    else:
        # print(f"Mixer initialized: {pygame.mixer.get_init()}")
        freq, fmt, chans = pygame.mixer.get_init()
        # print(f"Mixer settings: freq={freq}, format={fmt}, channels={chans}")
        pygame.mixer.set_num_channels(16)
        # print(f"Number of channels set to: {pygame.mixer.get_num_channels()}")

        mk_audio_game = Game()
        if mk_audio_game.running:
            mk_audio_game.run()

        if not mk_audio_game.running and pygame.get_init():
            pygame.quit()
