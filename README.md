
---

# Social Sensing in the Dark (Project Chameleon) 

This repository implements an **Adversarial Reinforcement Learning (ARL) Framework** to address the **Transmission Degradation Problem** in social sensing. We use a PPO-based agent to simulate visual noise (blur, compression, noise) and retrain a YOLOv8 detector to achieve zero-shot robustness against viral media degradation .

> **Note on Storage Optimization**: To keep the repository lightweight, large synthetic image datasets and high-resolution visualization results have been removed. The directory structure is preserved, and these folders will be automatically populated upon running the scripts.

---

##  Project Structure

```text
Project_Chameleon/
│
[cite_start]├── assets/                 # [Source] Raw resources: High-res Emojis, Fonts [cite: 577]
[cite_start]├── dataset/                # [Auto-Created] Raw synthetic images (Empty on upload) [cite: 579]
[cite_start]├── yolo_dataset/           # [Auto-Created] Standardized YOLO format data [cite: 586]
│   ├── train/              # Training set (Clean)
│   ├── val/                # Validation set
[cite_start]│   └── adversarial/        # [Generated] Hard examples mined by RL agent [cite: 765, 772]
│
├── runs/                   # [Auto-Created] Training logs for Baseline V1 Model
│   └── detect/emoji_defense_model/weights/best.pt  # [CRITICAL] Saved V1 Model
│
├── runs_v2/                # [Auto-Created] Training logs for Robust V2 Model
│   └── detect/emoji_defense_model_v2/weights/best.pt # [CRITICAL] Saved V2 Model
│
├── results/                # [Output] Basic visualization of attack samples
├── results_comparison/     # [Output] Final academic reports (CSV) & Comparison Plots
│
[cite_start]├── yolov8n.pt              # [REQUIRED] Pre-trained YOLOv8 weights (Auto-downloaded) [cite: 598]
[cite_start]├── emoji_attacker_ppo_v2.zip # [CRITICAL] Fully trained PPO Agent model file [cite: 888]
[cite_start]├── data.yaml               # [Config] YOLO dataset configuration [cite: 586]
│
[cite_start]├── download_emojis.py      # [Step 0] Scraper script for emoji assets [cite: 577]
[cite_start]├── dataset_generator.py    # [Step 1] Synthesizes "meme-style" social media images [cite: 579]
[cite_start]├── split_data.py           # [Step 2] Splits raw data into YOLO format [cite: 585]
[cite_start]├── train_defense.py        # [Step 3] Trains the Naive Baseline Model (V1) [cite: 570]
[cite_start]├── train_attacker.py       # [Step 4] Trains the RL Agent (PPO) to attack V1 [cite: 571]
[cite_start]├── generate_adv_data.py    # [Step 5] Generates "Hard Examples" (Vaccine) [cite: 771-772]
[cite_start]├── retrain_defense.py      # [Step 6] Adversarial Fine-tuning for V2 Model [cite: 775-776]
│
[cite_start]├── attack_env.py           # [Core] Custom Gymnasium Environment for RL [cite: 735]
[cite_start]├── evaluate_attack.py      # [Eval] A/B Testing script (V1 vs V2 robustness) [cite: 900]
[cite_start]├── generate_extra_plots.py # [Vis] Generates high-quality academic plots [cite: 928, 996]
└── test_attack.py          # [Debug] Sandbox script for single image testing

```

---

##  Execution Workflow

Please execute the scripts in the following numerical order to replicate the adversarial loop:

### Phase 1: Data Engine Construction

1. 
`python dataset_generator.py`: Generates synthetic images by blending emojis, backgrounds, and text.


2. 
`python split_data.py`: Partitions raw data and creates labels in `yolo_dataset/`.



### Phase 2: Victim Training (The Baseline)

3. 
`python train_defense.py`: Fine-tunes YOLOv8n on clean data to create the **V1 Baseline Model**.



### Phase 3: Attack Simulation (The Virus)

4. 
`python train_attacker.py`: Trains the PPO agent to find visual vulnerabilities in V1.



### Phase 4: Defense Hardening (The Vaccine)

5. 
`python generate_adv_data.py`: Uses the trained agent to mine "Hard Examples".


6. 
`python retrain_defense.py`: Retrains the model on a mix of clean and adversarial data to create the **V2 Robust Model**.



### Phase 5: Final Evaluation

7. 
`python evaluate_attack.py`: Runs a comparative stress test on V1 and V2 models.


8. 
`python generate_extra_plots.py`: Visualizes metrics like Attack Success Rate (ASR) and SSIM Distribution.



---

## 🔬 Mathematical Foundation

The RL agent optimizes a trade-off reward $R_t$ to ensure attacks are effective yet semantically valid :

$$R_{t} = \alpha \cdot (Conf_{initial} - Conf_{t}) - \beta \cdot \max(0, \tau - SSIM_{t})$$

* 
**$\alpha = 10$**: Rewards the agent for lowering the victim's detection confidence.


* 
**$\beta = 20$**: Penalizes the agent if the Structural Similarity Index ($SSIM$) falls below threshold $\tau = 0.8$.



---

##  Performance Breakdown

The adversarial hardening process results in a model that is virtually immune to viral transmission noise.

| Metric | Baseline YOLOv8 (V1) | **Robust YOLOv8 (V2)** | Improvement |
| --- | --- | --- | --- |
| **Attack Success Rate (ASR)** | 80.00% | **0.00%** | -80.00% 

 |
| **Median Confidence** | $\approx 0.0$ | **$\approx 0.99$** | +0.99 

 |
| **mAP50 (Clean Data)** | 0.995 | **0.995** | No Degradation 

 |

---

##  License

Distributed under the **MIT License**.

---

Developed by **Phil-1030** | Based on research: *Social Sensing in the Dark*

---
