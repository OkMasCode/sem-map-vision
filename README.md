# sem_map_vision

ROS2 package for RGB + pointcloud object perception, semantic mapping, goal checking, and LLM-assisted navigation command generation.

## Overview

This repository contains:
- A vision node that runs YOLO segmentation + tracking, computes 3D centroids from pointcloud masks, and publishes detections.
- A semantic mapper node that fuses detections into a persistent map with TF transforms.
- A goal checker node that monitors the semantic map and publishes a goal-reached flag/position.
- Two standalone scripts:
  - `scripts/map_preproc.py` for DBSCAN clustering of `map.json`.
  - `scripts/llm_transformers.py` for LLM-based command generation (`robot_command.json`).

---

## Repository Structure

```text
sem_map_vision/
├── config/
│   ├── map.json
│   ├── map_final.json
│   ├── clustered_map.json
│   └── robot_command.json
├── scripts/
│   ├── llm_transformers.py
│   ├── map_preproc.py
│   └── prompts/
├── sem_map_vision/
│   ├── no_pc_vision.py
│   ├── mapper_node.py
│   ├── mapper.py
│   ├── goal_checker_node.py
│   └── utils/
│       └── clip_processor.py
├── setup.py
├── package.xml
└── README.md
```

---

## ROS2 Nodes

The package currently installs these console scripts (from `setup.py`):
- `no_pc_vision_node`
- `mapper_node`
- `goal_checker_node`

### 1) Vision Node (`no_pc_vision.py`)

**Purpose**
- Subscribes to synchronized RGB + PointCloud2 streams.
- Runs YOLO segmentation/tracking.
- Computes per-instance 3D centroid and 3D box from masked pointcloud.
- Computes CLIP image embeddings (batched) and goal similarity.
- Publishes detections and optional visualization.

**Main subscriptions**
- `image_topic` (default `/camera/camera/color/image_raw`)
- `pointcloud_topic` (default `/camera/camera/depth/color/points`)
- `camera_info_topic` (default `/camera/camera/color/camera_info`)

**Main publications**
- `/vision/detections` (`yolo11_seg_interfaces/DetectedObject`)
- `/vision/centroid_markers` (`visualization_msgs/MarkerArray`, only if visualization enabled)
- `/vision/annotated_image` (`sensor_msgs/Image`, only if visualization enabled)

**Notable behavior**
- Invalid point filtering excludes `NaN`, `Inf`, and all-zero XYZ points.
- CLIP prompt is periodically reloaded from `config/robot_command.json`.

---

### 2) Semantic Mapper Node (`mapper_node.py` + `mapper.py`)

**Purpose**
- Converts detections from camera frame into a fixed map frame using TF2.
- Merges repeated observations.
- Publishes semantic map and periodically exports JSON.

**Subscribed topics**
- `/vision/detections` (`DetectedObject`)

**Published topics**
- `/vision/semantic_map` (`SemanticObjectArray`)

**Exported files**
- `config/map.json` (periodic)
- `config/map_final.json` (on shutdown)

**Important update: multi-frame confirmation gate**
- New detections are first stored in a tentative buffer.
- Promotion to persistent map occurs only after repeated observations (default: 3 hits within 1.0s).
- Stale tentative entries are automatically dropped.
- This reduces one-frame false positives being saved to the map.

---

### 3) Goal Checker Node (`goal_checker_node.py`)

**Purpose**
- Reads goal class from `config/robot_command.json`.
- Monitors semantic map objects.
- Publishes goal reached flag and goal position when similarity threshold is met.

**Subscribed topics**
- `/vision/semantic_map`

**Published topics**
- `/vision/goal_reached` (`std_msgs/Bool`)
- `/vision/goal_position` (`geometry_msgs/PointStamped`)

**Key parameter**
- `similarity_threshold` (default `5.0`)

---

## Standalone Scripts

These scripts are not ROS nodes.

### `scripts/map_preproc.py`

**Purpose**
- Loads `config/map.json`.
- Runs DBSCAN clustering.
- Reassigns outliers into unique clusters.
- Writes `config/clustered_map.json`.

**Output fields per object**
- `id`
- `cluster`
- `class`
- `coords`
- `cluster_centroid`
- `cluster_dimensions`:
  - `bounding_box.min/max`
  - `bounding_box.dimensions` (`width`, `length`)
  - `radius`

**Current default clustering in script**
- `eps=3.5`
- `min_samples=2`

Run:
```bash
cd ~/ros2_ws/src/sem_map_vision
python scripts/map_preproc.py
```

---

### `scripts/llm_transformers.py`

**Purpose**
- Processes natural-language navigation instructions.
- Extracts goal class and CLIP prompts.
- Ranks mapped objects by CLIP similarity.
- Predicts most likely cluster.
- Classifies action (`go_to_object` or `bring_back_object`).
- Saves final command to `config/robot_command.json`.

**Current model stack**
- Hugging Face causal LM pipeline (`meta-llama/Llama-3.1-8B-Instruct` by default).
- Local SigLIP encoder via `CLIPProcessor`.

**Current output payload includes**
- `goal`
- `clip_prompts`
- `text_embedding`
- `goal_objects`
- `object_similarities`
- `cluster_info` (including `coords` and `dimensions`)
- `action`
- `valid`

Run:
```bash
cd ~/ros2_ws/src/sem_map_vision
python scripts/llm_transformers.py
```

---

## Build and Run

### 1) Build

```bash
cd ~/ros2_ws
colcon build --packages-select sem_map_vision yolo11_seg_interfaces
source install/setup.bash
```

### 2) Run nodes (separate terminals)

**Vision node**
```bash
source ~/ros2_ws/install/setup.bash
ros2 run sem_map_vision no_pc_vision_node
```

**Mapper node**
```bash
source ~/ros2_ws/install/setup.bash
ros2 run sem_map_vision mapper_node
```

**Goal checker node**
```bash
source ~/ros2_ws/install/setup.bash
ros2 run sem_map_vision goal_checker_node
```

---

## Configuration Notes

- Several scripts/nodes use absolute defaults like `/home/workspace/ros2_ws/...`.
- If your workspace path differs, override ROS params or update constants in scripts.
- `llm_transformers.py` expects prompt templates under `scripts/prompts/`.

---

## Dependencies (high level)

- ROS2 (Humble+ recommended)
- `yolo11_seg_interfaces`
- Python libs used by this package/scripts include:
  - `torch`, `ultralytics`, `opencv-python`, `numpy`
  - `transformers`, `pydantic`
  - `scikit-learn`

Install missing Python packages in your environment as needed.

---

## License

Apache-2.0
