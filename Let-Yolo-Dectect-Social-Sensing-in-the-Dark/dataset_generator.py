import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import os
import random

# ================= 配置区域 =================

# 1. 动态获取脚本所在的绝对路径 (修复 FileNotFoundError 的核心)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 2. 基于绝对路径构建资源路径
EMOJI_DIR = os.path.join(BASE_DIR, "assets", "emojis")
# 注意：你需要放一个支持英文的字体，比如 arial.ttf，或者继续用原来的字体也可以
FONT_PATH = os.path.join(BASE_DIR, "assets", "fonts", "arial.ttf") 
OUTPUT_IMG_DIR = os.path.join(BASE_DIR, "dataset", "images")
OUTPUT_LBL_DIR = os.path.join(BASE_DIR, "dataset", "labels")

# 输出数量
NUM_IMAGES = 200  
# 图像尺寸
IMG_SIZE = (640, 640) 

# 3. 英文反讽/双关语料库 (English Sarcastic Corpus)
# 这些词看起来正面或中性，但在网络语境常用于阴阳怪气
SARCASTIC_TEXTS = [
    "Great job.", "So smart.", "Wow.", "Interesting.", 
    "Sure...", "You tried.", "Big brain energy", 
    "Totally normal", "No way", "Cool story", 
    "Genius.", "My bad", "Obsessed", "As if",
    "Have fun", "Good luck", "Whatever", "Okay boomer"
]

# ===========================================

def create_folders():
    if not os.path.exists(OUTPUT_IMG_DIR): os.makedirs(OUTPUT_IMG_DIR)
    if not os.path.exists(OUTPUT_LBL_DIR): os.makedirs(OUTPUT_LBL_DIR)

def load_emojis(directory):
    emojis = []
    # 检查目录是否存在
    if not os.path.exists(directory):
        print(f"Error: 找不到目录 {directory}")
        return []

    # 过滤掉非图片文件 (如 .DS_Store)
    files = [f for f in os.listdir(directory) if f.lower().endswith('.png')]
    
    for f in files:
        # 尝试从文件名获取 ID (例如 0.png -> id 0), 如果不是数字则默认 0
        file_name_clean = os.path.splitext(f)[0]
        class_id = int(file_name_clean) if file_name_clean.isdigit() else 0
        
        img_path = os.path.join(directory, f)
        try:
            # 使用 PIL 读取以保留 Alpha 通道
            img = Image.open(img_path).convert("RGBA")
            emojis.append({'img': img, 'id': class_id, 'name': f})
        except Exception as e:
            print(f"跳过损坏的文件 {f}: {e}")
            
    return emojis

def generate_background(size):
    bg_type = random.choice(['solid', 'noise'])
    if bg_type == 'solid':
        color = tuple(np.random.randint(0, 256, 3).tolist())
        img = Image.new('RGBA', size, color)
    else:
        noise = np.random.randint(0, 256, (size[1], size[0], 3), dtype=np.uint8)
        img = Image.fromarray(noise).convert("RGBA")
    return img

def yolo_format(img_w, img_h, box):
    x1, y1, x2, y2 = box
    dw = 1. / img_w
    dh = 1. / img_h
    x = (x1 + x2) / 2.0
    y = (y1 + y2) / 2.0
    w = x2 - x1
    h = y2 - y1
    return (x * dw, y * dh, w * dw, h * dh)

def main():
    print(f"当前工作目录: {BASE_DIR}")
    create_folders()
    emojis = load_emojis(EMOJI_DIR)
    
    if not emojis:
        print(f"严重错误: 在 {EMOJI_DIR} 下没找到任何 .png 图片！")
        print("请确保你已经把 emoji 图片放进去了。")
        return

    print(f"找到 {len(emojis)} 个 Emoji 素材，开始生成 {NUM_IMAGES} 张图片...")

    for i in range(NUM_IMAGES):
        # 1. 创建背景
        bg_img = generate_background(IMG_SIZE)
        draw = ImageDraw.Draw(bg_img)
        
        # 2. 随机写入英文文字
        text = random.choice(SARCASTIC_TEXTS)
        
        # 字体处理逻辑
        try:
            font_size = random.randint(40, 80) # 英文可以稍微大一点
            font = ImageFont.truetype(FONT_PATH, font_size)
        except OSError:
            # 如果找不到字体文件，尝试使用默认字体 (仅用于调试，默认字体很小)
            if i == 0: print(f"警告: 找不到字体文件 {FONT_PATH}，将使用默认字体。建议下载一个 arial.ttf 放入 fonts 文件夹。")
            font = ImageFont.load_default()
        
        # 随机位置写字
        text_x = random.randint(10, IMG_SIZE[0] - 200)
        text_y = random.randint(10, IMG_SIZE[1] - 100)
        # 随机颜色
        text_color = tuple(np.random.randint(0, 256, 3).tolist())
        
        # 绘制文字
        draw.text((text_x, text_y), text, font=font, fill=text_color)

        # 3. 随机贴入 Emoji
        selected = random.choice(emojis)
        emoji_img = selected['img']
        
        scale = random.uniform(0.5, 1.5)
        new_size = (int(emoji_img.width * scale), int(emoji_img.height * scale))
        emoji_resized = emoji_img.resize(new_size)
        
        max_x = IMG_SIZE[0] - new_size[0]
        max_y = IMG_SIZE[1] - new_size[1]
        paste_x = random.randint(0, max(0, max_x))
        paste_y = random.randint(0, max(0, max_y))
        
        bg_img.paste(emoji_resized, (paste_x, paste_y), emoji_resized)
        
        # 4. 保存
        file_name = f"train_{i}"
        save_path_img = os.path.join(OUTPUT_IMG_DIR, file_name + ".jpg")
        bg_img.convert("RGB").save(save_path_img)
        
        # 5. 生成 YOLO 标签
        bbox = (paste_x, paste_y, paste_x + new_size[0], paste_y + new_size[1])
        yolo_box = yolo_format(IMG_SIZE[0], IMG_SIZE[1], bbox)
        
        save_path_lbl = os.path.join(OUTPUT_LBL_DIR, file_name + ".txt")
        with open(save_path_lbl, "w") as f:
            f.write(f"{selected['id']} {yolo_box[0]:.6f} {yolo_box[1]:.6f} {yolo_box[2]:.6f} {yolo_box[3]:.6f}")

    print("SUCCESS: 数据生成完毕！")
    print(f"图片路径: {OUTPUT_IMG_DIR}")

if __name__ == "__main__":
    main()