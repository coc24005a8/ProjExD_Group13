import os
import sys
import time
import pygame as pg


os.chdir(os.path.dirname(os.path.abspath(__file__)))
pg.mixer.init()  # 初期化

def main():
    # 効果音を読み込む
    effect = pg.mixer.Sound("sound/boom.wav")  # 爆発音
    # 再生（非同期で一時的に鳴る）
    effect.play()  # 即再生され，終わったら自動で停止
    effect.play(maxtime=1000)  # 1000ミリ秒で強制停止

    # BGMの読み込み
    pg.mixer.music.load("sound/house_lo.wav")
    # 再生（ループなしバージョン）
    pg.mixer.music.play()  
    time.sleep(10)  # 10秒間だけ流す（プログラム側で制御）
    pg.mixer.music.stop()  # 停止
    # 再生（ループありバージョン）
    pg.mixer.music.play(loops=-1)


if __name__ == "__main__":
    pg.init()
    main()
    pg.quit()
    sys.exit()