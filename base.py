import pygame
import os
import time

# 1. 定数と初期設定
pygame.init()
# サウンドミキサーを明示的に初期化（周波数、ビット深度、チャンネル数を指定）
pygame.mixer.quit()  # 一度終了
pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
os.chdir(os.path.dirname(os.path.abspath(__file__)))
TILE_SIZE = 40
GRAVITY = 0.8         # 重力
JUMP_STRENGTH = -15   # ジャンプ力 (Y軸は上がマイナス)
PLAYER_SPEED = 5      # 左右の移動速度

# 色の定義
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (50, 200, 50)   # プレイヤーの色
BROWN = (139, 69, 19)   # ブロックの色
RED = (255, 0, 0)       # 爆発エフェクトの色
ORANGE = (255, 165, 0)  # 爆発エフェクトの色

# ========================================
# 個人実装: ボムコピー能力システム (C0C24001)
# カービィが敵を吸い込んでコピーする能力として実装
# ========================================
C0C24001_BOMB_FUSE_TIME = 3.0  # 爆弾の導火線の時間(秒)
C0C24001_BOMB_EXPLOSION_DURATION = 0.5  # 爆発エフェクトの表示時間(秒)
C0C24001_BOMB_EXPLOSION_RADIUS = TILE_SIZE * 3  # 爆発範囲の半径

# 画面設定
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("2Dアクションゲーム デモ")
clock = pygame.time.Clock()

# 2. ステージデータ (0=空, 1=ブロック)
# 画面下部が地面、途中に浮島があるマップ
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
# (ゲーム開始時に一度だけ計算する)
block_rects = []
for y, row in enumerate(map_data):
    for x, tile_type in enumerate(row):
        if tile_type == 1:
            # (x座標, y座標, 幅, 高さ) のRectを作成
            block_rects.append(pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE))

# 3.5 ボムコピー能力システムの定義
# ========================================
# 個人実装機能: ボムコピー能力 (C0C24001)
# カービィが敵を吸い込んでコピーする能力として実装
# ========================================

class C0C24001_BombAbility:
    """ボムコピー能力クラス (C0C24001実装)
    
    カービィが爆弾を持つ敵を吸い込んだ後に使えるようになる能力
    
    使い方:
    1. 他のメンバーの吸い込みシステムから activate() を呼ぶ
    2. プレイヤーがBキーを押したら use_ability() を呼ぶ
    3. 返り値の爆弾オブジェクトを bombs リストに追加
    """
    def __init__(self):
        self.has_ability = False  # ボム能力を持っているか
        
    def activate(self):
        """ボム能力を取得(敵を吸い込んだ時に呼ばれる)"""
        self.has_ability = True
        print("【ボム能力を取得!】")
        
    def deactivate(self):
        """ボム能力を失う"""
        self.has_ability = False
        print("【ボム能力を失った】")
        
    def use_ability(self, player_pos, player_facing_right, ability_type="place"):
        """ボム能力を使用
        
        Args:
            player_pos: プレイヤーの位置 (rect)
            player_facing_right: プレイヤーの向き
            ability_type: "place"(設置), "throw"(投擲), "kick"(キック)
            
        Returns:
            爆弾オブジェクト または None
        """
        if not self.has_ability:
            return None
            
        # 爆弾を生成して返す
        if ability_type == "place":
            bomb_x = player_pos.centerx - TILE_SIZE // 2
            bomb_y = player_pos.bottom - TILE_SIZE
            return C0C24001_BombProjectile(bomb_x, bomb_y, velocity_x=0, velocity_y=1)
        elif ability_type == "throw":
            bomb_x = player_pos.centerx - TILE_SIZE // 2
            bomb_y = player_pos.centery - TILE_SIZE // 2
            throw_speed_x = 10 if player_facing_right else -10
            throw_speed_y = -8
            return C0C24001_BombProjectile(bomb_x, bomb_y, velocity_x=throw_speed_x, velocity_y=throw_speed_y)
        
        return None

class C0C24001_BombProjectile:
    """爆弾プロジェクタイルクラス (C0C24001実装)
    
    ボム能力で生成される爆弾オブジェクト
    
    実装機能:
    - 物理演算(重力、跳ね返り、摩擦)
    - 爆発タイマーとエフェクト
    - GIFアニメーション表示
    """
    def __init__(self, x, y, velocity_x=0, velocity_y=0):
        self.rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)
        self.placed_time = time.time()  # 設置時刻
        self.is_exploded = False  # 爆発したか
        self.explosion_time = None  # 爆発時刻
        self.velocity_x = velocity_x  # X方向の速度
        self.velocity_y = velocity_y  # Y方向の速度
        self.on_ground = False  # 地面に接地しているか
        
    def update(self, block_rects):
        """爆弾の状態を更新"""
        current_time = time.time()
        
        # まだ爆発していない場合、時間経過をチェック
        if not self.is_exploded:
            if current_time - self.placed_time >= C0C24001_BOMB_FUSE_TIME:
                self.is_exploded = True
                self.explosion_time = current_time
                return True  # 爆発した
            
            # 速度がある場合、爆弾を移動させる
            if self.velocity_x != 0 or self.velocity_y != 0:
                # 重力を適用
                self.velocity_y += GRAVITY * 0.5  # 爆弾用の重力（少し弱め）
                
                # X方向の移動
                self.rect.x += self.velocity_x
                
                # X方向の衝突チェック（壁で跳ね返る）
                for block in block_rects:
                    if self.rect.colliderect(block):
                        if self.velocity_x > 0:  # 右に移動中
                            self.rect.right = block.left
                            self.velocity_x = -self.velocity_x * 0.5  # 跳ね返る（減衰）
                        elif self.velocity_x < 0:  # 左に移動中
                            self.rect.left = block.right
                            self.velocity_x = -self.velocity_x * 0.5
                
                # 画面端で跳ね返る
                if self.rect.left < 0:
                    self.rect.left = 0
                    self.velocity_x = -self.velocity_x * 0.5
                elif self.rect.right > SCREEN_WIDTH:
                    self.rect.right = SCREEN_WIDTH
                    self.velocity_x = -self.velocity_x * 0.5
                
                # Y方向の移動
                self.rect.y += self.velocity_y
                
                # Y方向の衝突チェック
                self.on_ground = False
                for block in block_rects:
                    if self.rect.colliderect(block):
                        if self.velocity_y > 0:  # 落下中
                            self.rect.bottom = block.top
                            self.velocity_y = -self.velocity_y * 0.3  # 少し跳ねる
                            self.on_ground = True
                            # 摩擦で減速
                            self.velocity_x *= 0.9
                            if abs(self.velocity_x) < 0.5:
                                self.velocity_x = 0
                        elif self.velocity_y < 0:  # 上昇中
                            self.rect.top = block.bottom
                            self.velocity_y = 0
                
                # 画面下端チェック
                if self.rect.bottom > SCREEN_HEIGHT:
                    self.rect.bottom = SCREEN_HEIGHT
                    self.velocity_y = 0
                    self.on_ground = True
                    self.velocity_x *= 0.9
                    if abs(self.velocity_x) < 0.5:
                        self.velocity_x = 0
                        
        return False
    
    def is_explosion_finished(self):
        """爆発エフェクトが終了したか"""
        if self.is_exploded and self.explosion_time:
            return time.time() - self.explosion_time >= C0C24001_BOMB_EXPLOSION_DURATION
        return False
    
    def draw(self, surface, bomb_image, explosion_frames):
        """爆弾または爆発エフェクトを描画"""
        if self.is_exploded:
            # 爆発エフェクトを描画
            if explosion_frames and len(explosion_frames) > 0:
                # アニメーションフレームを表示
                elapsed_time = time.time() - self.explosion_time
                # フレームレート: 0.05秒ごとに切り替え(20fps)
                frame_index = int(elapsed_time / 0.05) % len(explosion_frames)
                current_frame = explosion_frames[frame_index]
                
                explosion_center = self.rect.center
                explosion_rect = current_frame.get_rect(center=explosion_center)
                surface.blit(current_frame, explosion_rect.topleft)
            else:
                # 画像がない場合は円で表現
                explosion_center = self.rect.center
                # 外側の円(赤)
                pygame.draw.circle(surface, RED, explosion_center, C0C24001_BOMB_EXPLOSION_RADIUS, 0)
                # 中間の円(オレンジ)
                pygame.draw.circle(surface, ORANGE, explosion_center, C0C24001_BOMB_EXPLOSION_RADIUS * 2 // 3, 0)
                # 内側の円(黄色)
                pygame.draw.circle(surface, (255, 255, 0), explosion_center, C0C24001_BOMB_EXPLOSION_RADIUS // 3, 0)
        else:
            # 爆弾画像を描画
            surface.blit(bomb_image, self.rect.topleft)
    
    def get_explosion_rect(self):
        """爆発範囲の矩形を返す"""
        if self.is_exploded:
            center = self.rect.center
            explosion_rect = pygame.Rect(
                center[0] - C0C24001_BOMB_EXPLOSION_RADIUS,
                center[1] - C0C24001_BOMB_EXPLOSION_RADIUS,
                C0C24001_BOMB_EXPLOSION_RADIUS * 2,
                C0C24001_BOMB_EXPLOSION_RADIUS * 2
            )
            return explosion_rect
        return None

# 4. プレイヤー設定
# 画像を読み込み、ステージに合うサイズにスケーリング
# img/bom2.png を使う。見つからない・読み込めない場合は四角形で代替表示する。
PLAYER_SIZE = TILE_SIZE * 3.0  # プレイヤーサイズを大きめに（タイルの3.0倍）
try:
    player_image_original = pygame.image.load(os.path.join("img", "bom2.png")).convert_alpha()
    # ステージのタイルサイズに合わせてスケーリング（透過を保持するため smoothscale を使用）
    player_image_original = pygame.transform.smoothscale(player_image_original, (PLAYER_SIZE, PLAYER_SIZE))
except Exception:
    # 画像がない場合は幅=TILE_SIZE//2, 高さ=TILE_SIZE の透明サーフェスに色を付ける
    player_image_original = pygame.Surface((TILE_SIZE // 2, TILE_SIZE), pygame.SRCALPHA)
    player_image_original.fill(GREEN)

# 右向きと左向きの画像を用意（flip も透過を保持）
player_image_right = player_image_original
player_image_left = pygame.transform.flip(player_image_original, True, False)
player_image = player_image_right  # デフォルトは右向き

# プレイヤーの当たり判定用のRect(画像より少し小さめにして足元を調整)
player_rect = pygame.Rect(100, 100, PLAYER_SIZE * 0.6, PLAYER_SIZE * 0.5)
player_velocity_y = 0  # プレイヤーの垂直方向の速度
is_on_ground = False     # 地面（ブロック）に接地しているか
player_move_left = False # 左に移動中か
player_move_right = False# 右に移動中か
player_facing_right = True # プレイヤーの向き（True=右向き, False=左向き）

# ========================================
# 個人実装: 爆弾画像の読み込み (C0C24001)
# ========================================
try:
    c0c24001_bomb_image = pygame.image.load(os.path.join("img", "bom3.png")).convert_alpha()
    c0c24001_bomb_image = pygame.transform.smoothscale(c0c24001_bomb_image, (TILE_SIZE, TILE_SIZE))
except Exception:
    # 画像がない場合は黒い円で代替
    c0c24001_bomb_image = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
    pygame.draw.circle(c0c24001_bomb_image, BLACK, (TILE_SIZE // 2, TILE_SIZE // 2), TILE_SIZE // 2)

# 爆発エフェクト画像の読み込み（GIFアニメーション対応）
try:
    from PIL import Image
    # PILでGIFを読み込んでフレームを抽出
    gif_path = os.path.join("img", "bakuha.gif")
    pil_gif = Image.open(gif_path)
    
    c0c24001_explosion_frames = []
    c0c24001_explosion_size = C0C24001_BOMB_EXPLOSION_RADIUS * 2
    
    # 全フレームを読み込む
    try:
        frame_index = 0
        while True:
            pil_gif.seek(frame_index)
            # PILイメージをPygameサーフェスに変換
            frame = pil_gif.convert("RGBA")
            frame_data = frame.tobytes()
            pygame_surface = pygame.image.fromstring(frame_data, frame.size, "RGBA")
            # スケーリング
            pygame_surface = pygame.transform.smoothscale(pygame_surface, (c0c24001_explosion_size, c0c24001_explosion_size))
            c0c24001_explosion_frames.append(pygame_surface)
            frame_index += 1
    except EOFError:
        pass  # 全フレーム読み込み完了
    
    if c0c24001_explosion_frames:
        print(f"爆発エフェクト画像を読み込みました: img/bakuha.gif ({len(c0c24001_explosion_frames)}フレーム)")
    else:
        c0c24001_explosion_frames = None
        print("GIFフレームの読み込みに失敗しました")
        
except ImportError:
    c0c24001_explosion_frames = None
    print("警告: Pillow (PIL) がインストールされていません")
    print("GIFアニメーションを使用するには 'pip install pillow' を実行してください")
    print("デフォルトの円形エフェクトを使用します。")
except Exception as e:
    c0c24001_explosion_frames = None
    print(f"爆発エフェクト画像の読み込みに失敗: {e}")
    print("デフォルトの円形エフェクトを使用します。")

# 背景画像の読み込み
try:
    background_image = pygame.image.load(os.path.join("img", "haikei.jpg")).convert()
    # 画面サイズに合わせてスケーリング
    background_image = pygame.transform.scale(background_image, (SCREEN_WIDTH, SCREEN_HEIGHT))
    print("背景画像を読み込みました: img/haikei.jpg")
except Exception as e:
    # 画像がない場合は黒背景
    background_image = None
    print(f"背景画像の読み込みに失敗: {e}")
    print("黒背景を使用します。")

# 爆発音の読み込み
explosion_sound = None
sound_paths = [
    os.path.join("bgm", "bom.mp3"),
    os.path.join("bgm", "bom.wav"),
    os.path.join("img", "bom.mp3"),
    os.path.join("img", "bom.wav"),
    "bom.mp3",
    "bom.wav"
]

for sound_path in sound_paths:
    try:
        if os.path.exists(sound_path):
            explosion_sound = pygame.mixer.Sound(sound_path)
            print(f"爆発音を読み込みました: {sound_path}")
            break
    except Exception as e:
        print(f"音声ファイル {sound_path} の読み込みに失敗: {e}")

if explosion_sound is None:
    print("警告: 爆発音ファイルが見つかりません。")
    print("bgm/bom.mp3 または img/bom.wav を配置してください。")

# BGM（背景音楽）の読み込みと再生
print("BGMの読み込みを開始...")
# 複数の形式を試す（OGGを優先）
bgm_files = [
    ("bgm", "music.ogg"),   # OGG形式（推奨）
    ("bgm", "music.wav"),   # WAV形式
    ("bgm", "music.mp3"),   # MP3形式（互換性に問題がある場合あり）
]

bgm_loaded = False
for folder, filename in bgm_files:
    bgm_path = os.path.join(folder, filename)
    if os.path.exists(bgm_path):
        print(f"ファイルが見つかりました: {bgm_path}")
        try:
            pygame.mixer.music.load(bgm_path)
            pygame.mixer.music.set_volume(0.3)
            pygame.mixer.music.play(-1)
            print(f"✓ BGMの再生を開始しました: {filename}")
            bgm_loaded = True
            break
        except pygame.error as e:
            print(f"✗ {filename} の読み込みに失敗: {e}")
            continue

if not bgm_loaded:
    print("=" * 60)
    print("【BGMが再生できませんでした】")
    print("MP3ファイルがPygameと互換性がない可能性があります。")
    print("")
    print("解決方法：")
    print("1. https://convertio.co/ja/mp3-ogg/ で変換")
    print("2. music.mp3 を OGG形式に変換")
    print("3. 変換したファイル(music.ogg)をbgmフォルダに保存")
    print("")
    print("ゲームは音楽なしで続行します。")
    print("=" * 60)

# ========================================
# 個人実装: 爆弾能力システム (C0C24001)
# ========================================
# 爆弾能力マネージャー（カービィのコピー能力として管理）
c0c24001_bomb_ability = C0C24001_BombAbility()

# テスト用: 能力を初期状態で有効化（実際のゲームでは敵を吸い込んで取得）
# マージ時は、吸い込み機能実装者がc0c24001_bomb_ability.activate()を呼び出す
c0c24001_bomb_ability.activate()
print("【テストモード】爆弾能力が有効化されました。マージ時はこの行を削除してください。")

# 爆弾リスト（設置された爆弾を管理）
c0c24001_bombs = []

# 5. ゲームループ
running = True
while running:
    
    # 6. イベント処理 (キー操作など)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        # キーが押された時
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:
                player_move_left = True
            if event.key == pygame.K_RIGHT:
                player_move_right = True
            if event.key == pygame.K_SPACE and is_on_ground:
                player_velocity_y = JUMP_STRENGTH # 上向きの速度を与える
                is_on_ground = False
            
            # ========================================
            # 個人実装: 爆弾操作 (C0C24001)
            # ========================================
            if event.key == pygame.K_b:
                # 爆弾能力を持っている場合のみ使用可能
                if c0c24001_bomb_ability.has_ability:
                    # Shiftキーが押されている場合は投擲、それ以外は設置
                    keys = pygame.key.get_pressed()
                    if keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]:
                        # 爆弾を投擲（前方に投げる）
                        bomb_x = player_rect.centerx - TILE_SIZE // 2
                        bomb_y = player_rect.centery - TILE_SIZE // 2
                        # プレイヤーの向きに応じて速度を設定
                        throw_speed_x = 10 if player_facing_right else -10
                        throw_speed_y = -8  # 上向きに投げる
                        new_bomb = C0C24001_BombProjectile(bomb_x, bomb_y, velocity_x=throw_speed_x, velocity_y=throw_speed_y)
                        c0c24001_bombs.append(new_bomb)
                    else:
                        # 爆弾を設置（プレイヤーの足元に設置し、重力で落下）
                        bomb_x = player_rect.centerx - TILE_SIZE // 2
                        bomb_y = player_rect.bottom - TILE_SIZE
                        # 設置時に初期速度を設定（重力で落下させる）
                        new_bomb = C0C24001_BombProjectile(bomb_x, bomb_y, velocity_x=0, velocity_y=1)
                        c0c24001_bombs.append(new_bomb)
            if event.key == pygame.K_k:
                # 近くの爆弾をキック
                for bomb in c0c24001_bombs:
                    if not bomb.is_exploded and abs(bomb.velocity_x) < 1:  # 静止している爆弾のみ
                        # プレイヤーとの距離をチェック
                        distance = ((player_rect.centerx - bomb.rect.centerx) ** 2 + 
                                   (player_rect.centery - bomb.rect.centery) ** 2) ** 0.5
                        if distance < TILE_SIZE * 2:  # 2タイル以内
                            # プレイヤーの向きに応じて蹴る
                            kick_speed = 8 if player_facing_right else -8
                            bomb.velocity_x = kick_speed
                            bomb.velocity_y = -3  # 少し浮かせる
                            break  # 1つだけキック
        
        # キーが離された時
        if event.type == pygame.KEYUP:
            if event.key == pygame.K_LEFT:
                player_move_left = False
            if event.key == pygame.K_RIGHT:
                player_move_right = False

    # 7. プレイヤーのロジック更新 (移動と当たり判定)
    
    # --- 左右の移動と当たり判定 ---
    player_movement_x = 0
    if player_move_left:
        player_movement_x -= PLAYER_SPEED
        if player_facing_right:  # 右向きから左向きに変更
            player_image = player_image_left
            player_facing_right = False
    if player_move_right:
        player_movement_x += PLAYER_SPEED
        if not player_facing_right:  # 左向きから右向きに変更
            player_image = player_image_right
            player_facing_right = True
    
    player_rect.x += player_movement_x # まずX方向に動かす
    
    # X方向の衝突チェック
    for block in block_rects:
        if player_rect.colliderect(block):
            if player_movement_x > 0: # 右に移動中に衝突
                player_rect.right = block.left # 右端をブロックの左端に合わせる
            elif player_movement_x < 0: # 左に移動中に衝突
                player_rect.left = block.right # 左端をブロックの右端に合わせる

    # --- 垂直方向（重力・ジャンプ）の移動と当たり判定 ---
    player_velocity_y += GRAVITY # 重力を速度に加算
    player_rect.y += player_velocity_y # Y方向に動かす
    
    # Y方向の衝突チェック
    is_on_ground = False # 毎フレーム「接地していない」と仮定
    for block in block_rects:
        if player_rect.colliderect(block):
            if player_velocity_y > 0: # 落下中に衝突
                player_rect.bottom = block.top # 足元をブロックの上端に合わせる
                player_velocity_y = 0 # 落下速度をリセット
                is_on_ground = True   # 接地フラグを立てる
            elif player_velocity_y < 0: # ジャンプ中に衝突
                player_rect.top = block.bottom # 頭をブロックの下端に合わせる
                player_velocity_y = 0 # 上昇速度をリセット（頭を打った）

    # --- 爆弾の更新処理 (C0C24001) ---
    # 爆発した爆弾、エフェクトが終了した爆弾を削除
    c0c24001_bombs_to_remove = []
    for bomb in c0c24001_bombs:
        if bomb.update(block_rects):  # 爆発した場合（block_rectsを渡す）
            # 爆発音を再生
            if explosion_sound:
                explosion_sound.play()
            # 将来的にここで敵やプレイヤーへのダメージ処理を追加
            pass
        
        # 爆発エフェクトが終了したら削除リストに追加
        if bomb.is_explosion_finished():
            c0c24001_bombs_to_remove.append(bomb)
    
    # 削除リストの爆弾を除去
    for bomb in c0c24001_bombs_to_remove:
        c0c24001_bombs.remove(bomb)

    # 8. 描画処理
    # 背景画像を描画（画像がある場合）または黒で塗りつぶし
    if background_image:
        screen.blit(background_image, (0, 0))
    else:
        screen.fill(BLACK)
    
    # ステージ（ブロック）を描画
    for block in block_rects:
        pygame.draw.rect(screen, BROWN, block)
    
    # 爆弾を描画 (C0C24001)
    for bomb in c0c24001_bombs:
        bomb.draw(screen, c0c24001_bomb_image, c0c24001_explosion_frames)
        
    # プレイヤーを描画(画像を使う)
    # 当たり判定Rectの中央下部に画像を配置(足元を合わせる)
    player_draw_x = player_rect.centerx - PLAYER_SIZE // 2
    player_draw_y = player_rect.bottom - PLAYER_SIZE * 0.75  # 地面に少しめり込ませて足をしっかり接地
    screen.blit(player_image, (player_draw_x, player_draw_y))
    
    # 画面を更新
    pygame.display.flip()
    
    # 9. FPS (フレームレート) の制御
    clock.tick(60) # 1秒間に60回ループが回るように調整

# ループが終了したらPygameを終了
pygame.quit()