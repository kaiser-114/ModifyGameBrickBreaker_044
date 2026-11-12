import pygame
import random
import math
import array

# Inisialisasi Pygame dan Mixer Audio
pygame.init()
pygame.mixer.init(frequency=44100, size=-16, channels=1)

# Dimensi layar
WIDTH, HEIGHT = 600, 500
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Block Breaker: Skill & Arena Edition")

clock = pygame.time.Clock()
FPS = 60

# Warna Dasar
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (120, 120, 120)
DARK_GRAY = (40, 40, 40)
CYAN = (0, 255, 255)
MAGENTA = (255, 0, 255)
ORANGE = (255, 165, 0)
BLUE = (50, 150, 255)
GOLD = (255, 215, 0)

# Warna Brick berdasarkan Health
HEALTH_COLORS = {
    1: (0, 255, 0),    # Hijau: 1 HP
    2: (255, 255, 0),  # Kuning: 2 HP
    3: (255, 50, 50),  # Merah: 3 HP
    -1: GRAY           # Abu-abu: Unbreakable
}

# Konfigurasi 5 Jenis Skill Point
SKILL_INFO = {
    1: {"color": CYAN,    "label": "+B", "name": "+1 Bola Baru"},
    2: {"color": MAGENTA, "label": "2X", "name": "Level Bola 2x"},
    3: {"color": BLUE,    "label": "P>", "name": "Paddle Cepat 2x"},
    4: {"color": GOLD,    "label": "HD", "name": "Bola Keras (2 dtk)"},
    5: {"color": ORANGE,  "label": "4X", "name": "Bola Cepat 4x (10 dtk)"}
}

# Font
font_sm = pygame.font.Font('freesansbold.ttf', 13)
font_md = pygame.font.Font('freesansbold.ttf', 18)
font_lg = pygame.font.Font('freesansbold.ttf', 28)


# Fungsi pembuat efek suara sintetis
def generate_beep(freq, duration=0.08, volume=0.25):
    sample_rate = 44100
    n_samples = int(sample_rate * duration)
    buf = array.array('h', [
        int(32767 * volume * math.sin(2 * math.pi * freq * i / sample_rate))
        for i in range(n_samples)
    ])
    return pygame.mixer.Sound(buffer=buf)


SOUND_PADDLE = generate_beep(440, 0.05)
SOUND_BRICK_HIT = generate_beep(587, 0.05)
SOUND_BRICK_BREAK = generate_beep(880, 0.09)
SOUND_UNBREAKABLE = generate_beep(220, 0.07)
SOUND_SKILL_PICKUP = generate_beep(1046, 0.12)
SOUND_LOST_LIFE = generate_beep(150, 0.35)


class Striker:
    def __init__(self):
        self.width, self.height = 100, 15
        self.posx = WIDTH // 2 - self.width // 2
        self.posy = HEIGHT - 40
        self.base_speed = 7
        self.speed_multiplier = 1
        self.color = WHITE
        self.rect = pygame.Rect(self.posx, self.posy, self.width, self.height)

    def reset_pos(self):
        self.posx = WIDTH // 2 - self.width // 2
        self.rect.x = self.posx

    def display(self):
        color = BLUE if self.speed_multiplier > 1 else self.color
        pygame.draw.rect(screen, color, self.rect, border_radius=3)

    def update(self, xFac):
        current_speed = self.base_speed * self.speed_multiplier
        self.posx += current_speed * xFac
        if self.posx <= 0:
            self.posx = 0
        elif self.posx + self.width >= WIDTH:
            self.posx = WIDTH - self.width
        self.rect.x = int(self.posx)


class Block:
    def __init__(self, posx, posy, width, height, health):
        self.rect = pygame.Rect(posx, posy, width, height)
        self.health = health

    def display(self):
        if self.health > 0 or self.health == -1:
            color = HEALTH_COLORS.get(self.health, WHITE)
            pygame.draw.rect(screen, color, self.rect)
            pygame.draw.rect(screen, DARK_GRAY, self.rect, 1)

    def hit(self, damage, is_hard_ball=False):
        if is_hard_ball:
            # Bola keras menghancurkan semua tingkatan brick (termasuk unbreakable)
            self.health = 0
            SOUND_BRICK_BREAK.play()
            return True

        if self.health > 0:
            self.health -= damage
            if self.health <= 0:
                self.health = 0
                SOUND_BRICK_BREAK.play()
                return True
            else:
                SOUND_BRICK_HIT.play()
        elif self.health == -1:
            SOUND_UNBREAKABLE.play()
        return False


class Ball:
    def __init__(self, posx, posy, xFac=None, yFac=-1):
        self.posx, self.posy = float(posx), float(posy)
        self.radius = 7
        self.base_speed = 3.5
        self.xFac = xFac if xFac is not None else random.choice([-1, 1])
        self.yFac = yFac
        self.rect = pygame.Rect(int(self.posx - self.radius), int(self.posy - self.radius), self.radius * 2, self.radius * 2)

    def display(self, is_hard, ball_level):
        if is_hard:
            color = GOLD
        elif ball_level > 1:
            color = MAGENTA
        else:
            color = WHITE
        pygame.draw.circle(screen, color, (int(self.posx), int(self.posy)), self.radius)

    def update(self, speed_mult=1):
        # Sub-stepping agar pada kecepatan 4x bola tidak menembus tembok/brick
        steps = int(speed_mult)
        for _ in range(steps):
            self.posx += self.xFac * self.base_speed
            self.posy += self.yFac * self.base_speed

            if self.posx - self.radius <= 0:
                self.posx = self.radius
                self.xFac *= -1
            elif self.posx + self.radius >= WIDTH:
                self.posx = WIDTH - self.radius
                self.xFac *= -1

            if self.posy - self.radius <= 0:
                self.posy = self.radius
                self.yFac *= -1

            self.rect.topleft = (int(self.posx - self.radius), int(self.posy - self.radius))

        return self.posy - self.radius >= HEIGHT

    def hit_paddle(self, paddle_rect):
        if self.yFac > 0:
            self.yFac *= -1
            # Variasi sudut pantul berdasarkan titik jatuh di paddle
            offset = (self.posx - paddle_rect.centerx) / (paddle_rect.width / 2)
            self.xFac = offset * 1.2
            if abs(self.xFac) < 0.4:
                self.xFac = 0.4 if self.xFac >= 0 else -0.4
            SOUND_PADDLE.play()

    def hit_block(self, block_rect):
        dx = min(abs(self.rect.right - block_rect.left), abs(self.rect.left - block_rect.right))
        dy = min(abs(self.rect.bottom - block_rect.top), abs(self.rect.top - block_rect.bottom))
        if dx < dy:
            self.xFac *= -1
        else:
            self.yFac *= -1


class SkillItem:
    def __init__(self, x, y, skill_type):
        self.rect = pygame.Rect(x - 12, y - 8, 24, 16)
        self.skill_type = skill_type
        self.speed = 2.5
        self.color = SKILL_INFO[skill_type]["color"]
        self.label = SKILL_INFO[skill_type]["label"]

    def update(self):
        self.rect.y += self.speed
        return self.rect.top >= HEIGHT

    def display(self):
        pygame.draw.rect(screen, self.color, self.rect, border_radius=4)
        pygame.draw.rect(screen, WHITE, self.rect, 1, border_radius=4)
        txt = font_sm.render(self.label, True, BLACK)
        screen.blit(txt, (self.rect.centerx - txt.get_width() // 2, self.rect.centery - txt.get_height() // 2))


# Desain 5 Arena Level (12 Kolom x 8 Baris, Rapat Tanpa Celah)
def create_arena(level):
    blocks = []
    bw, bh = 50, 20
    cols = WIDTH // bw  # 12 kolom
    rows = 8
    start_y = 45

    for r in range(rows):
        for c in range(cols):
            x = c * bw
            y = start_y + r * bh
            health = 0

            if level == 1:
                # Arena 1: Baris Klasik Berlapis
                if r < 2: health = 3
                elif r < 5: health = 2
                else: health = 1
                if r == 4 and c in (3, 8): health = -1

            elif level == 2:
                # Arena 2: Benteng Pertahanan
                if r == 7 and c not in (5, 6): health = -1
                elif (r + c) % 2 == 0: health = 3
                else: health = 1

            elif level == 3:
                # Arena 3: Piramida Inti Baja
                if abs(c - 5.5) <= r:
                    if r == 5 and 3 <= c <= 8: health = -1
                    elif r < 4: health = 3
                    else: health = 2
                else:
                    health = 1

            elif level == 4:
                # Arena 4: Koridor Labirin
                if c in (2, 5, 6, 9) and r < 6: health = -1
                elif r % 2 == 0: health = 3
                else: health = 2

            elif level == 5:
                # Arena 5: Boss Cage (Sangkar Baja)
                if (r in (1, 6) and 2 <= c <= 9) or (c in (2, 9) and 1 <= r <= 6):
                    if c in (5, 6) and r == 6: health = 3  # Pintu masuk bola
                    else: health = -1
                elif 2 < c < 9 and 1 < r < 6:
                    health = 3
                else:
                    health = 2

            if health != 0:
                blocks.append(Block(x, y, bw, bh, health))

    return blocks


def draw_text_center(text, font_obj, color, y):
    surf = font_obj.render(text, True, color)
    screen.blit(surf, (WIDTH // 2 - surf.get_width() // 2, y))


def main():
    state = "MENU"  # MENU, WAIT_START, PLAY, ASK_CONTINUE, LEVEL_CLEAR
    selected_level = 1
    score = 0
    lives = 3

    striker = Striker()
    striker_dir = 0
    balls = []
    blocks = []
    skills = []

    # Status Efek Skill
    ball_level = 1
    hard_ball_end_time = 0
    fast_ball_end_time = 0

    def init_level(lvl, reset_score=False):
        nonlocal score, lives, balls, blocks, skills, ball_level, hard_ball_end_time, fast_ball_end_time
        if reset_score:
            score = 0
            lives = 3
        striker.reset_pos()
        striker.speed_multiplier = 1
        ball_level = 1
        hard_ball_end_time = 0
        fast_ball_end_time = 0
        skills.clear()
        balls = [Ball(striker.rect.centerx, striker.rect.top - 8)]
        blocks = create_arena(lvl)

    def reset_after_death():
        nonlocal balls, skills, ball_level, hard_ball_end_time, fast_ball_end_time
        striker.reset_pos()
        striker.speed_multiplier = 1
        ball_level = 1
        hard_ball_end_time = 0
        fast_ball_end_time = 0
        skills.clear()
        balls = [Ball(striker.rect.centerx, striker.rect.top - 8)]

    running = True
    while running:
        screen.fill(BLACK)
        current_time = pygame.time.get_ticks()

        # Event Handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN:
                if state == "MENU":
                    if event.key == pygame.K_LEFT and selected_level > 1:
                        selected_level -= 1
                    elif event.key == pygame.K_RIGHT and selected_level < 5:
                        selected_level += 1
                    elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        init_level(selected_level, reset_score=True)
                        state = "WAIT_START"

                elif state == "WAIT_START":
                    if event.key == pygame.K_LEFT: striker_dir = -1
                    elif event.key == pygame.K_RIGHT: striker_dir = 1
                    elif event.key == pygame.K_SPACE:
                        state = "PLAY"

                elif state == "PLAY":
                    if event.key == pygame.K_LEFT: striker_dir = -1
                    elif event.key == pygame.K_RIGHT: striker_dir = 1

                elif state == "ASK_CONTINUE":
                    if event.key in (pygame.K_y, pygame.K_SPACE, pygame.K_RETURN):
                        if lives <= 0:
                            lives = 3
                            score = max(0, score - 50)
                        reset_after_death()
                        # Langsung mulai tanpa disuruh pencet spasi lagi
                        state = "PLAY"
                    elif event.key in (pygame.K_n, pygame.K_ESCAPE):
                        state = "MENU"

                elif state == "LEVEL_CLEAR":
                    if event.key == pygame.K_SPACE:
                        if selected_level < 5:
                            selected_level += 1
                            init_level(selected_level, reset_score=False)
                            state = "WAIT_START"
                        else:
                            state = "MENU"

            if event.type == pygame.KEYUP:
                if event.key in (pygame.K_LEFT, pygame.K_RIGHT):
                    striker_dir = 0

        # ================= STATE: MAIN MENU =================
        if state == "MENU":
            draw_text_center("BLOCK BREAKER: ARENA", font_lg, CYAN, 70)
            draw_text_center("Pilih Arena (Panah Kiri / Kanan):", font_md, WHITE, 150)
            draw_text_center(f"<  ARENA LEVEL {selected_level}  >", font_lg, GOLD, 190)

            # Info Skill Point di Menu
            draw_text_center("Daftar Skill Point (70% Drop Rate):", font_sm, WHITE, 260)
            y_pos = 285
            for k, info in SKILL_INFO.items():
                txt = font_sm.render(f"[{info['label']}] : {info['name']}", True, info["color"])
                screen.blit(txt, (WIDTH // 2 - 110, y_pos))
                y_pos += 22

            draw_text_center("Tekan ENTER atau SPASI untuk Masuk Arena", font_md, HEALTH_COLORS[1], 430)

        # ================= STATE: GAMEPLAY & OVERLAYS =================
        else:
            is_hard = current_time < hard_ball_end_time
            ball_speed_mult = 4 if current_time < fast_ball_end_time else 1

            # Update saat menunggu mulai (bola menempel di paddle)
            if state == "WAIT_START":
                striker.update(striker_dir)
                if balls:
                    balls[0].posx = striker.rect.centerx
                    balls[0].posy = striker.rect.top - balls[0].radius

            # Update saat bermain aktif
            elif state == "PLAY":
                striker.update(striker_dir)

                # Update Bola
                for b in balls[:]:
                    if b.update(ball_speed_mult):
                        balls.remove(b)
                        continue

                    if b.rect.colliderect(striker.rect):
                        b.hit_paddle(striker.rect)

                    for blk in blocks[:]:
                        if b.rect.colliderect(blk.rect):
                            # Jika bola tidak dalam mode keras, bola memantul normal
                            if not is_hard:
                                b.hit_block(blk.rect)

                            destroyed = blk.hit(ball_level, is_hard)
                            if destroyed:
                                blocks.remove(blk)
                                score += 10
                                # 70% Persentase mengeluarkan Skill Point
                                if random.random() <= 0.70:
                                    s_type = random.randint(1, 5)
                                    skills.append(SkillItem(blk.rect.centerx, blk.rect.centery, s_type))
                            break

                # Update Skill Point yang jatuh
                for sk in skills[:]:
                    if sk.update():
                        skills.remove(sk)
                    elif sk.rect.colliderect(striker.rect):
                        SOUND_SKILL_PICKUP.play()
                        if sk.skill_type == 1:
                            # Tambah 1 bola baru
                            ref_x = balls[0].posx if balls else striker.rect.centerx
                            ref_y = balls[0].posy if balls else striker.rect.top - 10
                            balls.append(Ball(ref_x, ref_y, xFac=random.choice([-1, 1]), yFac=-1))
                        elif sk.skill_type == 2:
                            # Gandakan level (damage) bola
                            ball_level *= 2
                        elif sk.skill_type == 3:
                            # Kecepatan paddle 2x
                            striker.speed_multiplier = 2
                        elif sk.skill_type == 4:
                            # Bola keras selama 2 detik
                            hard_ball_end_time = current_time + 2000
                        elif sk.skill_type == 5:
                            # Bola bergerak 4x selama 10 detik
                            fast_ball_end_time = current_time + 10000
                        skills.remove(sk)

                # Cek apakah semua bola jatuh (Mati)
                if not balls:
                    lives -= 1
                    SOUND_LOST_LIFE.play()
                    striker_dir = 0
                    state = "ASK_CONTINUE"

                # Cek apakah semua brick yang bisa dihancurkan sudah habis
                breakable_left = [blk for blk in blocks if blk.health > 0]
                if not breakable_left:
                    striker_dir = 0
                    state = "LEVEL_CLEAR"

            # Render semua objek permainan
            striker.display()
            for blk in blocks:
                blk.display()
            for sk in skills:
                sk.display()
            for b in balls:
                b.display(is_hard, ball_level)

            # HUD Informasi di Bagian Atas & Bawah
            hud_top = font_sm.render(
                f"Arena: {selected_level}/5   |   Score: {score}   |   Lives: {lives}   |   Ball Lv: {ball_level}",
                True, WHITE
            )
            screen.blit(hud_top, (15, 12))

            # Indikator Timer Skill Aktif di Bawah
            status_list = []
            if striker.speed_multiplier > 1:
                status_list.append("Paddle: 2x Speed")
            if is_hard:
                sisa_hd = (hard_ball_end_time - current_time) / 1000
                status_list.append(f"Bola Keras: {sisa_hd:.1f}s")
            if ball_speed_mult > 1:
                sisa_4x = (fast_ball_end_time - current_time) / 1000
                status_list.append(f"Speed 4x: {sisa_4x:.1f}s")

            if status_list:
                status_txt = font_sm.render("  |  ".join(status_list), True, GOLD)
                screen.blit(status_txt, (15, HEIGHT - 20))

            # Overlay Teks Instruksi sesuai State
            if state == "WAIT_START":
                pygame.draw.rect(screen, (20, 20, 20), (80, HEIGHT // 2 - 25, 440, 50), border_radius=8)
                pygame.draw.rect(screen, CYAN, (80, HEIGHT // 2 - 25, 440, 50), 2, border_radius=8)
                draw_text_center("Tekan SPASI untuk Mulai Bermain!", font_md, WHITE, HEIGHT // 2 - 10)

            elif state == "ASK_CONTINUE":
                pygame.draw.rect(screen, (20, 20, 20), (60, HEIGHT // 2 - 55, 480, 110), border_radius=8)
                pygame.draw.rect(screen, HEALTH_COLORS[3], (60, HEIGHT // 2 - 55, 480, 110), 2, border_radius=8)
                if lives > 0:
                    draw_text_center(f"Bola Jatuh! Sisa Nyawa: {lives}", font_md, GOLD, HEIGHT // 2 - 35)
                else:
                    draw_text_center("Nyawa Habis!", font_md, HEALTH_COLORS[3], HEIGHT // 2 - 35)
                draw_text_center("Apakah mau lanjut?", font_md, WHITE, HEIGHT // 2 - 5)
                draw_text_center("[Y / SPASI] Lanjut Main     [N / ESC] Ke Menu", font_sm, CYAN, HEIGHT // 2 + 25)

            elif state == "LEVEL_CLEAR":
                pygame.draw.rect(screen, (20, 20, 20), (70, HEIGHT // 2 - 45, 460, 90), border_radius=8)
                pygame.draw.rect(screen, HEALTH_COLORS[1], (70, HEIGHT // 2 - 45, 460, 90), 2, border_radius=8)
                if selected_level < 5:
                    draw_text_center(f"ARENA {selected_level} SELESAI!", font_md, HEALTH_COLORS[1], HEIGHT // 2 - 25)
                    draw_text_center("Tekan SPASI untuk lanjut ke Arena berikutnya", font_sm, WHITE, HEIGHT // 2 + 10)
                else:
                    draw_text_center("SELAMAT! SEMUA 5 ARENA TAMAT!", font_md, GOLD, HEIGHT // 2 - 25)
                    draw_text_center("Tekan SPASI untuk kembali ke Main Menu", font_sm, WHITE, HEIGHT // 2 + 10)

        pygame.display.update()
        clock.tick(FPS)

    pygame.quit()


if __name__ == "__main__":
    main()