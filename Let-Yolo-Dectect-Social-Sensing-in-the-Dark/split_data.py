import os
import shutil
import random

# ================= 配置 =================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# 原始数据位置 (dataset_generator 生成的)
SRC_IMG_DIR = os.path.join(BASE_DIR, "dataset", "images")
SRC_LBL_DIR = os.path.join(BASE_DIR, "dataset", "labels")

# 目标 YOLO 格式位置
DST_DIR = os.path.join(BASE_DIR, "yolo_dataset")

# 划分比例 (80% 训练, 20% 验证)
TRAIN_RATIO = 0.8
# =======================================

def move_files(files, type_name):
    for f in files:
        # 移动图片
        src_img = os.path.join(SRC_IMG_DIR, f + ".jpg")
        dst_img = os.path.join(DST_DIR, type_name, "images", f + ".jpg")
        shutil.copy(src_img, dst_img)
        
        # 移动标签
        src_lbl = os.path.join(SRC_LBL_DIR, f + ".txt")
        dst_lbl = os.path.join(DST_DIR, type_name, "labels", f + ".txt")
        shutil.copy(src_lbl, dst_lbl)

def main():
    # 1. 创建目录结构
    for t in ['train', 'val']:
        os.makedirs(os.path.join(DST_DIR, t, "images"), exist_ok=True)
        os.makedirs(os.path.join(DST_DIR, t, "labels"), exist_ok=True)

    # 2. 获取所有文件ID (不带后缀)
    files = [f.split('.')[0] for f in os.listdir(SRC_IMG_DIR) if f.endswith('.jpg')]
    random.shuffle(files)
    
    # 3. 计算切分点
    split_idx = int(len(files) * TRAIN_RATIO)
    train_files = files[:split_idx]
    val_files = files[split_idx:]
    
    print(f"正在划分数据... 训练集: {len(train_files)}, 验证集: {len(val_files)}")
    
    # 4. 移动文件
    move_files(train_files, 'train')
    move_files(val_files, 'val')
    
    print(f"完成！数据已整理到: {DST_DIR}")
    print("结构如下：")
    print("yolo_dataset/train/images (用于模型学习)")
    print("yolo_dataset/val/images   (用于考试打分)")

if __name__ == "__main__":
    main()