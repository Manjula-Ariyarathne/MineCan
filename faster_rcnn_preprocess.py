import json
import os
from PIL import Image


dataset_path = "dataset_7_3/"
output_dataset_path = "COCODevKit"

# Define paths
yolo_train_labels_path = f'{dataset_path}/labels/train/'
yolo_val_labels_path = f'{dataset_path}/labels/val/'
yolo_test_labels_path = f'{dataset_path}/labels/test/'
train_images_path = f'{output_dataset_path}/train2017/'
val_images_path = f'{output_dataset_path}/val2017/'
test_images_path = f'{output_dataset_path}/test2017/'
output_json_train = f'{output_dataset_path}/annotations/instances_train2017.json'
output_json_val = f'{output_dataset_path}/annotations/instances_val2017.json'
output_json_test = f'{output_dataset_path}/annotations/image_info_test2017.json'

# Class names for VHR10 dataset
# names = [
#     'airplane', 'ship', 'storage_tank', 'baseball_diamond',
#     'tennis_court', 'basketball_court', 'ground_track_field',
#     'harbor', 'bridge', 'vehicle'
# ]

# Class names
names = [
    "mine"
]

# COCO format template
def create_coco_format():
    return {
        "images": [],
        "annotations": [],
        "categories": [{"id": i + 1, "name": name} for i, name in enumerate(names)]  # Create 10 categories
    }

# Add image and annotations to COCO JSON
def add_image_annotation(file_path, label_path, image_id, annotation_id, coco_data):
    # Load image to get dimensions
    with Image.open(file_path) as img:
        width, height = img.size
    
    # Add image information
    coco_data["images"].append({
        "id": image_id,
        "file_name": os.path.basename(file_path),
        "width": width,
        "height": height
    })
    
    # Add annotations
    with open(label_path, 'r') as f:
        for line in f:
            if line.strip():  # Skip empty lines
                label_data = line.strip().split()
                category_id = int(label_data[0]) + 1  # Class ID in COCO format starts from 1
                x_center, y_center, w, h = map(float, label_data[1:])
                
                # Convert YOLO format (normalized) to COCO format (absolute bounding box)
                x = (x_center - w / 2) * width
                y = (y_center - h / 2) * height
                bbox_width = w * width
                bbox_height = h * height
                
                coco_data["annotations"].append({
                    "id": annotation_id,
                    "image_id": image_id,
                    "category_id": category_id,
                    "bbox": [x, y, bbox_width, bbox_height],
                    "area": bbox_width * bbox_height,
                    "iscrowd": 0
                })
                annotation_id += 1
    return annotation_id

# Convert YOLO to COCO for both train and validation sets
def convert_yolo_to_coco(images_path, labels_path, output_json_path):
    coco_data = create_coco_format()
    image_id = 1
    annotation_id = 1
    
    for label_file in os.listdir(labels_path):
        if label_file.endswith(".txt"):
            image_file = label_file.replace(".txt", ".png")
            image_path = os.path.join(images_path, image_file)
            label_path = os.path.join(labels_path, label_file)
            
            # Ensure image and label match
            if os.path.exists(image_path):
                annotation_id = add_image_annotation(image_path, label_path, image_id, annotation_id, coco_data)
                image_id += 1
    
    # Write to JSON
    with open(output_json_path, 'w') as json_file:
        json.dump(coco_data, json_file, indent=4)

# Execute conversion for train and validation sets
convert_yolo_to_coco(train_images_path, yolo_train_labels_path, output_json_train)
convert_yolo_to_coco(val_images_path, yolo_val_labels_path, output_json_val)
convert_yolo_to_coco(test_images_path, yolo_test_labels_path, output_json_test)
