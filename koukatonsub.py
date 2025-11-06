import pygame as pg
import os
import random 

# 1. 定数と初期設定
pg.init() 
pg.font.init() 

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600

try:
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
except NameError:
    pass 

TILE_SIZE = 40
GRAVITY = 0.8        
JUMP_STRENGTH = -15    
PLAYER_SPEED = 5       
BULLET_SPEED = 10 

SUPER_ATTACK_CHANCE = 5 

# 色の定義 (頭上の数字用)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255) 
BROWN = (139, 69, 19)   
RED_TEXT = (255, 0, 0)      
BLUE_TEXT = (0, 0, 255)     
YELLOW_TEXT = (255, 255, 0) 
CYAN_TEXT = (0, 255, 255)   

# 頭上に表示する数字用のフォント
try:
    attack_font = pg.font.SysFont(None, 40)
except Exception as e:
    print(f"フォントの読み込みに失敗: {e}。デフォルトフォントを使用します。")
    attack_font = pg.font.Font(None, 40) 

# 画面設定
screen = pg.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pg.display.set_caption("2Dアクションゲーム デモ (Zキーで攻撃 - 5%で超特大！)")
clock = pg.time.Clock()

# 2. ステージデータ (省略... 元のコードと同じ)
map_data = [
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 0],
    [1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [1, 1, 1, 1, 1, 1, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
]

# 3. ステージの「当たり判定用の四角形(Rect)」リストを作成
block_rects = []
for y, row in enumerate(map_data):
    for x, tile_type in enumerate(row):
        if tile_type == 1:
            block_rects.append(pg.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE))

# 4. プレイヤー設定
player_width = (TILE_SIZE // 2) * 3  # 幅 60
player_height = TILE_SIZE * 3        # 高さ 120
player_rect = pg.Rect(100, 100, player_width, player_height) 

# --- 画像読み込みと左右反転 ---
try:
    player_image_original = pg.image.load("カービィカジノ吸収.png")
    player_image_right = pg.transform.scale(player_image_original, (player_width, player_height))
    player_image_left = pg.transform.flip(player_image_right, True, False)
except (pyg.error, FileNotFoundError) as e:
    if isinstance(e, FileNotFoundError):
        print("プレイヤー画像ファイル 'カービィカジノ吸収.png' が見つかりません。")
    else:
        print(f"プレイヤー画像の読み込みに失敗しました: {e}")
    player_image_right = pg.Surface((player_width, player_height))
    player_image_right.fill((50, 200, 50))
    player_image_left = player_image_right.copy() 

player_image_current = player_image_right

# ★★★ 弾の画像読み込みとスケール (ファイル名を修正) ★★★
bullet_images = {} # 弾の画像を格納する辞書

# 弾の種類とファイル名、サイズを定義
bullet_configs = {
    1: {"file": "きいろ.png", "size": (TILE_SIZE // 2, TILE_SIZE // 2)},      # タイプ1 (黄)
    2: {"file": "あお.png", "size": (TILE_SIZE // 2 + 10, TILE_SIZE // 2 + 10)}, # タイプ2 (青)
    3: {"file": "あか.png", "size": (TILE_SIZE // 2 + 20, TILE_SIZE // 2 + 20)},   # タイプ3 (赤)
    99999: {"file": "くろ.png", "size": (TILE_SIZE * 15, TILE_SIZE * 15)}    # 超特大 (黒)
}

for type_key, config in bullet_configs.items():
    try:
        # 画像を読み込む (.jpgは透過情報がないため .convert() が最適ですが、
        # .convert_alpha() でも問題なく動作します)
        img_original = pg.image.load(config["file"]).convert_alpha()
        bullet_images[type_key] = pg.transform.scale(img_original, config["size"])
    except (pg.error, FileNotFoundError) as e:
        # エラーメッセージも正しいファイル名に修正
        print(f"弾画像ファイル '{config['file']}' の読み込みに失敗しました: {e}") 
        #エラー時は代替として赤い四角形を生成
        alt_surface = pg.Surface(config["size"], pg.SRCALPHA) # アルファチャンネル付き
        alt_surface.fill((255, 0, 0, 128)) # 半透明な赤
        bullet_images[type_key] = alt_surface
# ----------------------------------------

player_velocity_y = 0  
is_on_ground = False     
player_move_left = False 
player_move_right = False
player_direction = 1 

# 弾を管理するリスト: [bullet_rect, 弾の画像, 向き(1 or -1), 攻撃タイプ]
bullets = []

current_attack_type = random.randint(1, 3)

# 5. ゲームループ
running = True
while running:
    
    # 6. イベント処理 (キー操作など)
    for event in pg.event.get():
        if event.type == pg.QUIT:
            running = False
        
        if event.type == pg.KEYDOWN:
            if event.key == pg.K_LEFT:
                player_move_left = True
            if event.key == pg.K_RIGHT:
                player_move_right = True
            if event.key == pg.K_SPACE and is_on_ground:
                player_velocity_y = JUMP_STRENGTH 
                is_on_ground = False
                
            # ★★★ 攻撃キー (Zキー) が押された時 ★★★
            if event.key == pg.K_z:
                actual_attack_type = current_attack_type
                
                bullet_image = bullet_images.get(actual_attack_type)
                if bullet_image is None: 
                    bullet_image = bullet_images.get(1) 
                    actual_attack_type = 1 
                    
                bullet_width, bullet_height = bullet_image.get_size()
                
                start_x = player_rect.centerx - bullet_width // 2 
                start_y = player_rect.centery - bullet_height // 2 
                
                bullet_rect = pg.Rect(start_x, start_y, bullet_width, bullet_height)
                
                bullets.append([bullet_rect, bullet_image, player_direction, actual_attack_type])
                
                next_attack_candidate = random.randint(1, 3)
                
                if random.randint(1, 100) <= SUPER_ATTACK_CHANCE:
                    current_attack_type = 99999 
                else:
                    current_attack_type = next_attack_candidate 
            # ★★★★★★★★★★★★★★★★★★★★★★★

        if event.type == pg.KEYUP:
            if event.key == pg.K_LEFT:
                player_move_left = False
            if event.key == pg.K_RIGHT:
                player_move_right = False

    # 7. プレイヤーのロジック更新 (省略... 元と同じ)
    player_movement_x = 0
    if player_move_left: player_movement_x -= PLAYER_SPEED
    if player_move_right: player_movement_x += PLAYER_SPEED
    
    if player_move_right: 
        player_image_current = player_image_right
        player_direction = 1 
    elif player_move_left: 
        player_image_current = player_image_left
        player_direction = -1 

    player_rect.x += player_movement_x 
    
    for block in block_rects:
        if player_rect.colliderect(block):
            if player_movement_x > 0: player_rect.right = block.left 
            elif player_movement_x < 0: player_rect.left = block.right 

    player_velocity_y += GRAVITY 
    player_rect.y += player_velocity_y 
    
    if player_rect.top > SCREEN_HEIGHT + 100:
        player_rect.x = 100; player_rect.y = 100
        player_velocity_y = 0; is_on_ground = False

    is_on_ground = False 
    for block in block_rects:
        if player_rect.colliderect(block):
            if player_velocity_y > 0: 
                player_rect.bottom = block.top; player_velocity_y = 0; is_on_ground = True   
            elif player_velocity_y < 0: 
                player_rect.top = block.bottom; player_velocity_y = 0 

    # ★★★ 弾のロジック更新 ★★★
    for bullet in reversed(bullets):
        bullet_rect = bullet[0]
        direction = bullet[2] # 向きはリストの3番目 (index 2)
        bullet_rect.x += BULLET_SPEED * direction
        if bullet_rect.right < 0 or bullet_rect.left > SCREEN_WIDTH:
            bullets.remove(bullet)

    # 8. 描画処理
    screen.fill(WHITE) 
    
    for block in block_rects:
        pg.draw.rect(screen, BROWN, block)
        
    screen.blit(player_image_current, player_rect) 
    
    # ★★★ 頭上に次の攻撃タイプを描画 ★★★
    attack_text = str(current_attack_type)
    
    if current_attack_type == 1: text_color = YELLOW_TEXT
    elif current_attack_type == 2: text_color = BLUE_TEXT
    elif current_attack_type == 3: text_color = RED_TEXT
    else: text_color = CYAN_TEXT 
        
    text_surface = attack_font.render(attack_text, True, text_color, WHITE)
    
    text_rect = text_surface.get_rect()
    text_rect.centerx = player_rect.centerx
    text_rect.bottom = player_rect.top - 5 
    
    screen.blit(text_surface, text_rect)
    # ★★★★★★★★★★★★★★★★★★★★★★★

    # ★★★ 弾の描画 (画像を使用) ★★★
    for bullet in bullets:
        bullet_rect = bullet[0]
        bullet_image_to_draw = bullet[1] # 画像はリストの2番目 (index 1)
        
        screen.blit(bullet_image_to_draw, bullet_rect)
    # ★★★★★★★★★★★★★★

    pg.display.flip()
    
    clock.tick(60) 

pg.quit()