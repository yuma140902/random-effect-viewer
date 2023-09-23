import argparse
import pathlib
import random

from PIL import Image, ImageTk
import cv2
from cv2.typing import MatLike
import numpy as np

import tkinter as tk
from tkinter import messagebox
import tkinter.ttk as ttk

win_width = 1600
win_height = 900

class ScrollableFrame(tk.Frame):
    def __init__(self, parent, minimal_canvas_size):
        tk.Frame.__init__(self, parent)

        self.minimal_canvas_size = minimal_canvas_size

        # 縦スクロールバー
        vscrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL)
        vscrollbar.pack(fill=tk.Y, side=tk.RIGHT, expand=False)

        # 横スクロールバー
        hscrollbar = ttk.Scrollbar(self, orient=tk.HORIZONTAL)
        hscrollbar.pack(fill=tk.X, side=tk.BOTTOM, expand=False)

        # Canvas
        self.canvas = tk.Canvas(self, bd=0, highlightthickness=0,
            yscrollcommand=vscrollbar.set, xscrollcommand=hscrollbar.set)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # スクロールバーをCanvasに関連付け
        vscrollbar.config(command=self.canvas.yview)
        hscrollbar.config(command=self.canvas.xview)

        # Canvasの位置の初期化
        self.canvas.xview_moveto(0)
        self.canvas.yview_moveto(0)

        # スクロール範囲の設定
        self.canvas.config(scrollregion=(0, 0, self.minimal_canvas_size[0], self.minimal_canvas_size[1]))

        # Canvas内にフレーム作成
        self.interior = tk.Frame(self.canvas)
        self.canvas.create_window(0, 0, window=self.interior, anchor='nw')

        # 内部フレームの大きさが変わったらCanvasの大きさを変える関数を呼び出す
        self.interior.bind('<Configure>', self._configure_interior)

    # Canvasの大きさを変える関数
    def _configure_interior(self, event):
        size = (max(self.interior.winfo_reqwidth(), self.minimal_canvas_size[0]),
            max(self.interior.winfo_reqheight(), self.minimal_canvas_size[1]))
        self.canvas.config(scrollregion=(0, 0, size[0], size[1]))
        if self.interior.winfo_reqwidth() != self.canvas.winfo_width():
            self.canvas.config(width = self.interior.winfo_reqwidth())
        if self.interior.winfo_reqheight() != self.canvas.winfo_height():
            self.canvas.config(height = self.interior.winfo_reqheight())

class Application(tk.Frame):
    def __init__(self, master: tk.Tk, path: pathlib.Path):

        super().__init__(master)
        self.isMouseDown = False
        self.prevPos = (0.0, 0.0)
        self.offsetX = 0.0
        self.offsetY = 0.0
        self.path = path

        self.master = master
        self.master.title('scrollbar trial')
        self.master.geometry(f"{win_width}x{win_height}")
        self.pack(fill=tk.BOTH, expand=True)
        self.create_widgets()

    def create_widgets(self):
        self.canvas_frame = ScrollableFrame(self, [100, 100])
        self.canvas_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.control_frame = tk.Frame(self)
        self.control_frame.pack(side=tk.TOP, fill=tk.Y, expand=False)

        ttk.Label(self.control_frame, text="フィルター:").pack()
        self.filt_name = tk.StringVar()
        ttk.Label(self.control_frame, textvariable=self.filt_name).pack()

        ttk.Label(self.control_frame, text="").pack()

        btn = tk.Button(self.control_frame, text="ランダム")
        btn.pack()
        btn.bind("<ButtonPress-1>", self.handleRandomFilterBtn)

        ttk.Label(self.control_frame, text="").pack()

        btn = tk.Button(self.control_frame, text="永続化")
        btn.pack()
        btn.bind("<ButtonPress-1>", self.handlePersistBtn)

        ttk.Label(self.control_frame, text="").pack()

        for filt in filt_list:
            self.registerFilterButton(filt)

        self.canvas_frame.canvas.bind("<ButtonPress-1>", self.mouseDown)
        self.canvas_frame.canvas.bind("<ButtonRelease>", self.mouseRelease)
        self.canvas_frame.canvas.bind("<Motion>", self.mouseMove)
        self.canvas_frame.canvas.bind("<MouseWheel>", self.mouseWheel)

        ttk.Label(self.control_frame, text="").pack()

        btn = tk.Button(self.control_frame, text="保存")
        btn.pack()
        btn.bind("<ButtonPress-1>", self.handleSaveBtn)

        self.status_str = tk.StringVar()
        ttk.Label(self.control_frame, textvariable=self.status_str).pack()

        btn = tk.Button(self.control_frame, text="クリア")
        btn.pack()
        btn.bind("<ButtonPress-1>", self.handleClearStatusBtn)

        # canvasに画像をセットする

        # [Python OpenCV の cv2.imread 及び cv2.imwrite で日本語を含むファイルパスを取り扱う際の問題への対処について - Qiita](https://qiita.com/SKYS/items/cbde3775e2143cad7455)
        n = np.fromfile(self.path, np.uint8)
        image = cv2.imdecode(n, cv2.IMREAD_COLOR)
        self.image_cv = cv2.cvtColor(image, cv2.COLOR_BGR2RGB) # imreadはBGRなのでRGBに変換
        # デフォルトの倍率
        self.scale = np.min([win_width / image.shape[1], win_height / image.shape[0]])
        self.filt = get_random_filt()
        self.update_filt()

    def registerFilterButton(self, filt):
        btn = tk.Button(self.control_frame, text=filt.__name__)
        btn.pack()
        btn.bind("<ButtonPress-1>", self.filterApplyer(filt))

    def filterApplyer(self, filt):
        def f(evt):
            self.filt = filt
            self.update_filt()
        return f


    def update_filt(self):
        self.filt_name.set(self.filt.__name__)
        self.image_cv_filt = self.filt(self.image_cv)
        self.update_pil()

    def update_pil(self):
        self.image_pil = Image.fromarray(self.image_cv_filt)
        self.image_pil = self.image_pil.resize((int(self.image_pil.width * self.scale), int(self.image_pil.height * self.scale)))
        self.image_tk = ImageTk.PhotoImage(image=self.image_pil)
        self.update_canvas()

    def update_canvas(self):
        self.canvas_frame.canvas.delete("main")
        self.canvas_frame.canvas.photo = self.image_tk
        self.canvas_frame.canvas.create_image(self.image_pil.width / 2 + self.offsetX, self.image_pil.height / 2 + self.offsetY, anchor=tk.CENTER, image=self.image_tk, tag="main")

    # def pickup_point(self, event):
    #   self.point_x.set('x : ' + str(event.x))
    #   self.point_y.set('y : ' + str(event.y))
    #   self.point_xc.set('x : ' + str(self.canvas_frame.canvas.canvasx(event.x)))
    #   self.point_yc.set('y : ' + str(self.canvas_frame.canvas.canvasy(event.y)))

    def handleRandomFilterBtn(self, e):
        filt = get_random_filt()
        self.filt = filt
        self.update_filt()

    def handlePersistBtn(self, e):
        self.image_cv = self.image_cv_filt
        self.filt = そのまま
        self.update_filt()

    def handleSaveBtn(self, e):
        while True:
            path = self.path.parent / f"{self.path.stem}_{self.filt.__name__}_{random.randint(0, 2048)}{self.path.suffix}"
            if not path.is_file():
                break

        img = cv2.cvtColor(self.image_cv_filt, cv2.COLOR_RGB2BGR)
        result, n = cv2.imencode(self.path.suffix, img)

        if result:
            with open(path, mode='w+b') as f:
                n.tofile(f)
            self.status_str.set(f"保存: {path.name}")
        else:
            self.status_str.set(f"保存失敗: {path.name}")

    def handleClearStatusBtn(self, e):
        self.status_str.set("")

    def mouseDown(self, e):
        self.prevPos = (e.x, e.y)
        self.isMouseDown = True

    def mouseRelease(self, e):
        self.isMouseDown = False

    def mouseMove(self, e):
        if self.isMouseDown:
            dx = e.x - self.prevPos[0]
            dy = e.y - self.prevPos[1]
            self.prevPos = (e.x, e.y)
            self.offsetX += dx
            self.offsetY += dy
            self.update_canvas()
    
    def mouseWheel(self, e):
        self.scale = self.scale * (1 + e.delta / 1000)
        self.update_pil()


def get_random_filt():
    return random.choice(filt_list)

def そのまま(image: MatLike) -> MatLike:
    return image

def ラインアート(image: MatLike) -> MatLike:
    med_val = np.median(image)
    sigma = 0.33  # 0.33
    min_val = int(max(0, (1.0 - sigma) * med_val))
    max_val = int(max(255, (1.0 + sigma) * med_val))

    lineart = cv2.Canny(image, threshold1 = min_val, threshold2 = max_val)
    lineart = cv2.bitwise_not(lineart)

    if (image.shape[2] == 3):
        lineart = cv2.cvtColor(lineart, cv2.COLOR_GRAY2RGB);
    else:
        lineart = cv2.cvtColor(lineart, cv2.COLOR_GRAY2RGBA);
    return cv2.add(image, lineart)

def グレー(image: MatLike) -> MatLike:
    return cv2.cvtColor(image, cv2.COLOR_RGBA2GRAY)

def コントラスト(image: MatLike) -> MatLike:
    if(image.shape[2] == 4):
        r, g, b, a = cv2.split(image)
        color_only = cv2.merge((r, g, b))
        alpha = random.randrange(start=9, stop=50) / 10
        beta = random.randrange(start=0, stop=10)
        color_only = cv2.convertScaleAbs(color_only, alpha=alpha, beta=beta)
        r, g, b = cv2.split(color_only)
        return cv2.merge((r, g, b, a))
    else:
        alpha = random.randrange(start=8, stop=15) / 10
        beta = random.randrange(start=0, stop=10)
        return cv2.convertScaleAbs(image, alpha=alpha, beta=beta)

def 輪郭強調(image: MatLike) -> MatLike:
    med_val = np.median(image)
    sigma = 0.33  # 0.33
    min_val = int(max(0, (1.0 - sigma) * med_val))
    max_val = int(max(255, (1.0 + sigma) * med_val))

    lineart = cv2.Canny(image, threshold1 = min_val, threshold2 = max_val)

    if (image.shape[2] == 3):
        lineart = cv2.cvtColor(lineart, cv2.COLOR_GRAY2RGB);
    else:
        lineart = cv2.cvtColor(lineart, cv2.COLOR_GRAY2RGBA);
    return cv2.subtract(image, lineart)

def HSV_S(image: MatLike) -> MatLike:
    img_hsv = cv2.cvtColor(image,cv2.COLOR_RGB2HSV) 
    s_mag = random.randint(11, 30) / 10 
     
    img_hsv[:,:,(0)] = img_hsv[:,:,(0)]
    img_hsv[:,:,(1)] = np.clip(img_hsv[:,:,(1)]*s_mag, 0, 255) 
    img_hsv[:,:,(2)] = img_hsv[:,:,(2)]
    return cv2.cvtColor(img_hsv,cv2.COLOR_HSV2RGB) 

def HSV_V(image: MatLike) -> MatLike:
    img_hsv = cv2.cvtColor(image,cv2.COLOR_RGB2HSV) 
    v_mag = random.randint(11, 30) / 10
     
    img_hsv[:,:,(0)] = img_hsv[:,:,(0)]
    img_hsv[:,:,(1)] = img_hsv[:,:,(1)]
    img_hsv[:,:,(2)] = np.clip(img_hsv[:,:,(2)]*v_mag, 0, 255)
    return cv2.cvtColor(img_hsv,cv2.COLOR_HSV2RGB) 

def HLS_S(image: MatLike) -> MatLike:
    img_hls = cv2.cvtColor(image,cv2.COLOR_RGB2HLS) 
    mag = random.randint(11, 30) / 10
     
    img_hls[:,:,(0)] = img_hls[:,:,(0)]
    img_hls[:,:,(1)] = img_hls[:,:,(1)]
    img_hls[:,:,(2)] = np.clip(img_hls[:,:,(2)]*mag, 0, 255)
    return cv2.cvtColor(img_hls,cv2.COLOR_HLS2RGB) 

def HLS_L(image: MatLike) -> MatLike:
    img_hls = cv2.cvtColor(image,cv2.COLOR_RGB2HLS) 
    mag = random.randint(11, 30) / 10
     
    img_hls[:,:,(0)] = img_hls[:,:,(0)]
    img_hls[:,:,(1)] = np.clip(img_hls[:,:,(1)]*mag, 0, 255)
    img_hls[:,:,(2)] = img_hls[:,:,(2)]
    return cv2.cvtColor(img_hls,cv2.COLOR_HLS2RGB) 

def ポスタ(image: MatLike) -> MatLike:
    n = random.randint(2, 6)                               #分割数
    x = np.arange(256)                   #0,1,2...255までの整数が並んだ配列

    ibins = np.linspace(0, 255, n+1)     #LUTより入力は255/(n+1)で分割
    obins = np.linspace(0,255, n)        #LUTより出力は255/nで分割

    num=np.digitize(x, ibins)-1          #インプットの画素値をポスタリゼーションするために番号付けを行う
    num[255] = n-1                       #digitize処理で外れてしまう画素値255の番号を修正する

    y = np.array(obins[num], dtype=np.uint8)   #ポスタリゼーションするLUTを作成する
    image =  cv2.LUT(image, y)                 #ポスタリゼーションを行う
    return image


filt_list = [そのまま, ラインアート, グレー, コントラスト, 輪郭強調, HSV_S, HSV_V, HLS_S, HLS_L, ポスタ]

def main(args: argparse.Namespace):
    path = pathlib.Path(args.file)
    if not path.is_file():
        messagebox.showerror("ファイルがありません", f"ファイルではない: {path}")
        return

    # アプリケーション起動
    root = tk.Tk()
    app = Application(root, path)
    app.mainloop()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("file")
    args = parser.parse_args()
    main(args)
