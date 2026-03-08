import gymnasium as gym
from gymnasium import spaces
import numpy as np
import cv2
from ultralytics import YOLO
from skimage.metrics import structural_similarity as ssim
import random

class EmojiAttackEnv(gym.Env):
    """
    自定义 RL 环境：攻击 Emoji 识别模型
    目标：在保持图片可视性的前提下，让 YOLO 识别不出 Emoji
    """
    def __init__(self, model_path, image_path, target_class_id):
        super(EmojiAttackEnv, self).__init__()
        
        # 1. 加载被攻击的防御模型 (Frozen)
        self.model = YOLO(model_path)
        
        # 2. 加载原始图片 (作为 Ground Truth)
        self.original_img = cv2.imread(image_path)
        if self.original_img is None:
            raise ValueError(f"无法读取图片: {image_path}")
        self.original_img = cv2.resize(self.original_img, (640, 640))
        self.current_img = self.original_img.copy()
        
        self.target_id = target_class_id
        
        # 3. 定义动作空间 (离散动作)
        # 0: 无操作, 1: 高斯模糊, 2: 椒盐噪声, 3: 降低亮度, 4: 像素化
        self.action_space = spaces.Discrete(6)
        
        # 4. 定义观察空间 (RGB 图片)
        self.observation_space = spaces.Box(low=0, high=255, shape=(640, 640, 3), dtype=np.uint8)
        
        # 记录初始置信度
        self.initial_conf = self._get_confidence(self.original_img)
        print(f"--- 环境初始化 ---")
        print(f"目标类别: {target_class_id}")
        print(f"初始置信度: {self.initial_conf:.4f}")

    def _get_confidence(self, img):
        """让 YOLO 看图，返回目标类别的置信度"""
        # verbose=False 避免刷屏
        results = self.model.predict(img, verbose=False, imgsz=640)
        
        # 提取最高置信度
        max_conf = 0.0
        for box in results[0].boxes:
            cls_id = int(box.cls[0])
            conf = float(box.conf[0])
            # 只有当检测到我们关注的那个 Emoji 时才算数
            if cls_id == self.target_id:
                if conf > max_conf:
                    max_conf = conf
        return max_conf

    def step(self, action):
        """执行一步动作"""
        # 1. 执行图像处理操作
        if action == 0:   # Pass (无操作)
            pass
        elif action == 1: # Gaussian Blur (模糊)
            self.current_img = cv2.GaussianBlur(self.current_img, (5, 5), 0)
        elif action == 2: # Salt & Pepper (噪点)
            noise = np.random.normal(0, 25, self.current_img.shape).astype(np.uint8)
            # 简单的加法噪声，截断到 0-255
            self.current_img = cv2.add(self.current_img, noise)
        elif action == 3: # Darken (变暗)
            table = np.array([i * 0.8 for i in range(256)]).astype("uint8")
            self.current_img = cv2.LUT(self.current_img, table)
        elif action == 4: # Pixelate (马赛克)
            h, w = self.current_img.shape[:2]
            temp = cv2.resize(self.current_img, (w//4, h//4), interpolation=cv2.INTER_LINEAR)
            self.current_img = cv2.resize(temp, (w, h), interpolation=cv2.INTER_NEAREST)
        elif action == 5: # Random Patch (随机遮挡)
            h, w = self.current_img.shape[:2]
            # 随机生成一个 50x50 的黑块
            patch_size = 50 
            x = np.random.randint(0, w - patch_size)
            y = np.random.randint(0, h - patch_size)
            # 画一个黑块 (或者噪点块)
            cv2.rectangle(self.current_img, (x, y), (x+patch_size, y+patch_size), (0, 0, 0), -1)
        # 2. 计算当前状态的指标
        current_conf = self._get_confidence(self.current_img)
        
        # 计算结构相似度 (SSIM): 范围 0-1，越接近 1 代表画质越好
        # win_size=3 是为了适应小窗口计算，channel_axis=2 指定颜色通道
        score_ssim = ssim(self.original_img, self.current_img, win_size=3, channel_axis=2)

        # 3. 设计奖励函数 (Reward Function) - 核心部分
        # 目标：Conf 越低越好，SSIM 越高越好
        
        conf_drop = self.initial_conf - current_conf # 置信度下降量
        
        # 基础奖励：置信度下降带来的快感
        reward = conf_drop * 10 
        
        # 惩罚：如果画质太差 (SSIM < 0.5)，重罚
        if score_ssim < 0.6:
            reward -= 15
            
        # 结束条件：置信度归零（攻击成功）或 画质太差（失败）
        terminated = False
        if current_conf < 0.2: # 成功骗过模型
            reward += 50 # 大额奖励
            terminated = True
        elif score_ssim < 0.5: # 图片废了
            reward -= 50
            terminated = True
            
        truncated = False # 用于时间限制，这里暂时不用
        
        info = {
            "confidence": current_conf,
            "ssim": score_ssim
        }
        
        return self.current_img, reward, terminated, truncated, info

    def reset(self, seed=None):
        super().reset(seed=seed)
        # 重置回原始干净图片
        self.current_img = self.original_img.copy()
        return self.current_img, {}