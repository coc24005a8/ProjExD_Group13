import pygame
import os
import random
import math
import sys
import time


# 1. 定数と初期設定
pygame.init()  # pygameを初期化
SCREEN_WIDTH = 1100
SCREEN_HEIGHT = 600
os.chdir(os.path.dirname(os.path.abspath(__file__)))
TILE_SIZE = 40
GRAVITY = 0.8         # 重力
JUMP_STRENGTH = -15   # ジャンプ力 (Y軸は上がマイナス)
PLAYER_SPEED = 5      # 左右の移動速度

# 色の定義
BLACK = (255, 255, 255)
WHITE = (255, 255, 255)
GREEN = (50, 200, 50)   # プレイヤーの色
BLACK = (0, 0, 0)   # ブロックの色

# 画面設定
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("2Dアクションゲーム デモ")
clock = pygame.time.Clock()

class BombEnemy(pygame.sprite.Sprite):
    """
    爆弾の敵に関するクラス（描画・床判定・投擲タイマー）
    """
    def __init__(self):
        super().__init__()
        bomb_img = pygame.image.load("fig/bakudan.png")
        self.image = pygame.transform.rotozoom(bomb_img, 0, 0.125)
        # 当たり用 rect と表示用 rect を保持（既存コードと互換）
        self.rect = pygame.Rect(800, 300, TILE_SIZE, TILE_SIZE)
        self.image_rect = self.image.get_rect()
        self.image_rect.center = self.rect.center
        # 物理量
        self.vy = 0.0
        self.on_ground = False
        # 次に爆弾を投げるフレーム
        self.next_throw = random.randint(60, 120)

    def update(self, blocks):
        """
        重力処理とブロックとの衝突判定（落下・接地管理）
        blocks: block_rects（マップの矩形リスト）を想定
        """
        # 重力加算（接地していなければ落下）
        if not self.on_ground:
            self.vy += GRAVITY
            self.rect.y += int(self.vy)
            self.image_rect.center = self.rect.center

        # 地面との当たり判定（落下時のみ処理）
        self.on_ground = False
        for block in blocks:
            if self.rect.colliderect(block):
                if self.vy > 0:
                    self.rect.bottom = block.top
                    self.vy = 0.0
                    self.on_ground = True
                    self.image_rect.center = self.rect.center

    def draw(self, screen):
        """
        爆弾の敵を描画（image_rect を用いる既存の描画仕様に合わせる）
        """
        screen.blit(self.image, self.image_rect)

    def get_throw_velocity(self) -> tuple[float, float]:
        """
        プレイヤー方向への投擲初速ベクトルを返す（長さ = speed）
        戻り値: (vx, vy)
        """
        dx = player_rect.centerx - self.rect.centerx
        dy = player_rect.centery - self.rect.centery
        dist = math.hypot(dx, dy)
        if dist == 0:
            return 0.0, 0.0
        speed = 8.0
        return dx / dist * speed, dy / dist * speed


class Bomb(pygame.sprite.Sprite):
    """
    投げられた爆弾（移動・簡易重力）
    コンストラクタは BombEnemy インスタンスを受け取り初期位置・角度を決定する。
    """
    def __init__(self, bomb_enemy: BombEnemy):
        super().__init__()
        # 爆弾の初速ベクトル（BombEnemy 側で速さを乗せた vx, vy を返す）
        vx, vy = bomb_enemy.get_throw_velocity()
        self.vx = vx
        self.vy = vy
        # 画像と角度合わせ
        bomb_img = pygame.image.load("fig/bom3.png")
        angle = math.degrees(math.atan2(-self.vy, self.vx))
        self.image = pygame.transform.rotozoom(bomb_img, angle, 0.125)
        self.rect = self.image.get_rect()
        # 発射元の表示中心を起点に少し外にオフセット
        self.rect.center = bomb_enemy.image_rect.center
        offset = max(bomb_enemy.rect.width, bomb_enemy.rect.height) // 2 + 6
        if not (vx == 0 and vy == 0):
            norm = math.hypot(vx, vy)
            if norm != 0:
                self.rect.centerx += int(vx / norm * offset)
                self.rect.centery += int(vy / norm * offset)

    def update(self, blocks):
        """
        爆弾の移動（等速移動 + 少しの重力）と位置更新
        blocks 引数は現状未使用だが既存仕様に合わせて受け取る
        """
        # 少し重力を加えて落下させる
        self.vy += GRAVITY * 0.5
        # 位置更新（小数切り捨てで位置を進める）
        self.rect.x += int(self.vx)
        self.rect.y += int(self.vy)

    def draw(self, screen):
        screen.blit(self.image, self.rect)


class SlotEnemy(pygame.sprite.Sprite):
    """
    スロットの敵（BombEnemy と同様の初期位置設定をコンストラクタで可能に）
    - コンストラクタで (x, y) を与えればその座標を中心に初期配置する
    - set_position も引き続き使用可能
    - 重力・ブロック判定は行わない（仕様通り）
    """
    def __init__(self, x: int | None = None, y: int | None = None):
        super().__init__()
        slot_img = pygame.image.load("fig/slot.png")
        self.image = pygame.transform.rotozoom(slot_img, 0, 0.125)
        # デフォルト初期位置（BombEnemy と同じ書き方）
        self.rect = pygame.Rect(800, 150, TILE_SIZE, TILE_SIZE)
        self.image_rect = self.image.get_rect()
        self.image_rect.center = self.rect.center

        # コンストラクタ引数で座標が与えられていれば中心を設定する
        if x is not None and y is not None:
            self.rect.centerx = int(x)
            self.rect.centery = int(y)
            self.image_rect.center = self.rect.center

        # 速度（デフォルトは静止）
        self.vx = 0.0
        self.vy = 0.0

        # 発射関連（フレームカウント基準）
        self.next_shot = random.randint(60, 180)
        self.weapon_speed = 8.0

    def set_position(self, x: int, y: int):
        """外部から座標で位置を指定する（以降はその座標を基準にする）"""
        self.rect.centerx = int(x)
        self.rect.centery = int(y)
        self.image_rect.center = self.rect.center

    def update(self, blocks=None):
        """
        BombEnemy と同様に update メソッドを持つが，
        重力やブロック判定は行わない（等速移動のみ対応）
        """
        if self.vx != 0.0 or self.vy != 0.0:
            self.rect.x += int(self.vx)
            self.rect.y += int(self.vy)
            self.image_rect.center = self.rect.center

    def draw(self, screen):
        screen.blit(self.image, self.image_rect)


class FireEnemy(pygame.sprite.Sprite):
    """
    炎の敵に関するクラス（描画・床判定・BombEnemyと同様の物理演算）
    """
    def __init__(self):
        super().__init__()
        fire_img = pygame.image.load("fig/fire_enemy.png")
        fire_img = pygame.transform.flip(fire_img, True, False)  # 水平方向に反転
        self.image = pygame.transform.rotozoom(fire_img, 0, 0.125)
        # 当たり用 rect と表示用 rect を保持（BombEnemy と同様）
        self.rect = pygame.Rect(700, 300, TILE_SIZE, TILE_SIZE)
        self.image_rect = self.image.get_rect()
        self.image_rect.center = self.rect.center
        # 物理量（BombEnemy と同様）
        self.vy = 0.0
        self.on_ground = False

        # 発射関連（SlotEnemyと同様）
        self.next_shot = random.randint(60, 180)  # 次の発射時刻
        self.weapon_speed = 6.0  # 弾の速度

    def update(self, blocks):
        """
        重力処理とブロックとの衝突判定（落下・接地管理）
        blocks: block_rects（マップの矩形リスト）を想定
        BombEnemy と同様の実装
        """
        # 重力加算（接地していなければ落下）
        if not self.on_ground:
            self.vy += GRAVITY
            self.rect.y += int(self.vy)
            self.image_rect.center = self.rect.center

        # 地面との当たり判定（落下時のみ処理）
        self.on_ground = False
        for block in blocks:
            if self.rect.colliderect(block):
                if self.vy > 0:
                    self.rect.bottom = block.top
                    self.vy = 0.0
                    self.on_ground = True
                    self.image_rect.center = self.rect.center

    def draw(self, screen):
        """
        炎の敵を描画（image_rect を用いる既存の描画仕様に合わせる）
        """
        screen.blit(self.image, self.image_rect)

class SlotWeapon(pygame.sprite.Sprite):
    """
    スロットから発射される弾（直線移動・追尾無し）
    コンストラクタで位置と速度を受け取り、update で等速移動する。
    """
    def __init__(self, sx: int, sy: int, vx: float, vy: float):
        super().__init__()
        weapon_img = pygame.image.load("fig/slot_weapon.png")
        angle = math.degrees(math.atan2(-vy, vx))
        self.image = pygame.transform.rotozoom(weapon_img, angle, 0.125)
        self.rect = self.image.get_rect()
        self.rect.center = (int(sx), int(sy))
        self.vx = float(vx)
        self.vy = float(vy)

    def update(self, blocks=None):
        # 等速直線移動（blocks は仕様互換のため受け取るが使用しない）
        # move_ip を使って移動（浮動小数の扱いは Rect 側で整数化される）
        self.rect.move_ip(int(self.vx), int(self.vy))

    def draw(self, screen):
        screen.blit(self.image, self.rect)

class FireWeapon(pygame.sprite.Sprite):
    """
    炎の敵から発射される弾（X軸等速、Y軸は正弦波で揺れる）
    """
    def __init__(self, sx: int, sy: int, vx: float):
        super().__init__()
        weapon_img = pygame.image.load("fig/fire.png")  # 弾の画像（要作成）
        self.image = pygame.transform.rotozoom(weapon_img, 0, 0.125)
        self.rect = self.image.get_rect()
        self.rect.center = (int(sx), int(sy))
        self.vx = float(vx)  # X方向速度（一定）
        self.base_y = float(sy)  # Y座標の基準位置
        self.time = 0  # 正弦波の時間パラメータ
        
    def update(self, blocks=None):
        """
        X軸: 等速直線運動
        Y軸: 基準位置から±10の範囲で正弦波移動
        """
        self.rect.x += int(self.vx)
        # 正弦波でY座標を変化（振幅10ピクセル）
        self.time += 0.1
        self.rect.y = int(self.base_y + math.sin(self.time) * 10)

    def draw(self, screen):
        screen.blit(self.image, self.rect)

map_data = [
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
]

# 3. ステージの「当たり判定用の四角形(Rect)」リストを作成
# (ゲーム開始時に一度だけ計算する)
block_rects = []
for y, row in enumerate(map_data):
    for x, tile_type in enumerate(row):
        if tile_type == 1:
            # (x座標, y座標, 幅, 高さ) のRectを作成
            block_rects.append(pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE))

# 4. プレイヤー設定
# プレイヤーを (幅20, 高さ40) の四角形として定義
player_rect = pygame.Rect(100, 100, TILE_SIZE // 2, TILE_SIZE) # 初期位置(100,100)
player_velocity_y = 0  # プレイヤーの垂直方向の速度
is_on_ground = False     # 地面（ブロック）に接地しているか
player_move_left = False # 左に移動中か
player_move_right = False# 右に移動中か

# --- 追加: フレームタイマーをここで初期化（tmrが使用される前に必ず定義） ---
tmr = 0

# 爆弾の敵
bomb_enemies = pygame.sprite.Group()
bomb_enemy = BombEnemy()
bomb_enemies.add(bomb_enemy)

# 炎の敵を追加
fire_enemies = pygame.sprite.Group()
fire_enemy = FireEnemy()
fire_enemies.add(fire_enemy)

# 炎の弾のグループを追加
fire_weapons = pygame.sprite.Group()

# 投げた爆弾のグループ
bombs = pygame.sprite.Group()

# ここにスロット敵用のグループを追加
slot_enemies = pygame.sprite.Group()
# スロットから発射される弾のグループ
slot_weapons = pygame.sprite.Group()
# --- 追加：最初から座標でスロット敵を生成して配置（必要に応じて座標を編集してください） ---
#SLOT_INITIAL_POSITIONS = [
#    (900, 150),
#]
#
#for pos in SLOT_INITIAL_POSITIONS:
#    sx, sy = pos
#    # コンストラクタで初期座標を与えて生成（BombEnemy と同じようにクラスから初期位置設定可能）
#    slot = SlotEnemy(sx, sy)
#    slot_enemies.add(slot)
slot_enemies.add(SlotEnemy())

# タイマーを初期化（tmr が未定義だったため追加）
tmr = 0

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
            if event.key == pygame.K_UP and is_on_ground:
                player_velocity_y = JUMP_STRENGTH # 上向きの速度を与える
                is_on_ground = False
        
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
    if player_move_right:
        player_movement_x += PLAYER_SPEED
    
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

    # 爆弾の敵がプレイヤーに向かって投げる1〜2秒ごとに
    for b_enemy in bomb_enemies:
        if tmr >= b_enemy.next_throw:
            bombs.add(Bomb(b_enemy))
            b_enemy.next_throw = tmr + random.randint(60, 120)

    # SlotEnemy からの発射処理（直線、同じ速さ、追尾なし）
    for s in slot_enemies:
        # s.next_shot はフレームカウント (tmr) ベース
        if tmr >= getattr(s, "next_shot", 0):
            # 位置は s.image_rect.center を起点にする
            sx, sy = s.image_rect.center
            # プレイヤー方向へ向かわせる（追尾しない -> 初速のみ設定）
            dx = player_rect.centerx - sx
            dy = player_rect.centery - sy
            dist = math.hypot(dx, dy)
            if dist == 0:
                vx = 0.0
                vy = 0.0
            else:
                vx = dx / dist * s.weapon_speed
                vy = dy / dist * s.weapon_speed
            # 弾を生成してグループへ追加
            slot_weapons.add(SlotWeapon(sx, sy, vx, vy))
            # 次の発射タイミングを設定（ランダム間隔）
            s.next_shot = tmr + random.randint(90, 240)
            
    # 炎の敵から発射処理
    for f_enemy in fire_enemies:
        if tmr >= getattr(f_enemy, "next_shot", 0):
            # 発射位置を設定（敵の中心から）
            sx, sy = f_enemy.image_rect.center
            # プレイヤーの方向に応じて速度の符号を決定
            vx = f_enemy.weapon_speed
            if player_rect.centerx < f_enemy.rect.centerx:
                vx = -f_enemy.weapon_speed
                # 左向きの場合、敵の左側から発射
                sx = f_enemy.rect.left - 5
            else:
                # 右向きの場合、敵の右側から発射
                sx = f_enemy.rect.right + 5
            
            # 弾を生成してグループへ追加（Y座標はそのまま中心を使用）
            fire_weapons.add(FireWeapon(sx, sy, vx))
            # 次の発射タイミングを設定
            f_enemy.next_shot = tmr + random.randint(90, 240)

    # 8. 描画処理
    screen.fill(WHITE) # 画面を黒で塗りつぶし
    
    # ステージ（ブロック）を描画
    for block in block_rects:
        pygame.draw.rect(screen, BLACK, block)
        
    # プレイヤーを描画
    pygame.draw.rect(screen, GREEN, player_rect)
    
    # 爆弾の敵の更新と描画
    for b_enemy in bomb_enemies:
        b_enemy.update(block_rects)
        b_enemy.draw(screen)

    # 炎の敵の更新と描画
    for f_enemy in fire_enemies:
        f_enemy.update(block_rects)
        f_enemy.draw(screen)

    # 投げられた爆弾の更新と描画
    for b in list(bombs):
        b.update(block_rects)
        b.draw(screen)
    
    # SlotEnemy の弾を更新・描画（画面外に出たら削除）
    for w in list(slot_weapons):
        w.update(block_rects)
        w.draw(screen)
        # 画面外チェックで削除
        if w.rect.right < 0 or w.rect.left > SCREEN_WIDTH or w.rect.bottom < 0 or w.rect.top > SCREEN_HEIGHT:
            slot_weapons.remove(w)
    
    # SlotEnemy を描画（爆弾の上に表示したいので爆弾描画の後に描画する）
    for s in slot_enemies:
        s.draw(screen)

    # 炎の弾の更新と描画
    for w in list(fire_weapons):
        w.update()
        w.draw(screen)
        # 画面外チェックで削除
        if w.rect.right < 0 or w.rect.left > SCREEN_WIDTH:
            fire_weapons.remove(w)

    # 画面を更新
    pygame.display.flip()
    
    # 9. FPS (フレームレート) の制御
    clock.tick(60) # 1秒間に60回ループが回るように調整
    # タイマーを進める
    tmr += 1

# ループが終了したらPygameを終了
pygame.quit()