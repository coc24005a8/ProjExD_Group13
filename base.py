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
    爆弾の敵に関するクラス
    """
    def __init__(self):
        """
        爆弾の敵を初期化する
        """
        super().__init__()
        bomb_img = pygame.image.load("fig/bakudan.png")
        self.image = pygame.transform.rotozoom(bomb_img, 0, 0.125)  # 画像の設定
        self.rect = pygame.Rect(800, 300, TILE_SIZE, TILE_SIZE)  # 初期位置(100,100)と当たり判定用のrect
        self.image_rect = self.image.get_rect()  # 画像表示用のrect
        self.image_rect.center = self.rect.center # 画像を表示する用の中心を設定
        self.vy = 0  # 垂直方向の速度
        self.on_ground = []
        self.next_throw = random.randint(60, 120)

    def update(self, blocks):
        """
        爆弾の敵と地面との判定
        """
        # 重力
        if not self.on_ground:
            self.vy += GRAVITY
            self.rect.y += self.vy

        # 地面との当たり判定
        self.on_ground = False
        for block in blocks:
            if self.rect.colliderect(block):
                if self.vy > 0:  # 下方向に移動中の場合
                    self.rect.bottom = block.top
                    self.vy = 0
                    self.on_ground = True

    def draw(self, screen):
        """
        爆弾の敵を描画する
        """
        screen.blit(self.image, self.image_rect)

    def get_throw_velocity(self) -> tuple[float, float]:
        """
        プレイヤーの位置に向かって投げるときの初速ベクトル
        プレイヤーの現在の位置を参照して方向を決める。
        """
        dx = player_rect.centerx - self.rect.centerx
        dy = player_rect.centery - self.rect.centery
        dist = math.hypot(dx, dy)
        if dist == 0:
            return 0.0, 0.0
        # 基本投射速度
        speed = 8.0
        vx = dx / dist * speed
        vy = dy / dist * speed
        return vx, vy


# タイマー（爆弾を投げる間隔）
tmr = 0
class Bomb(pygame.sprite.Sprite):
    """
    爆弾に関するクラス
    """
    def __init__(self, bomb_enemy: BombEnemy):
        """
        爆弾画像を生成する
        引数 bomb_enemy：爆弾を投げる爆弾の敵
        """
        super().__init__()
        # 速度ベクトルを取得
        vx, vy = bomb_enemy.get_throw_velocity()
        self.vx = vx
        self.vy = vy
        # 画像の読み込みと角度調整
        bomb_img = pygame.image.load("fig/bom3.png")
        angle = math.degrees(math.atan2(-self.vy, self.vx))
        self.image = pygame.transform.rotozoom(bomb_img, angle, 0.125)
        self.rect = self.image.get_rect()
        self.rect.center = bomb_enemy.image_rect.center
        offset = max(bomb_enemy.rect.width, bomb_enemy.rect.height) // 2 + 6
        if vx == 0 and vy == 0:
            pass
        else:
            self.rect.centerx += int(vx / (math.hypot(vx, vy)) * offset)
            self.rect.centery += int(vy / (math.hypot(vx, vy)) * offset)

    def update(self, blocks):
        """
        爆弾の移動とブロックとの当たり判定
        """
        # 速度を位置へ適用
        # 重力を少し加える（落下を表現）
        self.vy += GRAVITY * 0.5
        self.rect.x += int(self.vx)
        self.rect.y += int(self.vy)

    def draw(self, screen):
        screen.blit(self.image, self.rect)

# 2. ステージデータ (0=空, 1=ブロック)
# 画面下部が地面、途中に浮島があるマップ 元のマップデータ
# map_data = [ 
#     [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
#     [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
#     [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
#     [0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
#     [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
#     [0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0],
#     [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
#     [1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 0],
#     [1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
#     [1, 1, 1, 1, 1, 1, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
#     [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
#     [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
#     [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
#     [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
#     [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
# ]

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

# 爆弾の敵
bomb_enemies = pygame.sprite.Group()
bomb_enemy = BombEnemy()
bomb_enemies.add(bomb_enemy)
# 投げた爆弾のグループ
bombs = pygame.sprite.Group()

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
    for enemy in bomb_enemies:
        if tmr >= enemy.next_throw:
            bombs.add(Bomb(enemy))
            enemy.next_throw = tmr + random.randint(60, 120)

    # 8. 描画処理
    screen.fill(WHITE) # 画面を黒で塗りつぶし
    
    # ステージ（ブロック）を描画
    for block in block_rects:
        pygame.draw.rect(screen, BLACK, block)
        
    # プレイヤーを描画
    pygame.draw.rect(screen, GREEN, player_rect)
    
    # 爆弾の敵の更新と描画
    for enemy in bomb_enemies:
        enemy.update(block_rects)
        enemy.draw(screen)
    # 投げられた爆弾の更新と描画
    for b in list(bombs):
        b.update(block_rects)
        b.draw(screen)
    
    # 画面を更新
    pygame.display.flip()
    
    # 9. FPS (フレームレート) の制御
    clock.tick(60) # 1秒間に60回ループが回るように調整
    # タイマーを進める
    tmr += 1

# ループが終了したらPygameを終了
pygame.quit()