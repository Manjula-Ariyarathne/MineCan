import os
from PIL import Image, ImageEnhance
import shutil


# Paths for original and augmented data
train_images_path = "0original/images"
train_labels_path = "0original/labels"


train_augmented_images_path = "1all_augmented/images"
train_augmented_labels_path = "1all_augmented/labels"


# Create augmented directories if they don't exist
for path in [train_augmented_images_path, train_augmented_labels_path]:
    os.makedirs(path, exist_ok=True)


def augment_image(image, operation):
    """Apply augmentation to the image."""
    if operation == 'rotate_90':
        return image.rotate(90, expand=True)
    elif operation == 'rotate_180':
        return image.rotate(180, expand=True)
    elif operation == 'rotate_270':
        return image.rotate(270, expand=True)
    elif operation == 'flip_horizontal':
        return image.transpose(Image.FLIP_LEFT_RIGHT)
    elif operation == 'flip_vertical':
        return image.transpose(Image.FLIP_TOP_BOTTOM)
    elif operation == 'brightness_increase':
        enhancer = ImageEnhance.Brightness(image)
        return enhancer.enhance(1.2)
    elif operation == 'brightness_decrease':
        enhancer = ImageEnhance.Brightness(image)
        return enhancer.enhance(0.5)

def get_yolo_format_labels(original_labels, img_width, img_height, augment_op):
    """Convert COCO format labels to YOLO format based on the augmented image size."""
    yolo_labels = []

    for line in original_labels:
        class_id, x_center, y_center, width, height = map(float, line.strip().split())
        
        
        # Adjust coordinates based on the augmentation operation
        if augment_op == 'rotate_90':
            # After 90-degree rotation: new center x = old y, new center y = 1 - old x
            new_x_center = y_center
            new_y_center = 1 - x_center
            x_center, y_center = new_x_center, new_y_center
            width, height = height, width
        elif augment_op == 'rotate_180':
            # After 180-degree rotation: new center x = 1 - old x, new center y = 1 - old y
            x_center = 1 - x_center
            y_center = 1 - y_center
        elif augment_op == 'rotate_270':
            # After 270-degree rotation: new center x = 1 - old y, new center y = old x
            new_x_center = 1 - y_center
            new_y_center = x_center
            x_center, y_center = new_x_center, new_y_center
            width, height = height, width
        elif augment_op == 'flip_horizontal':
            # Horizontal flip: new center x = 1 - old x
            x_center = 1 - x_center
        elif augment_op == 'flip_vertical':
            # Vertical flip: new center y = 1 - old y
            y_center = 1 - y_center
        elif augment_op in ['brightness_increase', 'brightness_decrease']:
            # Brightness changes do not affect bounding box coordinates
            pass
        
        # Append YOLO formatted label with appropriate formatting
        yolo_labels.append(f"{int(class_id)} {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}")

    return yolo_labels



def save_augmented_data(img_file, image_path, labels, augment_op, save_image_path, save_label_path):
    """Save augmented images and their corresponding labels."""
    # img_path = os.path.join(save_image_path, image_file)
    img = Image.open(image_path)
    
    img_width, img_height = img.size
    augmented_img = augment_image(img, augment_op)
    
    # Save the augmented image
    augmented_img_name = f"{os.path.splitext(img_file)[0]}_{augment_op}.png"
    augmented_img.save(os.path.join(save_image_path, augmented_img_name))
    
    # Convert labels to YOLO format
    yolo_labels = get_yolo_format_labels(labels, img_width, img_height, augment_op)
    
    # Write YOLO formatted labels
    yolo_label_path = os.path.join(save_label_path, f"{os.path.splitext(img_file)[0]}_{augment_op}.txt")
    with open(yolo_label_path, 'w') as f:
        f.write("\n".join(yolo_labels))

def process_directory(images_path, labels_path, augmented_images_path, augmented_labels_path):
    """Process all images in a directory."""
    image_files = [f for f in os.listdir(images_path) if f.endswith('.png')]
    
    for img_file in image_files:
        label_file = img_file.replace('.png', '.txt')
        image_path = os.path.join(images_path, img_file)
        label_path = os.path.join(labels_path, label_file)
        
        if os.path.exists(label_path):
            with open(label_path, 'r') as f:
                original_labels = f.readlines()
            
            # Perform augmentations
            for op in ['rotate_90', 'rotate_180', 'rotate_270', 
                        'flip_horizontal', 'flip_vertical', 
                        'brightness_increase', 'brightness_decrease']:
                save_augmented_data(img_file, image_path, original_labels, op, augmented_images_path, augmented_labels_path)



def move_original_files(src_images, src_labels, dest_images, dest_labels):
    """Move original images and labels into augmented folders."""
    image_files = [f for f in os.listdir(src_images) if f.endswith('.png')]
    label_files = [f for f in os.listdir(src_labels) if f.endswith('.txt')]

    for img_file in image_files:
        src_path = os.path.join(src_images, img_file)
        dest_path = os.path.join(dest_images, img_file)
        shutil.copy2(src_path, dest_path)  # use move() instead of copy2() to move instead of copy

    for label_file in label_files:
        src_path = os.path.join(src_labels, label_file)
        dest_path = os.path.join(dest_labels, label_file)
        shutil.copy2(src_path, dest_path)

    print("Original images and labels moved to augmented folders successfully.")




# Process
process_directory(train_images_path, train_labels_path, train_augmented_images_path, train_augmented_labels_path)

# After augmentation is done
move_original_files(train_images_path, train_labels_path,
                    train_augmented_images_path, train_augmented_labels_path)

print("Augmentation complete!")
