import pygame as pg
import os
import sys
import random

#ーーーーーーーーー1.定数と初期設定ーーーーーーーーー
os.chdir(os.path.dirname(os.path.abspath(__file__)))

SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600 # 画面のサイズ
LEFT_BOUND, RIGHT_BOUND = SCREEN_WIDTH // 3, SCREEN_WIDTH * 2 // 3 # スクロール判定
TILE_SIZE_X, TILE_SIZE_Y = 100, 40 # タイルのサイズ
ADD_STAGE_BLOCK = 100 # ステージの拡張幅
GRAVITY = 0.8         # 重力
JUMP_STRENGTH = -15   # ジャンプ力 (Y軸は上がマイナス)
PLAYER_SPEED = 5      # 左右の移動速度
ENEMY_NUM = 1         # 敵の数
#ーーーーーーーーーーーーーーーーーーーーーーーーーー


def extend(map_data: "list[list[int]]", add_stage_width: "int", probs: "list[int]") -> list[list[int]]:
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

def ground_surface(map_data: "list[list[int]]") -> "list[list[int]]":
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

def make_float_land(map_data: "list[list[int]]", add_range: "tuple[int]", num: "int") -> "list[list[int]]":
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
    return map_data

def hover(instance: "Player"):
    instance.vy -= 15

def walled(instance: "object", blocks: "list[tuple[object, int]]") -> None:
    """
    壁衝突判定を行う関数
    内容: 壁に衝突したとき、自身の位置を壁端に合わせる。
    引数: 衝突判定を行うオブジェクト, 衝突するブロックを保持したリスト
    """
    for block, type in blocks:
        if instance.rect.colliderect(block): 
            if instance.movex > 0: # 右に移動中に衝突
                instance.rect.right = block.left # 右端をブロックの左端に合わせる
            elif instance.movex < 0: # 左に移動中に衝突
                instance.rect.left = block.right # 左端をブロックの右端に合わせる
            instance.movex *= -1
            instance.world[0] = instance.rect.x

def gravity(instance: "object", blocks: "list[tuple[object, int]]") -> None:
    """
    重力を適用し、地面との衝突判定を行う関数
    内容: 地面にぶつかった際、y方向の速度を0にし、座標を地面の上に合わせる
    引数: 重力を適用するオブジェクト, ブロックのリスト
    """
    instance.vy += GRAVITY # 重力を速度に加算
    instance.world[1] += instance.vy # Y方向に動かす
    instance.rect.y = instance.world[1]
    instance.is_on_ground = False # 毎フレーム「接地していない」と仮定
    instance.in_on_float = False
    
    for block in blocks:
        if instance.rect.colliderect(block[0]):
                if instance.vy > 0: # 落下中に衝突
                    instance.rect.bottom = block[0].top # 足元をブロックの上端に合わせる
                    instance.world[1] = instance.rect.y
                    instance.hover_num = 0
                    instance.vy = 0 # 落下速度をリセット
                    if block[1] == 2:
                        instance.is_on_ground = True   # 接地フラグを立てる
                    elif block[1] == 3:
                        instance.is_on_float = True
                elif instance.vy < 0: # ジャンプ中に衝突
                    instance.rect.top = block[0].bottom # 頭をブロックの下端に合わせる
                    instance.world[1] = instance.rect.y
                    instance.vy = 0 # 上昇速度をリセット（頭を打った）
 
class Assets:
    def __init__(self):
        self.bg = pg.image.load("fig/night_plain_bg.png")
        self.ground = pg.image.load("fig/ground2.png")
        self.weeds = pg.image.load("fig/weeds(extend).png")
        self.cloud = pg.image.load("fig/cloud(extend).png")

class Player(pg.sprite.Sprite):
    """
    操作キャラクターのクラス
    """
    def __init__(self):
        super().__init__()
        self.img = pg.image.load("fig/yoko1.png")
        # self.img = pg.transform.rotozoom(self.img, 0,)
        self.flip = pg.transform.flip(self.img, True, False)
        self.dire_img = {(1, 0) : self.img, (-1, 0) : self.flip}
        self.rect = self.img.get_rect()
        self.vy = 0
        self.movex = 0
        self.world = [self.rect.centerx, self.rect.centery]
        self.screen_x = 0
        self.direct = (1, 0)
        self.hover_num = 0
        self.is_on_ground = False
        self.is_on_float = False
        self.move_left = False
        self.move_right = False
    
    def update(self, stage_width: "int", block_rect, camera_x: "int") -> "int":
        """
        自身の座標を更新する関数
        内容: キーに合わせて自身が移動する。移動に合わせてカメラ座標も取得する
        戻り値: カメラ用の係数       
        """  
        self.movex = 0
        if self.move_left:
            self.movex -= PLAYER_SPEED
            self.direct = (-1, 0)
        if self.move_right:
            self.movex += PLAYER_SPEED
            self.direct = (1, 0)

        self.rect.x += self.movex # まずX方向に動かす
        self.screen_x = self.rect.x - camera_x # 画面内のプレイヤーの位置を確認
        if self.screen_x < LEFT_BOUND: # プレイヤーが左端ならカメラの位置を左にずらす
            camera_x = self.rect.x - LEFT_BOUND
        elif self.screen_x > RIGHT_BOUND: #プレイヤーが右端ならカメラの位置を右にずらす
            camera_x = self.rect.x - RIGHT_BOUND
        max_camera_x = stage_width * TILE_SIZE_X - SCREEN_WIDTH #カメラの動く範囲を総タイル数と画面のサイズから計算
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

class Enemy(pg.sprite.Sprite):
    """
    敵を司るクラス
    """
    def __init__(self, stage_width):
        super().__init__()
        self.image = pg.image.load("fig/troia.png")
        # self.iamge = pg.transform.rotozoom(self.img, 0, 0.1) # 修正予定 画像サイズは元画像の変更の方がよい
        self.rect = self.image.get_rect()
        # self.rect.center = (random.randrange(SCREEN_WIDTH, TILE_SIZE_X * stage_width), random.randrange(0, SCREEN_HEIGHT - (TILE_SIZE_Y * 5)))
        self.world = [400, 0] 
        self.movex = 1
        self.vy = 0
        
        self.is_on_ground = False

    def update(self, camera_x: "int") -> None:
        """
        自身の位置を更新する関数
        """
        # print(camera_x)
        # self.rect.x -= scroll_speed
        self.world[0] -= self.movex
        self.rect.x = self.world[0]
        self.rect.y = self.world[1]
        # self.rect.center = (self.rect.centerx - self.movex, self.rect.centery)        
        self.rect.x = self.world[0] - camera_x

class Goal(pg.sprite.Sprite):
    def __init__(self):
        super().__init__()
        # self.image = pg.image.load("")

class Score:
    def __init__(self):
        self.pic = pg.font.Font(None, 80)
        self.value = 0
        # txt = self.pic.render(f"スコア: {self.value}", True, (255, 255, 255))
    
    def update(self):
        self.txt = self.pic.render(f"Score: {self.value}", True, (255, 255, 255))


def main():
    # 画面設定
    screen = pg.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pg.display.set_caption("2Dアクションゲーム デモ")
    clock = pg.time.Clock()

    bg_img = pg.image.load("fig/night_plain_bg.png")
    # bg_flip = pg.transform.flip(bg_img, True, False)
    bg_width = bg_img.get_width()
    pg.mixer.music.load("fig/魔王魂(ファンタジー).mp3")
    pg.mixer.music.play(loops = -1)

    # ground = Ground()
    ground_img = pg.image.load("fig/ground2.png")
    weeds_img = pg.image.load("fig/weeds(extend).png")
    cloud_img = pg.image.load("fig/cloud(extend).png")
    # ground_rect = ground

    # 2. ステージデータ (0=空, 1=ブロック)
    # 画面下部が地面、途中に浮島があるマップ
    map_data = [
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

    probs = [0.5, 0.7, 0.9, 1.0, 1.0]


    # 3. ステージの「当たり判定用の四角形(Rect)」リストを作成
    # (ゲーム開始時に一度だけ計算する)
    map_data = extend(map_data, ADD_STAGE_BLOCK, probs)
    map_data = ground_surface(map_data)
    map_data = make_float_land(map_data, (6,10), 10)
    block_rects = []
    surface_rects = []
    floatland_rects = []
    for y, row in enumerate(map_data):
        for x, tile_type in enumerate(row):
            if tile_type == 1:
                # (x座標, y座標, 幅, 高さ) のRectを作成
                # block_rects.append(())
                block_rects.append((pg.Rect(x * TILE_SIZE_X, y * TILE_SIZE_Y, TILE_SIZE_X, TILE_SIZE_Y), 1))
            elif tile_type == 2:
                surface_rects.append((pg.Rect(x * TILE_SIZE_X, y * TILE_SIZE_Y + (TILE_SIZE_Y / 2), TILE_SIZE_X, TILE_SIZE_Y / 2), 2))
            elif tile_type == 3:
                floatland_rects.append((pg.Rect(x * TILE_SIZE_X, y * TILE_SIZE_Y + (TILE_SIZE_Y / 2), TILE_SIZE_X, TILE_SIZE_Y / 2), 3))
    # 4. プレイヤー設定
    player = Player() #プレイヤー
    enemys = pg.sprite.Group()
    for i in range(ENEMY_NUM):
        enemys.add(Enemy(len(map_data[0])))
    score = Score()
    
    camera_x = 0 #カメラの位置を初期化

    # 5. ゲームループ
    running = True
    while running:
        
        # 6. イベント処理 (キー操作など)
        for event in pg.event.get():
            if event.type == pg.QUIT:
                running = False
            
            # キーが押された時
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_LEFT:
                    player.move_left = True
                if event.key == pg.K_RIGHT:
                    player.move_right = True
                if event.key == pg.K_SPACE: #and player.is_on_ground:
                    # player.vy = JUMP_STRENGTH # 上向きの速度を与える
                    player.hover()
                    print("hoverd")
                    player.is_on_ground = False
            
            # キーが離された時
            if event.type == pg.KEYUP:
                if event.key == pg.K_LEFT:
                    player.move_left = False
                if event.key == pg.K_RIGHT:
                    player.move_right = False

        # 7. プレイヤーのロジック更新 (移動と当たり判定)
                # X方向の衝突チェック
        
        # for block in surface_rects:
        #     if player.rect.colliderect(block[0]):
        #         if player.movex > 0: # 右に移動中に衝突
        #             player.rect.right = block[0].left # 右端をブロックの左端に合わせる
        #         elif player.movex < 0: # 左に移動中に衝突
        #             player.rect.left = block[0].right # 左端をブロックの右端に合わせる

        # for block in block_rects:
        #     if player.rect.colliderect(block[0]):
        #         if player.movex > 0: # 右に移動中に衝突
        #             player.rect.right = block[0].left # 右端をブロックの左端に合わせる
        #         elif player.movex < 0: # 左に移動中に衝突
        #             player.rect.left = block[0].right # 左端をブロックの右端に合わせる
        
        # for block in floatland_rects:
        #     if player.rect.colliderect(block[0]):
        #         if player.movex > 0: # 右に移動中に衝突
        #             player.rect.right = block[0].left # 右端をブロックの左端に合わせる
        #         elif player.movex < 0: # 左に移動中に衝突
        #             player.rect.left = block[0].right # 左端をブロックの右端に合わせる
        
        # player.vy += GRAVITY # 重力を速度に加算
        # player.rect.y += player.vy
        all_blocks = surface_rects + floatland_rects
        walled(player, all_blocks)
        gravity(player, all_blocks)
        for i in enemys:
            walled(i, all_blocks)
            gravity(i, all_blocks)
        # gravity(player,floatland_rects)

        # 8. 描画処理
        # screen.fill((255, 255, 255)) # 画面を黒で塗りつぶし
        



        

        # プレイヤーを描画
        prev_camera_x = camera_x
        camera_x = player.update(len(map_data[0]), [surface_rects, floatland_rects], camera_x)
        scroll_x = -camera_x % bg_width
        scroll_speed = camera_x - prev_camera_x
        # print(camera_x)
        
        screen.blit(bg_img, (scroll_x - bg_width, -100))
        screen.blit(bg_img, (scroll_x, -100))
        screen.blit(player.dire_img[player.direct], (player.rect.x - camera_x, player.rect.y))
        enemys.update(camera_x)
        # enemys.update(scroll_speed)
        for enemy in enemys:
            screen.blit(enemy.image, (enemy.rect.centerx - camera_x, enemy.rect.centery))
        # ステージ（ブロック）を描画
        for block, type in block_rects:
            draw_rect = pg.Rect(
                block.x - camera_x, #ブロックの出現位置を調整
                block.y,
                block.width,
                block.height
            )
            # pg.draw.rect(screen, BROWN, draw_rect)
            screen.blit(ground_img, (block.x - camera_x, block.y, block.width, block.height))
        for block, type in surface_rects:
            draw_rect = pg.Rect(
                block.x - camera_x,
                block.y,
                block.width,
                block.height
            )
            # pg.draw.rect(screen, (0, 0, 0, 128), draw_rect)
            screen.blit(weeds_img, (block.x - camera_x,block.y))
        for block,type in floatland_rects:
            # draw_rect = pg.Rect(                
            #     block.x - camera_x,
            #     block.y,
            #     block.width,
            #     block.height)
            # pg.draw.rect(screen, (255, 255, 255), draw_rect)
            screen.blit(cloud_img, (block.x - camera_x, block.y))
        # 画面を更新
        # pg.display.flip()
        score.update()
        screen.blit(score.txt, (SCREEN_WIDTH / 10, SCREEN_HEIGHT - SCREEN_HEIGHT / 10))
        pg.display.update()
        
        # 9. FPS (フレームレート) の制御
        clock.tick(60) # 1秒間に60回ループが回るように調整

# ループが終了したらPygameを終了
if __name__ == "__main__":
    pg.init()
    main()
    pg.quit()
    sys.exit()
