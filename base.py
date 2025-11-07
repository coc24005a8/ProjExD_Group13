import pygame as pg
import os
import sys
import random

#ーーーーーーーーー1.定数と初期設定ーーーーーーーーー
import time

#あとで調整！！！！！
# サウンドミキサーを明示的に初期化（周波数、ビット深度、チャンネル数を指定）
pg.mixer.quit()  # 一度終了
pg.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
os.chdir(os.path.dirname(os.path.abspath(__file__)))

SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600 # 画面のサイズ
LEFT_BOUND, RIGHT_BOUND = SCREEN_WIDTH // 3, SCREEN_WIDTH * 2 // 3 # スクロール判定
TILE_SIZE_X, TILE_SIZE_Y = 100, 40 # タイルのサイズ
ADD_STAGE_BLOCK = 100 # ステージの拡張幅
GRAVITY = 0.8         # 重力
JUMP_STRENGTH = -15   # ジャンプ力 (Y軸は上がマイナス)
HOVER_AIR_TIME = 60   # ホバーエフェクトの表示時間(フレーム単位)
PLAYER_SPEED = 10      # 左右の移動速度
PLAYER_HP = 5
NO_DAMAGE_TIME = 120 # 無敵時間(フレーム単位)
PLAYER_POWER = 10 # プレイヤーの攻撃力
ENEMY_NUM = 1         # 敵の数
ENEMY_SPEED = 1
BULLET_SPEED = 10 
SUPER_ATTACK_CHANCE = 5 

#-------------------------------- 一旦 -------------------------------
RED_TEXT = (255, 0, 0)      
BLUE_TEXT = (0, 0, 255)     
YELLOW_TEXT = (255, 255, 0) 
CYAN_TEXT = (0, 255, 255)   

# 頭上に表示する数字用のフォント
# try:
#     attack_font = pg.font.SysFont(None, 40)
# except Exception as e:
#     print(f"フォントの読み込みに失敗: {e}。デフォルトフォントを使用します。")
#     attack_font = pg.font.Font(None, 40) 

# ----------------------------------------------------------------
# ========================================
# 個人実装: 爆弾画像の読み込み (C0C24001)
# ========================================
try:
    c0c24001_bomb_image = pg.image.load(os.path.join("img", "bom3.png")).convert_alpha()
    c0c24001_bomb_image = pg.transform.smoothscale(c0c24001_bomb_image, (TILE_SIZE, TILE_SIZE))
except Exception:
    # 画像がない場合は黒い円で代替
            # c0c24001_bomb_image = pg.Surface((TILE_SIZE, TILE_SIZE), pg.SRCALPHA)
            # pg.draw.circle(c0c24001_bomb_image, BLACK, (TILE_SIZE // 2, TILE_SIZE // 2), TILE_SIZE // 2)
        pass

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
            # PILイメージをpgサーフェスに変換
            frame = pil_gif.convert("RGBA")
            frame_data = frame.tobytes()
            pg_surface = pg.image.fromstring(frame_data, frame.size, "RGBA")
            # スケーリング
            pg_surface = pg.transform.smoothscale(pg_surface, (c0c24001_explosion_size, c0c24001_explosion_size))
            c0c24001_explosion_frames.append(pg_surface)
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
    background_image = pg.image.load(os.path.join("img", "haikei.jpg")).convert()
    # 画面サイズに合わせてスケーリング
    background_image = pg.transform.scale(background_image, (SCREEN_WIDTH, SCREEN_HEIGHT))
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
            explosion_sound = pg.mixer.Sound(sound_path)
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
            pg.mixer.music.load(bgm_path)
            pg.mixer.music.set_volume(0.3)
            pg.mixer.music.play(-1)
            print(f"✓ BGMの再生を開始しました: {filename}")
            bgm_loaded = True
            break
        except pg.error as e:
            print(f"✗ {filename} の読み込みに失敗: {e}")
            continue

if not bgm_loaded:
    print("=" * 60)
    print("【BGMが再生できませんでした】")
    print("MP3ファイルがpgと互換性がない可能性があります。")
    print("")
    print("解決方法：")
    print("1. https://convertio.co/ja/mp3-ogg/ で変換")
    print("2. music.mp3 を OGG形式に変換")
    print("3. 変換したファイル(music.ogg)をbgmフォルダに保存")
    print("")
    print("ゲームは音楽なしで続行します。")
    print("=" * 60)
#ーーーーーーーーーーーーーーーーーーーーーーーーーー
#---まだ
def start_page(screen: pg.surface, clock: pg.time.Clock) -> int:
    """
    スタート画面を表示する関数
    引数: スクリーンsurface, pgのクロック  
    戻り値: int(開始なら0, 終了なら-1)
    """
    bg_img = pg.image.load("fig/night_plain_bg.png")
    title = Text("GO KOUKATON (TUT)", 80, (100, 300))
    start_button = Text("Start", 80, (100, 100))
    end_button = Text("Quit", 80, (500, 100))

    mouse_x, mouse_y = -1000, -1000 # マウス位置をあり得ない位置で初期化
    while True:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                return -1
        
            if event.type == pg.MOUSEBUTTONDOWN:
                mouse_x, mouse_y = event.pos # マウスの位置を取得
 
        screen.blit(bg_img, (0, 0))
        screen.blit(title.txt, (title.x, title.y))
        screen.blit(start_button.txt, (start_button.x, start_button.y))
        screen.blit(end_button.txt, (end_button.x, end_button.y))
        
        if start_button.x < mouse_x < start_button.x + start_button.width and end_button.y < mouse_y < end_button.y + end_button.height:
            return 0 # スタートボタンをクリック
        if end_button.x < mouse_x < end_button.x + end_button.width and end_button.y < mouse_y < end_button.y + end_button.height:
            return -1 # Quitボタンをクリック
                
        pg.display.update()
        clock.tick(60)



# 画面設定
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
C0C24001_BOMB_EXPLOSION_RADIUS = TILE_SIZE_X * 3  # 爆発範囲の半径


#さあ解消を始めよう
# enemy_image = pygame.image.load("fig/syujinkou_yoko.png")
# enemy_image = pygame.transform.rotozoom(enemy_image, 0, 0.1) # テスト用の敵を設定
# enemy_rect = enemy_image.get_rect()
# enemy_rect.center = (300,300)
# enemy_size = 1.0

def gameover(screen: pg.surface, clock: pg.time.Clock) -> int:
    """
    ゲームオーバー画面を表示する関数
    引数: スクリーンsurface, pgのクロック
    戻り値: int(開始なら0, 終了なら-1)    
    """
    bg_img = pg.image.load("fig/night_plain_bg.png")
    txt = Text("Game Over", 80, (100, 300))
    retry = Text("Retry", 80, (100, 100))
    quit = Text("Quit", 80, (500, 100))

    mouse_x, mouse_y = -1000, -1000 # マウス位置をあり得ない位置で初期化

    while True:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                return -1
        
            if event.type == pg.MOUSEBUTTONDOWN:
                mouse_x, mouse_y = event.pos # マウス位置を取得
 
        screen.blit(bg_img, (0, 0))
        screen.blit(txt.txt, (txt.x, txt.y))
        screen.blit(retry.txt, (retry.x, retry.y))
        screen.blit(quit.txt, (quit.x, quit.y))
        
        if retry.x < mouse_x < retry.x + retry.width and retry.y < mouse_y < retry.y + retry.height:
            return 0 # リトライを押された
        if quit.x < mouse_x < quit.x + quit.width and quit.y < mouse_y < quit.y + quit.height:
            return -1 # 終了を押された
        
        pg.display.update()
        clock.tick(60)
#ーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーー

#ーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーー
def game_clear(screen: pg.surface, clock: pg.time.Clock) -> int:
    """
    クリア画面を表示する関数
    引数: スクリーンsurface, pgのクロック
    戻り値: int(再プレイなら0, 終了なら-1)
    """
    bg_img = pg.image.load("fig/night_plain_bg.png")
    txt = Text("Game Clear", 80, (100, 300))
    retry = Text("Retry", 80, (100, 100))
    quit = Text("Quit", 80, (500, 100))

    mouse_x, mouse_y = -1000, -1000 # マウス位置をあり得ない位置で初期化

    while True:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                return -1
        
            if event.type == pg.MOUSEBUTTONDOWN:
                mouse_x, mouse_y = event.pos # マウス位置を取得
 
        screen.blit(bg_img, (0, 0))
        screen.blit(txt.txt, (txt.x, txt.y))
        screen.blit(retry.txt, (retry.x, retry.y))
        screen.blit(quit.txt, (quit.x, quit.y))
        
        if retry.x < mouse_x < retry.x + retry.width and retry.y < mouse_y < retry.y + retry.height:
            return 0 # リトライを押された
        if quit.x < mouse_x < quit.x + quit.width and quit.y < mouse_y < quit.y + quit.height:
            return -1 # 終了を押された
        
        pg.display.update()
        clock.tick(60)
#------

def extend(map_data: list[list[int]], add_stage_width: int, probs: list[int]) -> list[list[int]]:
    """
    ステージを拡張する関数。地面ブロックとして追加する
    内容: 下2マスは確定で地面。それ以降は拡張幅まで、下のマスが地面 and 1つ前の下のマスが地面 の時に生成
    引数: 初期マップデータ, 追加するブロックの数, 生成する確率
    戻り値: 拡張したマップのリスト
    """  
    for i in range(len(map_data)):
        layer = -1 * (i + 1)  # 下の段から選択
        if i < 2:
            for j in range(add_stage_width):  # 下2段は地面ブロック(1)
                map_data[layer].append(1)
        elif i < len(probs):
            for j in range(add_stage_width):
                pos = len(map_data[layer]) - 1  # 現時点の自身の段のブロック数-1 が自身の位置
                generate_prob = random.randint(0,100) / 100 
                if generate_prob < probs[layer] and map_data[layer + 1][pos] == 1 and map_data[layer + 1][pos + 1] == 1:
                    map_data[layer].append(1)
                else:
                    map_data[layer].append(0)
        else:
            for j in range(add_stage_width):  # 地面を生成しない段
                map_data[layer].append(0)
    return map_data

def ground_surface(map_data: list[list[int]]) -> list[list[int]]:
    """
    地面ブロックの上に地表ブロックを配置する関数
    内容: 下のマスが地面 and 自分のマスが無 の時に生成
    引数: 現在のマップデータ
    戻り値: 地表追加後のマップデータ    
    """
    for i in range(len(map_data) - 2, 0, -1): #上段から調べる
        for j in range(len(map_data[0])):  
            if map_data[i + 1][j] == 1 and map_data[i][j] == 0:
                map_data[i][j] = 2
    return map_data

def make_float_land(map_data: list[list[int]], add_range: tuple[int], num: int) -> list[list[int]]:
    """
    浮島を生成する関数
    内容: 自身が無の時、下のマスが無 and 2マス下が無 の時に浮島を生成
    引数: 現在のマップ, 浮島を生成するレイヤー, 生成個数 
    戻り値: 浮島を追加したマップ
    """
    maked_floatland = 0 
    while maked_floatland <= num:
        width = random.randrange(2,4) # 生成する浮島の長さ
        X = random.randrange(10, len(map_data[0])) # 浮島のX座標
        Y = random.randrange(add_range[0], add_range[1] + 1) #浮島のY座標
        if map_data[len(map_data) - Y][X] == 0 and map_data[len(map_data) - Y + 1][X] == 0 and map_data[len(map_data) - Y + 2][X] == 0:
            maked_floatland += 1
            if X + width >= len(map_data[0]): # 生成位置がマップ範囲を超えてたらずらす
                X = len(map_data) - width
            for j in range(width):
                map_data[len(map_data) - Y][X + j] = 3
    
    for i in range(2):
        map_data[len(map_data)- 8][len(map_data[0]) - i - 1] = 3
    return map_data

#---修正
def walled(instance: object, blocks: list[tuple[object, int]]) -> None:
    """
    壁衝突判定を行う関数
    内容: 壁に衝突したとき、自身の位置を壁端に合わせる。
    引数: 衝突判定を行うオブジェクト, 衝突するブロックを保持したリスト
    """
    for block in blocks:
        if instance.rect.colliderect(block): 
            if instance.vx > 0: # 右に移動中に衝突
                instance.rect.right = block.left # 右端をブロックの左端に合わせる
            elif instance.vx < 0: # 左に移動中に衝突
                instance.rect.left = block.right # 左端をブロックの右端に合わせる
#-------

#---修正
def gravity(instance: object, blocks: list[tuple[object, int]]) -> None:
    """
    重力を適用し、地面との衝突判定を行う関数
    内容: 地面にぶつかった際、y方向の速度を0にし、座標を地面の上に合わせる
    引数: 重力を適用するオブジェクト, ブロックのリスト
    """
    instance.vy += GRAVITY # 重力を速度に加算
    instance.rect.y += instance.vy # Y方向に動かす
    instance.is_on_ground = False # 毎フレーム「接地していない」と仮定
    
    for block in blocks:
        if instance.rect.colliderect(block):
                if instance.vy > 0: # 落下中に衝突
                    instance.rect.bottom = block.top # 足元をブロックの上端に合わせる
                    instance.hover_num = 0
                    instance.vy = 0 # 落下速度をリセット
                    instance.is_on_ground = True   # 接地フラグを立てる
                elif instance.vy < 0: # ジャンプ中に衝突
                    instance.rect.top = block.bottom # 頭をブロックの下端に合わせる
                    instance.vy = 0 # 上昇速度をリセット（頭を打った）
#------

def no_damage(instance: object, flag: int = 0) -> None:
    """
    無敵時間中の処理を行う関数
    内容: 無敵時間中の画像表示、無敵時間の減算
    引数: 無敵時間を適用するインスタンス, フラグ(0なら無敵時間中, 1なら無敵になる前)
    """
    if instance.no_damage_time == 0 and flag == 1:
        instance.no_damage_time = NO_DAMAGE_TIME
    elif instance.no_damage_time > 0:
        if instance.no_damage_time % 10 == 0 and instance.no_damage_time % 20 != 0:
            instance.patarn = (instance.patarn[0], 0, "normal")
        elif instance.no_damage_time % 20 == 0:
            instance.patarn = (instance.patarn[0], 0, "no_damage")            
        instance.no_damage_time -= 1
    else:
        return
    
def camera_adjust(instance: object, camera_x: int, stage_width: int) -> int:
        if instance.rect.x - camera_x < LEFT_BOUND: # プレイヤーが左端
            camera_x = instance.rect.x - LEFT_BOUND # オブジェクトのずらし度を決定する。
        elif instance.rect.x - camera_x > RIGHT_BOUND: #プレイヤーが右端ならカメラの位置を右にずらす
            camera_x = instance.rect.x - RIGHT_BOUND 
        max_camera_x = stage_width * TILE_SIZE_X - SCREEN_WIDTH #カメラが右端を超えないように
        camera_x = max(0, min(camera_x, max_camera_x))
        
        return camera_x

class Assets:
    def __init__(self):
        self.bg = pg.image.load("fig/night_plain_bg.png")
        self.ground = pg.image.load("fig/ground2.png")
        self.weeds = pg.image.load("fig/weeds(extend).png")
        self.cloud = pg.image.load("fig/cloud(extend).png")

        self.init_map = [
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 3, 3, 0, 0, 0, 0, 3, 3, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3, 3, 3, 0, 0, 0, 0],
            [1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [1, 1, 1, 1, 1, 1, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
            [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
            [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
            [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
            [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
            [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
        ]
        self.probs = [0.5, 0.7, 0.9, 1.0, 1.0] # ブロックを生成する確率(左から上段)

class Text:
    def __init__(self, string: str, str_size: int, pos: tuple[int,int]) -> None:
        self.txt = pg.font.Font(None, str_size)
        self.txt = self.txt.render(string, True, (255, 255, 255))
        self.x = pos[0]
        self.y = pos[1]
        self.width = self.txt.get_width()
        self.height = self.txt.get_height()

#---修正
class Player(pg.sprite.Sprite):
    """
    操作キャラクターのクラス
    """
    def __init__(self):
        super().__init__()
        self.name = "normal"
        self.original = pg.image.load("fig/yoko1.png")
        # self.img = self.original
        self.flip = pg.transform.flip(self.original, True, False)
        self.punch = pg.image.load("fig/punch.png")
        self.imgs = [self.original, self.flip ]
        self.rect = self.imgs[0].get_rect()
        self.vx = 0
        self.vy = 0
        self.patarn = (1, 0, "normal")
        self.patarn_to_img = {(1, 0, "normal") : self.imgs[0], (-1, 0, "normal") : self.imgs[1],
                              (1, 0, "no_damage") : pg.transform.laplacian(self.imgs[0]), (-1, 0, "no_damage") : pg.transform.laplacian(self.imgs[1]),
                              (1, 0, "punch") : self.punch, (-1, 0, "punch"): pg.transform.flip(self.punch, True, False)
                              }

        self.hover_num = 0
        self.hp = PLAYER_HP
        self.no_damage_time = NO_DAMAGE_TIME
        self.power = PLAYER_POWER
        self.attacking = False

        self.is_on_ground = False
        self.move_left, self.move_right = False, False


    
    def update(self, stage_width: "int", all_blocks: "list[object]", floar_blocks: "list[object]", camera_x: "int") -> "int":
        """
        自身の座標を更新する関数
        内容: キーに合わせて自身が移動する。移動に合わせてカメラ座標も取得する
        戻り値: カメラ用の係数       
        """  
        if self.move_left:
            self.vx = -PLAYER_SPEED
            if self.attacking == True:
                self.patarn = (-1, 0, "punch")           
            else:
                self.patarn = (-1, 0, "normal")
        if self.move_right:
            self.vx = PLAYER_SPEED
            if self.attacking == True:
                self.patarn = (1, 0, "punch")
            else:
                self.patarn = (1, 0, "normal")

        self.rect.x += self.vx

        walled(self, all_blocks)
        gravity(self, floar_blocks)
        no_damage(self, 0)
        # camera_x = camera_adjust(self, camera_x, stage_width)
        # return camera_x

        if self.rect.x - camera_x < LEFT_BOUND: # プレイヤーが左端
            camera_x = self.rect.x - LEFT_BOUND # オブジェクトのずらし度を決定する。
        elif self.rect.x - camera_x > RIGHT_BOUND: #プレイヤーが右端ならカメラの位置を右にずらす
            camera_x = self.rect.x - RIGHT_BOUND 
        max_camera_x = stage_width * TILE_SIZE_X - SCREEN_WIDTH #カメラが右端を超えないように
        camera_x = max(0, min(camera_x, max_camera_x))
        
        return camera_x
    
    def hover(self) -> None:
        """
        ホバリングを行う関数
        内容: 上限まで連続して自身の上方速度を加算する。
        """
        if self.hover_num == 5:
            return
        self.vy += JUMP_STRENGTH
        self.hover_num += 1
        return
    
    # def no_damage(self,instance, flag = 0):
    #     if self.no_damage_time == 0 and flag == 1:
    #         self.no_damage_time = NO_DAMAGE_TIME
    #     elif self.no_damage_time > 0:
    #         if self.no_damage_time % 10 == 0 and self.no_damage_time % 20 != 0:
    #             self.dire = (self.dire[0], 0, 0)
    #         elif self.no_damage_time % 20 == 0:
    #             self.dire = (self.dire[0], 0, 1)            
    #         self.no_damage_time -= 1
    #     else:
    #         return
        
    def panch(self):
        attack = PlayerLeadAttack((50, 20), 600, "punch")
        self.patarn = (self.patarn[0], 0, "punch")
        self.attacking = True
        return attack

#---
class Absurb(pg.sprite.Sprite):
    def __init__(self, instance: object) -> None:
        """
        吸収判定を初期化する関数
        引数: 吸収機能を持つインスタンス
        """
        super().__init__()
        self.img = pg.image.load("fig/tatsumaki.png")
        self.img = pg.transform.rotozoom(self.img, 270, 0.05) #画像のサイズと向きを設定
        self.rect = self.img.get_rect()
        self.rect.center = ((instance.rect.centerx + 40, instance.rect.centery)) # 描写位置をプレイヤーのすぐ先に設定

    def update(self, instance: object) -> None:
        """
        吸収判定を移動させる関数
        引数: プレイヤーの位置を表す矩形
        """
        self.rect.centerx = instance.rect.centerx + 40 # 描写位置を再設定
        self.rect.centery = instance.rect.centery

class HoverAir(pg.sprite.Sprite):
    def __init__(self, instance, flag, flag_air_dire):
        super().__init__()
        self.image = pg.image.load("fig/jumped_air.png")
        self.image = [self.image, pg.transform.flip(self.image, True, False)][flag_air_dire]
        self.time = HOVER_AIR_TIME
        self.rect = self.image.get_rect()
        self.rect.x = instance.rect.centerx + instance.imgs[0].get_width() * flag
        self.rect.y = instance.rect.centery

    def update(self):
        self.time -= 1
        self.rect.y += 1
        if self.time == 0:
            self.kill()

# ==== 追加：炎の玉 & かーびー ====
class FireBall(pg.sprite.Sprite):
    """炎の玉：横に飛び、寿命で消える"""
    def __init__(self, x, y, direction):
        super().__init__()
        try:
            self.image = pg.image.load("fig/fire.jpg").convert_alpha()
            self.image = pg.transform.scale(self.image, (20, 20))
        except Exception:
            self.image = None  # 画像が無い場合は自前描画
        # rect は中心位置で受け取るようにする
        self.rect = pg.Rect(0, 0, 25, 25)
        self.rect.center = (x, y)
        self.speed = 12 * direction  # 水平速度
        # 垂直方向の物理 (重力 + バウンド)
        self.vy = 0
        self.gravity = 0.8
        self.damping = 0.6  # バウンドで減衰する係数
        # 寿命（フレーム数）
        self.life = 120  # バウンドさせるため少し長めにする

    def update(self, screen, blocks, stage_width, camera_x) -> bool:
        # 移動（X 方向）
        self.rect.x += int(self.speed)

        # ブロックとの水平衝突で反転（壁に当たれば跳ね返る）
        for block in blocks:
            if self.rect.colliderect(block):
                # 衝突の向きによって処理
                if self.speed > 0:
                    self.rect.right = block.left
                else:
                    self.rect.left = block.right
                # 水平速度を反転して減衰
                self.speed = -self.speed * 0.6

        # 垂直方向の物理（重力適用）
        self.vy += self.gravity
        self.rect.y += int(self.vy)

        # ブロックとの垂直衝突（地面や天井で跳ね返す）
        for block in blocks:
            if self.rect.colliderect(block):
                if self.vy > 0:
                    # 落下中にブロックと衝突 => 足元をブロックの上に合わせ、反射
                    self.rect.bottom = block.top
                    self.vy = -self.vy * self.damping
                elif self.vy < 0:
                    # 上昇中に頭が当たった
                    self.rect.top = block.bottom
                    self.vy = 0

        # 寿命減少
        self.life -= 1

        # 画面外 or 寿命切れで消滅（横にはみ出し過ぎたら消す）
        if self.life <= 0 or self.rect.right < -50 or self.rect.left > SCREEN_WIDTH * stage_width + 50:
            return False

        # 描画
        if self.image:
            screen.blit(self.image, (self.rect.x - camera_x, self.rect.y))
        else:
            # 発光風の炎（画像が無いとき用）
            import random
            r = random.randint(200, 255)
            g = random.randint(60, 150)
            y = random.randint(0, 60)
            color = (r, g, y)
            for i in range(3):
                radius = max(1, 10 - i * 3)
                pg.draw.circle(screen, color, (self.rect.x - camera_x, self.rect.y), radius)
        return True


class BreathParticle(pg.sprite.Sprite):
    """短距離の吐息（短命・ノー重力）"""
    def __init__(self, x, y, direction):
        super().__init__()
        # 向きと遅い速度（近距離ストリーム風）
        self.facing = direction
        self.speed = 4 * direction  # 以前より遅くしてストリーム感を出す
        self.life = 30
        img = None
        # 優先して吐息用画像を読み込む（fire_a.pngは参照しない）
        if direction >= 0:
            candidates = ("fig/fire_right.png", "fig/fire.jpg")
        else:
                candidates = ("fig/fire_left.png", "fig/fire_reft.png", "fig/fire.jpg")
        for fname in candidates:
            try:
                img = pg.image.load(fname).convert_alpha()
                self.src_name = os.path.basename(fname)
                break
            except Exception:
                img = None
        if img:
            # 吐息は横長にして少し大きめに
            w = 64
            h = 28
            img = pg.transform.scale(img, (w, h))
            # 左向きなら、読み込んだ画像が右向き（または汎用画像）だった場合のみ反転する
            if direction < 0:
                src = getattr(self, 'src_name', '')
                if any(k in src for k in ('fire_right', 'fire.jpg', 'fire-right')):
                    img = pg.transform.flip(img, True, False)
            self.image = img
            self.rect = self.image.get_rect()
            # 口元に沿わせるため、画像の左端/右端を口の位置に合わせる
            if direction >= 0:
                # 右向き: 画像の左端が口になるように設定
                self.rect.midleft = (x, y)
            else:
                # 左向き: 画像の右端が口になるように設定
                self.rect.midright = (x, y)
        else:
            # 画像がなければ円で表現
            self.image = None
            self.rect = pg.Rect(0, 0, 12, 12)
            self.src_name = ""
            if direction >= 0:
                self.rect.midleft = (x, y)
            else:
                self.rect.midright = (x, y)

    def update(self, screen, stage_width, camera_x) -> bool:
        # 水平方向に移動
        self.rect.x += int(self.speed)
        self.life -= 1

        # 画面外で消える
        if self.life <= 0:
            return False

        # 画面外で消える
        if self.life <= 0 or self.rect.right < -40 or self.rect.left > SCREEN_WIDTH * stage_width + 40:
            return False

        # 描画（画像があれば画像、無ければ円）
        if self.image:
            # 少し上下にゆらぎを入れて炎らしく見せる
            dy = random.randint(-3, 3)
            # グロー（薄い半透明の円）を先に描く
            glow_surf = pg.Surface((self.rect.width * 2, self.rect.height * 2), pg.SRCALPHA)
            glow_color = (255, 180, 70, 80)
            pg.draw.ellipse(glow_surf, glow_color, glow_surf.get_rect())
            screen.blit(glow_surf, ((self.rect.centerx - glow_surf.get_width() // 2) -  camera_x, self.rect.centery - glow_surf.get_height() // 2 + dy))
            # 本体を描画
            screen.blit(self.image, (self.rect.x - camera_x, self.rect.y + dy))
            # screen.blit(self.image, (100, 100))
        else:
            color = (255, 160, 60)
            pg.draw.circle(screen, color, self.rect.center, 6)
        return True


class CrashEffect(pg.sprite.Sprite):
    """自己中心の爆発エフェクト（非破壊・視覚効果）"""
    def __init__(self, center):
        super().__init__()  
        self.center = center
        # 少し長めに表示し、範囲を広げる
        self.life = 26
        self.max_radius = 140
        # 可能なら画像を読み込んで爆発に使う
        self.image = None
        try:
            img = pg.image.load("fig/fire_crash.png").convert_alpha()
            self.image = img
        except Exception:
            self.image = None

    def update(self, screen, camera_x) -> bool:
        t = (20 - self.life) / 20.0
        radius = int(self.max_radius * t)
        # 画像があれば画像をスケールしてアルファで描画、無ければ半透明サーフェスで描画
        if self.image:
            # スケールサイズは現在の radius に合わせる（直径）
            size = max(2, radius * 2)
            try:
                img = pg.transform.smoothscale(self.image, (size, size))
            except Exception:
                img = pg.transform.scale(self.image, (size, size))
            # フェードアウトするアルファ
            alpha = int(220 * (1.0 - t))
            img.set_alpha(alpha)
            if size > 500:
                self.kill()
            screen.blit(img, ((self.center[0] - size // 2) - camera_x, self.center[1] - size // 2))
        # else:
        #     surf = pg.Surface((self.max_radius * 2, self.max_radius * 2), pg.SRCALPHA)
        #     alpha = int(200 * (1.0 - t))
        #     pg.draw.circle(surf, (255, 180, 80, alpha), (self.max_radius, self.max_radius), max(1, radius))
        #     screen.blit(surf, (self.center[0] - self.max_radius, self.center[1] - self.max_radius))
        self.life -= 1
        return self.life > 0


class ExplosionEffect(pg.sprite.Sprite):
    """壁に当たったときの小規模爆発（視覚効果）"""
    def __init__(self, center):
        super().__init__()
        self.center = center
        self.life = 12
        self.max_size = 64
        self.image = None
        try:
            img = pg.image.load("fig/exposion.png").convert_alpha()
            self.image = img
        except Exception:
            self.image = None

    def update(self, screen):
        t = (12 - self.life) / 12.0
        size = int(self.max_size * (0.5 + t * 0.5))
        if self.image:
            try:
                img = pg.transform.smoothscale(self.image, (size, size))
            except Exception:
                img = pg.transform.scale(self.image, (size, size))
            alpha = int(255 * (1.0 - t))
            img.set_alpha(alpha)
            screen.blit(img, (self.center[0] - size // 2, self.center[1] - size // 2))
        else:
            surf = pg.Surface((self.max_size, self.max_size), pg.SRCALPHA)
            alpha = int(200 * (1.0 - t))
            pg.draw.circle(surf, (255, 180, 60, alpha), (self.max_size // 2, self.max_size // 2), max(1, size // 2))
            screen.blit(surf, (self.center[0] - self.max_size // 2, self.center[1] - self.max_size // 2))
        self.life -= 1
        return self.life > 0


class kirby_fire(Player):
    """かーびー本体（見た目＋炎の管理だけ。移動や当たり判定は既存ロジックを使用）"""
    def __init__(self, instance):
        super().__init__()
        # 右向き・左向き用の画像をそれぞれ読み込む
        self.name = "fire"
        self.img_right = None
        self.img_left = None
        try:
            # 左向き画像として読み込み
            self.img_right = pg.image.load("fig/kirby_fire.png").convert_alpha()
            self.img_right = pg.transform.scale(self.img_right, (50, 50))
            # 右向き画像として読み込み
            self.img_left = pg.image.load("fig/koukaton2.png").convert_alpha()
            self.img_left = pg.transform.scale(self.img_left, (50, 50))
        except Exception:
            pass  # 画像が読めなければ四角形で代用
        self.rect = instance.rect  # 既存の player_rect を共有
        self.rect.size = (28, 28)  # かーびーのサイズに合わせる
        self.fireballs = []
        # 吐息（短距離）用
        self.breaths = []
        self.breathing = False
        self._breath_spawn_timer = 0
        # クラッシュ（範囲攻撃）用
        self.crashes = []
    # クールタイム無しにする（いつでも発動可能）
        # 向き（1=右, -1=左）
        self.facing = 1

    def handle_input(self, event, move_left, move_right, fireballs, breathes, clashes):
        # 向き更新
        if move_left and not move_right:
            self.facing = -1
        elif move_right and not move_left:
            self.facing = 1
        # Zキーで炎発射（進行方向に飛ぶ）
        if event.type == pg.KEYDOWN and event.key == pg.K_z:
            # 発射方向は常にカービィの向きに合わせる（左右双方から出るように）
            direction = self.facing
            # 発射位置：口の位置に合わせる（体の前方・少し上）
            fx = self.rect.centerx + self.facing * (self.rect.width // 2)
            fy = self.rect.centery - 6
            fireballs.add(FireBall(fx, fy, direction))

        # Xキーで吐息（押している間持続）
        if event.type == pg.KEYDOWN and event.key == pg.K_x:
            self.breathing = True
            breathes.add(BreathParticle(x=self.rect.centerx + self.facing * (self.rect.width // 2),
                                        y=self.rect.centery - 4,
                                        direction=self.facing))
        if event.type == pg.KEYUP and event.key == pg.K_x:
            self.breathing = False
            for breath in breathes:
                breath.kill()
                break

        # Cキーでクラッシュ（単発・クールタイム無し）
        if event.type == pg.KEYDOWN and event.key == pg.K_c:
            # クールダウンなしで常に発動可能にする
            clashes.add(CrashEffect(self.rect.center))
    def draw_and_update(self, screen, explosions, all_blocks, camera_x, fireballs, breathes, crashes, stage_width):

        # 炎の更新＆描画（生存管理）
        alive = []
        for fb in fireballs:
            if fb.update(screen, all_blocks,stage_width, camera_x):
                if fb.life <= 0:
                    fb.kill()

        # 吐息のスポーン（押している間）
        if self.breathing:
            self._breath_spawn_timer -= 1
            if self._breath_spawn_timer <= 0:
                # 発射位置は口のすぐ前（中心から幅の半分だけ前）
                fx = self.rect.centerx + self.facing * (self.rect.width // 2)
                fy = self.rect.centery - 4
                breathes.add(BreathParticle(fx, fy, self.facing))
                self._breath_spawn_timer = 2  # 連射速度（小さくして連続感を強める）

        # 吐息更新
        for bp in breathes:
            if bp.update(screen, stage_width, camera_x):
                if bp.life < 0:
                    bp.kill()

        # クラッシュエフェクト更新
        for ce in crashes:
            if ce.update(screen, camera_x):
                if ce.life < 0:
                    ce.kill()

        # 壁衝突用の小規模爆発エフェクトの更新
        for ee in explosions:
            try:
                if ee.update(screen):
                    if ee.life < 0:
                        ee.kill()
            except Exception:
                pass
    # グローバルリストを更新（短命なので他と同じように扱う）
    # 注意: 物理（walled/gravity）は Player.update 側で一度だけ適用されるため
    # ここで再度呼び出すと移動や重力が二重に適用されてしまう。
    # そのため、描画側では物理処理を行わない。
        # 本体描画（画像があれば画像）
        if self.img_right and self.img_left:
            # 向きに応じて適切な画像を選択（左向き=kirby_fire, 右向き=koukaton2）
            img = self.img_left if self.facing > 0 else self.img_right
            screen.blit(img, (self.rect.centerx - camera_x, self.rect.centery - TILE_SIZE_Y / 2))
        else:
            pg.draw.rect(screen, (50, 200, 50), self.rect)
# ==== 追加ここまで ====

# 3.5 ボムコピー能力システムの定義
# ========================================
# 個人実装機能: ボムコピー能力 (C0C24001)
# カービィが敵を吸い込んでコピーする能力として実装
# ========================================

class C0C24001_BombAbility(Player):
    """ボムコピー能力クラス (C0C24001実装)
    
    カービィが爆弾を持つ敵を吸い込んだ後に使えるようになる能力
    
    使い方:
    1. 他のメンバーの吸い込みシステムから activate() を呼ぶ
    2. プレイヤーがBキーを押したら use_ability() を呼ぶ
    3. 返り値の爆弾オブジェクトを bombs リストに追加
    """
    def __init__(self, instance):
        super().__init__()
        # raise ValueError
        self.name = "bomb"  # ボム能力を持っているか
        self.bomb_img = pg.image.load("img/bom2.png").convert_alpha()
        self.flip_bomb_img = pg.transform.flip(self.bomb_img, True, False)
        self.rect = instance.rect
        # self.vx = PLAYER_SPEED
        self.is_on_ground = False     # 地面（ブロック）に接地しているか
        self.move_left = False # 左に移動中か
        self.move_right = False# 右に移動中か
        self.facing_right = True # プレイヤーの向き（True=右向き, False=左向き）


        
    def activate(self):
        """ボム能力を取得(敵を吸い込んだ時に呼ばれる)"""
        self.has_ability = True
        print("【ボム能力を取得!】")
        
    def deactivate(self):
        """ボム能力を失う"""
        self.has_ability = False
        print("【ボム能力を失った】")
        
    def use_ability(self, player_pos, player_facing_right, ability_type="place", camera_x = 0):
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
            print(self.rect.centerx, self.rect.centery)
            bomb_x = self.rect.centerx - camera_x
            bomb_y = self.rect.centery
            return C0C24001_BombProjectile(bomb_x, bomb_y, velocity_x=0, velocity_y=1)
        elif ability_type == "throw":
            bomb_x = self.rect.centerx - camera_x
            bomb_y = self.rect.centery
            throw_speed_x = 10 if player_facing_right else -10
            throw_speed_y = -8
            return C0C24001_BombProjectile(bomb_x, bomb_y, velocity_x=throw_speed_x, velocity_y=throw_speed_y)
        
        return None

class C0C24001_BombProjectile(pg.sprite.Sprite):
    """爆弾プロジェクタイルクラス (C0C24001実装)
    
    ボム能力で生成される爆弾オブジェクト
    
    実装機能:
    - 物理演算(重力、跳ね返り、摩擦)
    - 爆発タイマーとエフェクト
    - GIFアニメーション表示
    """
    def __init__(self,instance, velocity_x=0, velocity_y=0):
        super().__init__()
        self.img = pg.image.load("img/bom3.png").convert_alpha()
        self.img = pg.transform.rotozoom(self.img, 0, 0.1)  # 0.5から0.3に縮小
        # self.rect = pg.Rect(x, y, TILE_SIZE_X, TILE_SIZE_Y)
        self.rect = self.img.get_rect()
        self.rect.center = (instance.rect.centerx, instance.rect.centery)
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
            
            # 重力を常に適用（地面にいない限り）
            if not self.on_ground:
                self.velocity_y += GRAVITY * 0.5  # 爆弾用の重力（少し弱め）
            #frag_bomb
            # X方向の移動
            if self.velocity_x != 0:
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
                
                # 画面端チェックは削除（ワールド座標なので不要）
                # 爆弾がステージ外に出た場合は自然に落下して消える
            
            # Y方向の移動
            self.rect.y += self.velocity_y
            
            # Y方向の衝突チェック
            self.on_ground = False
            for block in block_rects:
                if self.rect.colliderect(block):
                    # raise ValueError
                    if self.velocity_y > 0:  # 落下中
                        self.rect.bottom = block.top
                        self.velocity_y = -self.velocity_y * 0.3  # 少し跳ねる
                        self.on_ground = True
                        # 摩擦で減速
                        self.velocity_x *= 0.9
                        if abs(self.velocity_x) < 0.5:
                            self.velocity_x = 0
                        # 跳ね返りが小さい場合は停止
                        if abs(self.velocity_y * 0.3) < 1:
                            self.velocity_y = 0
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
    
    def draw(self, surface, bomb_image, explosion_frames, camera_x):
        """爆弾または爆発エフェクトを描画"""
        if self.is_exploded:
            # 爆発エフェクトを描画
            if explosion_frames and len(explosion_frames) > 0:
                # アニメーションフレームを表示
                elapsed_time = time.time() - self.explosion_time
                # フレームレート: 0.05秒ごとに切り替え(20fps)
                frame_index = int(elapsed_time / 0.05) % len(explosion_frames)
                current_frame = explosion_frames[frame_index]
                
                # カメラオフセットを考慮して描画
                explosion_center_x = self.rect.centerx - camera_x
                explosion_center_y = self.rect.centery
                explosion_rect = current_frame.get_rect(center=(explosion_center_x, explosion_center_y))
                surface.blit(current_frame, explosion_rect.topleft)
            else:
                # 画像がない場合は円で表現（カメラオフセット考慮）
                explosion_center = (self.rect.centerx - camera_x, self.rect.centery)
                # 外側の円(赤)
                pg.draw.circle(surface, RED, explosion_center, C0C24001_BOMB_EXPLOSION_RADIUS, 0)
                # 中間の円(オレンジ)
                pg.draw.circle(surface, ORANGE, explosion_center, C0C24001_BOMB_EXPLOSION_RADIUS * 2 // 3, 0)
                # 内側の円(黄色)
                pg.draw.circle(surface, (255, 255, 0), explosion_center, C0C24001_BOMB_EXPLOSION_RADIUS // 3, 0)
        # else:
            # 爆弾画像を描画（カメラオフセット考慮）
            # surface.blit(bomb_image, (self.rect.x - camera_x, self.rect.y))
    
    def get_explosion_rect(self):
        """爆発範囲の矩形を返す"""
        if self.is_exploded:
            center = self.rect.center
            explosion_rect = pg.Rect(
                center[0] - C0C24001_BOMB_EXPLOSION_RADIUS,
                center[1] - C0C24001_BOMB_EXPLOSION_RADIUS,
                C0C24001_BOMB_EXPLOSION_RADIUS * 2,
                C0C24001_BOMB_EXPLOSION_RADIUS * 2
            )
            return explosion_rect
        return None
#---修正

class Kajino_kirby(Player):
    def __init__(self, instance):
        super().__init__()
        self.name = "kajino"
        self.kajino_img = pg.image.load("カービィカジノ吸収.png").convert_alpha()
        # self.img = pg.transform.scale(self.kajino_img, (50, 50))
        self.kajino_img = pg.transform.rotozoom(self.kajino_img, 0, 0.1)
        self.rect = instance.rect
        self.rect.size = (28, 28)

class Bullet(pg.sprite.Sprite):
    def __init__(self, instance, type):
        super().__init__()
        self.configs = {
            1: pg.transform.rotozoom(pg.image.load("きいろ.png"),0,0.1),      # タイプ1 (黄)
            2: pg.transform.rotozoom(pg.image.load("あお.png"),0,0.2), # タイプ2 (青)
            3: pg.transform.rotozoom(pg.image.load("あか.png"),0,0.3),   # タイプ3 (赤)
            99999: pg.transform.rotozoom(pg.image.load("くろ.png"),0,0.5) ,   # 超特大 (黒)
        }
        self.img = self.configs[type]
        self.rect = self.img.get_rect()
        self.rect.center = instance.rect.center
        # self.rect.center = (500, 100)
        self.speed = 15 * instance.patarn[0]
        self.time = 300
    def update(self, screen, blocks, stage_width, camera_x) -> bool:
        self.rect.x += int(self.speed)

        # for block in blocks:
        #     if self.rect.colliderect(block):
        #         self.kill()

        if self.rect.right < -50 or self.rect.left > SCREEN_WIDTH * stage_width + 50:
            self.kill()
        
        self.time -= 1
        if self.time <= 0:
            self.kill()

        screen.blit(self.img, (self.rect.x - camera_x, self.rect.y))
        return True
    

class Enemy(pg.sprite.Sprite):
    """
    敵を司るクラス
    """
    def __init__(self):
        super().__init__()

        self.original = pg.image.load("fig/troia1.png")
        self.image = self.original
        self.flip = pg.transform.flip(self.image, True, False)
        self.rect = self.image.get_rect()
        self.rect.center = (1000, 0) #テスト用で定数
        self.size = 1.0
        self.vx = ENEMY_SPEED
        self.vy = 0
        self.patarn = (1, 0, "normal")
        self.patarn_to_img = {(1, 0, "normal"): self.image, (-1, 0, "normal"): self.flip,
                              (1, 0, "no_damage"): pg.transform.laplacian(self.image), (1, 0, "no_damage"): pg.transform.laplacian(self.flip),
                              }

        self.hp = 5
        self.no_damage_time = NO_DAMAGE_TIME
        self.power = 1
        
        self.is_on_ground = False
        self.is_move_left, self.is_move_right = True, False

    def update(self, all_blocks: "list[object]", floar_blocks: "list[object]", camera_x: "int") -> None:
        """
        自身の位置を更新する関数
        """
        self.rect.x -= self.vx

        for block in all_blocks:
            if self.rect.colliderect(block):
                if self.is_move_left:
                    self.rect.left = block.right
                    self.is_move_right = True
                    self.is_move_left = False
                elif self.is_move_right:
                    self.rect.right = block.left
                    self.is_move_left = True
                    self.is_move_right = False
                self.vx *= -1
                # print(f"敵の速度{self.vx}")
                
        gravity(self, floar_blocks)
        # self.rect.centery -= (TILE_SIZE_Y/2)
#------

class PlayerLeadAttack(pg.sprite.Sprite):
    def __init__(self, size, time, type, ini_angle = 45):
        super().__init__()
        self.original = pg.Surface(size)
        self.original.fill((255, 0, 0))
        self.rect = self.original.get_rect()
        self.img = self.original
        self.time = time
        self.angle = ini_angle + 1
        self.type = type
        self.dire = (1, 0)


    def update(self, instance):
        if instance.move_left == True:
            self.dire = (-1, 0)
        elif instance.move_right == True:
            self.dire = (1, 0)

        if self.dire == (-1, 0):
            self.rect.x ,self.rect.y = instance.rect.left - 30, instance.rect.y + 50
        elif self.dire == (1, 0):
            self.rect.x ,self.rect.y = instance.rect.right + 30, instance.rect.y + 50
        if self.type == "punch":
            self.time -= 1
            # print(self.time)
            if self.time == 0:
                instance.attacking = False
                instance.patarn = (instance.patarn[0], 0, "normal")
                # instance.status = instance.imgs[0]
                self.kill()
                
    
class EnemyLeadAttack(pg.sprite.Sprite):
        def __init__(self, size,  time, type, ini_angle):
            self.original = pg.surface(size)
            self.img = self.original
            self.time = time
            self.angle = ini_angle + 1
            self.type = type        

        def update(self, fin_angle = 45):
            if self.type == "beam":
                self.angle += 1
                self.img = pg.transform.rotate(self.original, angle)
                if self.angle == fin_angle:
                    self.kill()

class BoundBalls(pg.sprite.Sprite):
    def __init__(self, stage_width, tile_num_y):
        super().__init__()
        self.img = pg.image.load("fig/virus.png")
        self.rect = self.img.get_rect()
        self.rect.center = (stage_width * TILE_SIZE_X, 0)
        self.vx = - 2
        self.vy = 1
        self.top_bordarline = 0
        self.bottom_bordarline = ((SCREEN_HEIGHT / TILE_SIZE_Y) - tile_num_y) * TILE_SIZE_Y

    def update(self):
        self.rect.x += self.vx
        if self.vy == 1:
            self.rect.y += 3 # Y方向に動かす
            # print(f"降下中{self.rect.y}")
            if self.rect.y >= self.bottom_bordarline:
                self.vy = -1
        elif self.vy == -1:
            self.rect.y -= 3
            # print("上昇中")
            if self.rect.y <= self.top_bordarline:
                self.vy = 1
        if self.rect.x <= 0:
            self.kill()

#------

#---まだ
class Goal(pg.sprite.Sprite):
    def __init__(self, map_data):
        super().__init__()
        self.image = pg.image.load("fig/goal(normal).png")
        self.rect = self.image.get_rect()
        self.rect.x, self.rect.y = TILE_SIZE_X * len(map_data[0]) - TILE_SIZE_X * 1.5, SCREEN_HEIGHT - TILE_SIZE_Y * 9

    # def update(self, camera_x):
        # self.rect.x = camera_x
        
    
#------
class Hp:
    def __init__(self):
        self.pic = pg.font.Font(None, 80)
        self.txt = self.pic.render("HP: ", True, (0, 0, 0))

class Heart(pg.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.img = pg.image.load("fig/hearts1.png")

    def update(self, instance, num):
        if instance.hp < num:
            self.kill()


#---まだ
class Score:
    def __init__(self):
        self.pic = pg.font.Font(None, 80)
        self.value = 0
    
    def update(self):
        self.txt = self.pic.render(f"Score: {self.value}", True, (255, 255, 255))
#------

def main():
    # ーーーーー画面設定ーーーーー
    screen = pg.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pg.display.set_caption("2Dアクションゲーム デモ")
    clock = pg.time.Clock()
    # ーーーーーーーーーーーーーー
    respond = start_page(screen, clock)
    if respond == -1:
        return
    

    assets = Assets()

    bg_img = pg.image.load("fig/night_plain_bg.png")
    bg_width = bg_img.get_width()
    pg.mixer.music.load("fig/魔王魂(ファンタジー).mp3")
    pg.mixer.music.play(loops = -1)

    map_data = assets.init_map
    map_data = extend(map_data, ADD_STAGE_BLOCK, assets.probs)
    map_data = ground_surface(map_data)
    map_data = make_float_land(map_data, (6,10), 10)

    block_rects = []
    surface_rects = []
    floatland_rects = []
    for y, row in enumerate(map_data):
        for x, tile_type in enumerate(row):
            if tile_type == 1:
                block_rects.append(pg.Rect(x * TILE_SIZE_X, y * TILE_SIZE_Y, TILE_SIZE_X, TILE_SIZE_Y))
            elif tile_type == 2:
                surface_rects.append(pg.Rect(x * TILE_SIZE_X, y * TILE_SIZE_Y + (TILE_SIZE_Y / 2), TILE_SIZE_X,TILE_SIZE_Y / 2))
            elif tile_type == 3:
                floatland_rects.append(pg.Rect(x * TILE_SIZE_X, y * TILE_SIZE_Y + (TILE_SIZE_Y / 2), TILE_SIZE_X, TILE_SIZE_Y / 2))


    floar_blocks = surface_rects + floatland_rects
    all_blocks = block_rects + floar_blocks
    
    enemys = pg.sprite.Group()
    hearts = pg.sprite.Group()
    hovers = pg.sprite.Group()
    player_lead_attacks = pg.sprite.Group()
    bound_balls = pg.sprite.Group()
    absurbs = pg.sprite.Group()
    explosions = pg.sprite.Group()
    fireballs = pg.sprite.Group()
    clashes = pg.sprite.Group()
    breathes = pg.sprite.Group()
    bombs = pg.sprite.Group()
    bullets = pg.sprite.Group()

    player = Player() 
    for i in range(ENEMY_NUM):
        enemys.add(Enemy())
    goal = Goal(map_data)
    for i in range(player.hp):
        hearts.add(Heart())
    bound_balls.add(BoundBalls(len(map_data[0]), 5))
    score = Score()
    hp = Hp()
    
    camera_x = 0
    time = 0

    #ーーーーーゲームスタートーーーーー
    while True:
    
        #ーーーーーイベント取得ーーーーー

        if player.rect.colliderect(goal):
            print("goal!!")
            respond = game_clear(screen, clock)
            if respond == -1:
                return
            else:
                enemys = pg.sprite.Group()
                hearts = pg.sprite.Group()
                hovers = pg.sprite.Group()
                player_lead_attacks = pg.sprite.Group()
                bound_balls = pg.sprite.Group()
                breathes = pg.sprite.Group()

                player = Player() 
                for i in range(ENEMY_NUM):
                    enemys.add(Enemy())
                goal = Goal(map_data)
                for i in range(player.hp):
                    hearts.add(Heart())
                bound_balls.add(BoundBalls(len(map_data[0]), 5))
                score = Score()
                hp = Hp()
                
                camera_x = 0
                time = 0 
            
        if player.hp <= 0:
            print("failed")
            respond = gameover(screen, clock)
            if respond == -1:
                return 
            else: 
                enemys = pg.sprite.Group()
                hearts = pg.sprite.Group()
                hovers = pg.sprite.Group()
                player_lead_attacks = pg.sprite.Group()
                bound_balls = pg.sprite.Group()

                player = Player() 
                for i in range(ENEMY_NUM):
                    enemys.add(Enemy())
                goal = Goal(map_data)
                for i in range(player.hp):
                    hearts.add(Heart())
                bound_balls.add(BoundBalls(len(map_data[0]), 5))
                score = Score()
                hp = Hp()
                
                camera_x = 0
                time = 0                

        for event in pg.event.get():
            #ゲーム終了
            if event.type == pg.QUIT:
                return 
            
            # キーが押された時
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_LEFT:
                    player.move_left = True
                if event.key == pg.K_RIGHT:
                    player.move_right = True
                if event.key == pg.K_SPACE:
                    player.hover()
                    hovers.add(HoverAir(player, -1, 1))
                    hovers.add(HoverAir(player, 1, 0))
                    player.is_on_ground = False
                if event.key == pg.K_p:
                    if not player.attacking:
                        player_lead_attacks.add(player.panch())
                if event.key == pg.K_a:
                    absurbs.add(Absurb(player))
                if player.name == "fire":
                    player.handle_input(event, player.move_left, player.move_right, fireballs, breathes, clashes)
                # ========================================
                # 個人実装: 爆弾操作 (C0C24001)
                # ========================================
                if event.key == pg.K_b:
                    # 爆弾能力を持っている場合のみ使用可能
                    if player.name == "bomb":
                        # Shiftキーが押されている場合は投擲、それ以外は設置
                        keys = pg.key.get_pressed()
                        if keys[pg.K_LSHIFT] or keys[pg.K_RSHIFT]:
                            # 爆弾を投擲（前方に投げる)
                            bomb_x = player.rect.centerx  # camera_xを引かない（ワールド座標）
                            bomb_y = player.rect.centery
                            # プレイヤーの向きに応じて速度を設定
                            throw_speed_x = 10 if player.facing_right else -10
                            throw_speed_y = -8  # 上向きに投げる
                            new_bomb = C0C24001_BombProjectile(player, velocity_x=throw_speed_x, velocity_y=throw_speed_y)
                            bombs.add(new_bomb)
                        else:
                            # 爆弾を設置（プレイヤーの足元に設置し、重力で落下）
                            bomb_x = player.rect.centerx  # camera_xを引かない（ワールド座標）
                            bomb_y = player.rect.centery
                            print(player.rect.centerx, player.rect.centery)
                            # 設置時に初期速度を設定（重力で落下させる）
                            new_bomb = C0C24001_BombProjectile(player, velocity_x=0, velocity_y=1)
                            bombs.add(new_bomb)
                
                if event.key == pg.K_k:
                    # 近くの爆弾をキック
                    for bomb in bombs:
                        if not bomb.is_exploded and abs(bomb.velocity_x) < 1:  # 静止している爆弾のみ
                            # プレイヤーとの距離をチェック
                            distance = ((player.rect.centerx - bomb.rect.centerx) ** 2 + 
                                       (player.rect.centery - bomb.rect.centery) ** 2) ** 0.5
                            if distance < TILE_SIZE_X * 2:  # 2タイル以内
                                # プレイヤーの向きに応じて蹴る
                                kick_speed = 8 if player.facing_right else -10
                                bomb.velocity_x = kick_speed
                                bomb.velocity_y = -3  # 少し浮かせる
                                break  # 1つだけキック
                if event.key == pg.K_0:
                    if random.randrange(1, 101) <= 5:
                        type_ = 99999
                    else:
                        type_ = random.randrange(1, 4)
                    bullets.add(Bullet(player, type_))

            # キーが離された時
            if event.type == pg.KEYUP:
                if event.key == pg.K_LEFT:
                    player.vx = 0
                    player.move_left = False
                if event.key == pg.K_RIGHT:
                    player.vx = 0
                    player.move_right = False
                if event.key == pg.K_a:
                    absurbs.empty()
                if player.name == "fire":
                    player.handle_input(event, player.move_left, player.move_right, fireballs, breathes, clashes)

        #ーーーーーーーーーーーーーーーー
        heart_num = len(hearts)



        for enemy in pg.sprite.spritecollide(player, enemys, False): 
            if player.no_damage_time == 0:
                player.hp -= 1
                for i in hearts:
                    i.update(player, heart_num)
                    heart_num -= 1
                no_damage(player,1)

        collisions = pg.sprite.groupcollide(absurbs, enemys, False, False)
        for absorber, hit_list in collisions.items():
            for enemy in hit_list:
                enemy.size -= 0.05
                enemy.patarn_to_img[enemy.patarn] = pg.transform.rotozoom(enemy.patarn_to_img[enemy.patarn], 0, enemy.size)
                enemy.rect.centery += 10
                if enemy.size <= 0:
                    enemy.kill()
                    player = Kajino_kirby(player)
        collisions = pg.sprite.groupcollide(bullets, enemys, False, False)
        for bullet, hit_list in collisions.items():
            for enemy in hit_list:
                if enemy.no_damage_time == 0:
                    enemy.hp -= 1
                    no_damage(enemy, 1)
                if enemy.hp == 0:
                    enemy.kill()


        for bound_boll in bound_balls:
            if player.rect.colliderect(bound_boll):
                if player.no_damage_time == 0:
                    player.hp -= 1
                    for i in hearts:
                        i.update(player, heart_num)
                        heart_num -= 1
                    no_damage(player,1)              

        for enemy in pg.sprite.groupcollide(enemys, player_lead_attacks, False, False).keys():
            if enemy.no_damage_time == 0:
                enemy.hp -= 1
                no_damage(enemy, 1)
                # print("attacked")
            if enemy.hp == 0:
                enemy.kill()


        #----修正
        # no_damage(player, 0)
        if player.name == "normal":
            camera_x = player.update(len(map_data[0]), all_blocks, floar_blocks, camera_x)
        elif player.name == "fire":
            camera_x = player.update(len(map_data[0]), all_blocks, floar_blocks, camera_x)
        elif player.name == "bomb":
            camera_x = player.update(len(map_data[0]), all_blocks, floar_blocks, camera_x)
        elif player.name == "kajino":
            camera_x = player.update(len(map_data[0]), all_blocks, floar_blocks, camera_x)
        # for i in player_lead_attacks:
        #     i.update(player)
        #     screen.blit(i.img, (100, 100))#(player.rect.x + 100, player.rect.y))
        scroll_x = -camera_x % bg_width
        #-------

        screen.blit(bg_img, (scroll_x - bg_width, -100))
        screen.blit(bg_img, (scroll_x, -100))
        #---修正
        if player.name == "normal":
            screen.blit(player.patarn_to_img[player.patarn], (player.rect.x - camera_x, player.rect.y))
        elif player.name == "fire":
            player.draw_and_update(screen, explosions, all_blocks, camera_x, fireballs, breathes, clashes, len(map_data[0]))

        elif player.name == "bomb":
            player.update(len(map_data[0]), all_blocks, floar_blocks, camera_x)
            screen.blit(player.bomb_img, (player.rect.x - camera_x, player.rect.y))
        elif player.name == "kajino":
            screen.blit(player.kajino_img, (player.rect.x - camera_x, player.rect.y - 50))
        for bomb in bombs:
            screen.blit(bomb.img, (bomb.rect.x - camera_x, bomb.rect.y))
        # kirby.draw_and_update(screen)
        hovers.update()
        for hover in hovers:
            screen.blit(hover.image, (hover.rect.x - camera_x, hover.rect.y))
        for i in player_lead_attacks:
            i.update(player)
            screen.blit(i.img, (i.rect.x - camera_x, i.rect.y))

        for i in absurbs:
            i.update(player)
            screen.blit(i.img, (i.rect.x - camera_x, i.rect.y))

        for bomb in bombs:
            if bomb.update(all_blocks):  # 爆発した場合（block_rectsを渡す）
                # 爆発音を再生
                if explosion_sound:
                    explosion_sound.play()
                # 将来的にここで敵やプレイヤーへのダメージ処理を追加
                pass
        
            # 爆発エフェクトが終了したら削除リストに追加
            if bomb.is_explosion_finished():
                bomb.kill()
            else:
                # 爆弾を描画 (C0C24001) - drawメソッドを使用してGIFアニメーション対応
                bomb.draw(screen, bomb.img, c0c24001_explosion_frames, camera_x)
                screen.blit(bomb.img, (bomb.rect.x - camera_x, bomb.rect.y))
        
        bullets.update(screen, all_blocks, len(map_data[0]), camera_x)
        for i in bound_balls:
            i.update()
            screen.blit(i.img, (i.rect.x - camera_x, i.rect.y))
        if time % 300 == 0:
            bound_balls.add(BoundBalls(len(map_data[0]), 5))

        enemys.update(all_blocks, floar_blocks, camera_x)
        for enemy in enemys:
            no_damage(enemy, 0)
            screen.blit(enemy.patarn_to_img[enemy.patarn], (enemy.rect.x - camera_x, enemy.rect.y))
        #------

        for block in block_rects:
            screen.blit(assets.ground, (block.x - camera_x, block.y, block.width, block.height))
        for block in surface_rects:
            screen.blit(assets.weeds, (block.x - camera_x,block.y))
        for block in floatland_rects:
            screen.blit(assets.cloud, (block.x - camera_x, block.y))
        screen.blit(goal.image, (goal.rect.x - camera_x, goal.rect.y))

        # hearts.update(player, len(hearts))
        for index, i in enumerate(hearts, 1):
            screen.blit(i.img, (10 + (80 * index), 0))
        screen.blit(hp.txt, (0, 5))
        score.update()
        screen.blit(score.txt, (SCREEN_WIDTH / 10, SCREEN_HEIGHT - SCREEN_HEIGHT / 10))
        
        time += 1
        pg.display.update()
        clock.tick(60)

if __name__ == "__main__":
    pg.init()
    main()
    pg.quit()
    sys.exit()
      


# 色の定義 (頭上の数字用)




# 画面設定

# 3. ステージの「当たり判定用の四角形(Rect)」リストを作成


# 4. プレイヤー設定 

# --- 画像読み込みと左右反転 ---
# try:
#     player_image_original = pg.image.load("カービィカジノ吸収.png")
#     player_image_right = pg.transform.scale(player_image_original, (player_width, player_height))
#     player_image_left = pg.transform.flip(player_image_right, True, False)
# except (pyg.error, FileNotFoundError) as e:
#     if isinstance(e, FileNotFoundError):
#         print("プレイヤー画像ファイル 'カービィカジノ吸収.png' が見つかりません。")
#     else:
#         print(f"プレイヤー画像の読み込みに失敗しました: {e}")
#     player_image_right = pg.Surface((player_width, player_height))
#     player_image_right.fill((50, 200, 50))
#     player_image_left = player_image_right.copy() 

# player_image_current = player_image_right

# # ★★★ 弾の画像読み込みとスケール (ファイル名を修正) ★★★
# bullet_images = {} # 弾の画像を格納する辞書

# # 弾の種類とファイル名、サイズを定義
# bullet_configs = {
#     1: {"file": "きいろ.png", "size": (TILE_SIZE // 2, TILE_SIZE // 2)},      # タイプ1 (黄)
#     2: {"file": "あお.png", "size": (TILE_SIZE // 2 + 10, TILE_SIZE // 2 + 10)}, # タイプ2 (青)
#     3: {"file": "あか.png", "size": (TILE_SIZE // 2 + 20, TILE_SIZE // 2 + 20)},   # タイプ3 (赤)
#     99999: {"file": "くろ.png", "size": (TILE_SIZE * 15, TILE_SIZE * 15)}    # 超特大 (黒)
# }

# for type_key, config in bullet_configs.items():
#     try:
#         # 画像を読み込む (.jpgは透過情報がないため .convert() が最適ですが、
#         # .convert_alpha() でも問題なく動作します)
#         img_original = pg.image.load(config["file"]).convert_alpha()
#         bullet_images[type_key] = pg.transform.scale(img_original, config["size"])
#     except (pg.error, FileNotFoundError) as e:
#         # エラーメッセージも正しいファイル名に修正
#         print(f"弾画像ファイル '{config['file']}' の読み込みに失敗しました: {e}") 
#         #エラー時は代替として赤い四角形を生成
#         alt_surface = pg.Surface(config["size"], pg.SRCALPHA) # アルファチャンネル付き
#         alt_surface.fill((255, 0, 0, 128)) # 半透明な赤
#         bullet_images[type_key] = alt_surface
# ----------------------------------------

 

# 弾を管理するリスト: [bullet_rect, 弾の画像, 向き(1 or -1), 攻撃タイプ]
# bullets = []

# current_attack_type = random.randint(1, 3)


                
#             # ★★★ 攻撃キー (Zキー) が押された時 ★★★
#             if event.key == pg.K_z:
#                 actual_attack_type = current_attack_type
                
#                 bullet_image = bullet_images.get(actual_attack_type)
#                 if bullet_image is None: 
#                     bullet_image = bullet_images.get(1) 
#                     actual_attack_type = 1 
                    
#                 bullet_width, bullet_height = bullet_image.get_size()
                
#                 start_x = player_rect.centerx - bullet_width // 2 
#                 start_y = player_rect.centery - bullet_height // 2 
                
#                 bullet_rect = pg.Rect(start_x, start_y, bullet_width, bullet_height)
                
#                 bullets.append([bullet_rect, bullet_image, player_direction, actual_attack_type])
                
#                 next_attack_candidate = random.randint(1, 3)
                
#                 if random.randint(1, 100) <= SUPER_ATTACK_CHANCE:
#                     current_attack_type = 99999 
#                 else:
#                     current_attack_type = next_attack_candidate 
#             # ★★★★★★★★★★★★★★★★★★★★★★★

#         if event.type == pg.KEYUP:
#             if event.key == pg.K_LEFT:
#                 player_move_left = False
#             if event.key == pg.K_RIGHT:
#                 player_move_right = False

#     # 7. プレイヤーのロジック更新 (省略... 元と同じ)


#     # ★★★ 弾のロジック更新 ★★★
#     for bullet in reversed(bullets):
#         bullet_rect = bullet[0]
#         direction = bullet[2] # 向きはリストの3番目 (index 2)
#         bullet_rect.x += BULLET_SPEED * direction
#         if bullet_rect.right < 0 or bullet_rect.left > SCREEN_WIDTH:
#             bullets.remove(bullet)

#     # 8. 描画処理
    
#     # ★★★ 頭上に次の攻撃タイプを描画 ★★★
#     attack_text = str(current_attack_type)
    
#     if current_attack_type == 1: text_color = YELLOW_TEXT
#     elif current_attack_type == 2: text_color = BLUE_TEXT
#     elif current_attack_type == 3: text_color = RED_TEXT
#     else: text_color = CYAN_TEXT 
        
#     text_surface = attack_font.render(attack_text, True, text_color, WHITE)
    
#     text_rect = text_surface.get_rect()
#     text_rect.centerx = player_rect.centerx
#     text_rect.bottom = player_rect.top - 5 
    
#     screen.blit(text_surface, text_rect)
#     # ★★★★★★★★★★★★★★★★★★★★★★★

#     # ★★★ 弾の描画 (画像を使用) ★★★
#     for bullet in bullets:
#         bullet_rect = bullet[0]
#         bullet_image_to_draw = bullet[1] # 画像はリストの2番目 (index 1)
        
#         screen.blit(bullet_image_to_draw, bullet_rect)
#     # ★★★★★★★★★★★★★★

