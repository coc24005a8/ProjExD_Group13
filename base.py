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
PLAYER_HP = 3
NO_DAMAGE_TIME = 2
PLAYER_POWER = 10
ENEMY_NUM = 1         # 敵の数
ENEMY_SPEED = 1
#ーーーーーーーーーーーーーーーーーーーーーーーーーー
#---まだ
def start_page():
    pass
#------

#---まだ
def gameover():
    pass
#------

#---まだ
def game_clear():
    pass
#------

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

#---修正
def walled(instance: "object", blocks: "list[tuple[object, int]]", camera_x: "int") -> None:
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
def gravity(instance: "object", blocks: "list[tuple[object, int]]") -> None:
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
        self.probs = [0.5, 0.7, 0.9, 1.0, 1.0]

#---修正
class Player(pg.sprite.Sprite):
    """
    操作キャラクターのクラス
    """
    def __init__(self):
        super().__init__()
        
        self.img = pg.image.load("fig/yoko1.png")
        self.flip = pg.transform.flip(self.img, True, False)
        self.rect = self.img.get_rect()
        self.vx = 0
        self.vy = 0
        self.dire = (1, 0)
        self.dire_to_img = {(1, 0) : self.img, (-1, 0) : self.flip}

        self.hover_num = 0
        self.hp = PLAYER_HP
        self.no_damage_time = NO_DAMAGE_TIME
        self.power = PLAYER_POWER

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
            self.dire = (-1, 0)
        if self.move_right:
            self.vx = PLAYER_SPEED
            self.dire = (1, 0)

        self.rect.x += self.vx

        walled(self, all_blocks, camera_x)
        gravity(self, floar_blocks)


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
#---

#---修正
class Enemy(pg.sprite.Sprite):
    """
    敵を司るクラス
    """
    def __init__(self):
        super().__init__()

        self.image = pg.image.load("fig/troia(extend).png")
        self.flip = pg.transform.flip(self.image, True, False)
        self.rect = self.image.get_rect()
        self.rect.center = (1000, 0) #テスト用で定数
        self.vx = ENEMY_SPEED
        self.vy = 0
        self.dire = (1, 0)
        self.dire_to_img = {(1, 0): self.image, (-1, 0): self.flip}

        self.hp = 5
        self.power = 1
        
        self.is_on_ground = True
        self.is_move_left, self.is_move_right = True, False

    def update(self, all_blocks: "list[object]", floar_blocks: "list[object]", camera_x: "int") -> None:
        """
        自身の位置を更新する関数
        """
        self.rect.x -= self.vx

        for block in all_blocks:
            if self.rect.colliderect(block):
                print("irregular")
                print(f"敵の速度{self.vx}")
                self.vx *= -1
                print(f"敵の速度{self.vx}")
        gravity(self, floar_blocks)
#------

#---まだ
class Goal(pg.sprite.Sprite):
    def __init__(self):
        super().__init__()
        # self.image = pg.image.load("")
#------

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
                surface_rects.append(pg.Rect(x * TILE_SIZE_X, y * TILE_SIZE_Y + (TILE_SIZE_Y / 2), TILE_SIZE_X, TILE_SIZE_Y / 2))
            elif tile_type == 3:
                floatland_rects.append(pg.Rect(x * TILE_SIZE_X, y * TILE_SIZE_Y + (TILE_SIZE_Y / 2), TILE_SIZE_X, TILE_SIZE_Y / 2))


    floar_blocks = surface_rects + floatland_rects
    all_blocks = block_rects + floar_blocks
    
    enemys = pg.sprite.Group()

    player = Player() 
    for i in range(ENEMY_NUM):
        enemys.add(Enemy())
    score = Score()
    
    camera_x = 0

    #ーーーーーゲームスタートーーーーー
    while True:
    
        #ーーーーーイベント取得ーーーーー
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
                    player.is_on_ground = False
            
            # キーが離された時
            if event.type == pg.KEYUP:
                if event.key == pg.K_LEFT:
                    player.vx = 0
                    player.move_left = False
                if event.key == pg.K_RIGHT:
                    player.vx = 0
                    player.move_right = False
        #ーーーーーーーーーーーーーーーー

        #----修正
        camera_x = player.update(len(map_data[0]), all_blocks, floar_blocks, camera_x)
        scroll_x = -camera_x % bg_width
        #-------

        screen.blit(bg_img, (scroll_x - bg_width, -100))
        screen.blit(bg_img, (scroll_x, -100))
        #---修正
        screen.blit(player.dire_to_img[player.dire], (player.rect.x - camera_x, player.rect.y))
        enemys.update(all_blocks, floar_blocks, camera_x)
        for enemy in enemys:
            screen.blit(enemy.image, (enemy.rect.centerx - camera_x, enemy.rect.centery))
        #------

        for block in block_rects:
            screen.blit(assets.ground, (block.x - camera_x, block.y, block.width, block.height))
        for block in surface_rects:
            screen.blit(assets.weeds, (block.x - camera_x,block.y))
        for block in floatland_rects:
            screen.blit(assets.cloud, (block.x - camera_x, block.y))

        score.update()
        screen.blit(score.txt, (SCREEN_WIDTH / 10, SCREEN_HEIGHT - SCREEN_HEIGHT / 10))
        
        pg.display.update()
        clock.tick(60)

if __name__ == "__main__":
    pg.init()
    main()
    pg.quit()
    sys.exit()