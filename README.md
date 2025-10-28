# MineCan: A Canada-Wide Benchmark Dataset for Mining Detection from Satellite Imagery

**MineCan** is the first Canada-wide benchmark dataset for **mining detection and segmentation** using high-resolution Google Earth imagery. It provides both **object detection bounding boxes** and **pixel-level segmentation masks**, enabling reproducible deep learning benchmarks across diverse geographies.

---

## Dataset Overview
- **Total images:** 1,519 (RGB, 750 × 750 pixels)  
- **Annotations:** Provided in three formats:  
  - **LabelMe JSONs** (polygon annotations)  
  - **YOLO text files** (object detection bounding boxes)  
  - **Segmentation masks** (pixel-level ground truth, PNG format)  
- **Geographic coverage:** Across all Canadian provinces and territories (coastal, inland, and northern regions).  
- **Acquisition dates:** 14 Jan. 2025 – 7 Feb. 2025 (recorded for reproducibility in Google Earth).  
- **Annotation tool:** [LabelMe](https://github.com/wkentaro/labelme) was used for manual polygon annotation, guided by polygons from the [FINEPRINT visualizer](https://www.fineprint.global/visualisations/viewer/).  

---

## Dataset Structure
```
MineCan
├── images                 # RGB images
│   ├── train (1063)
│   └── val (456)
│
├── labelme_jsons          # Polygon annotations (LabelMe format)
│   ├── train (1063)
│   └── val (456)
│
├── labels_yolo            # Object detection labels (YOLO format)
│   ├── train (1063)
│   └── val (456)
│
├── segmentation_masks     # Pixel-level ground truth masks
│   ├── train (1063)
│   └── val (456)
```

---

## Image Source and Usage License
The MineCan dataset was created using **Google Earth imagery**.  

- Use of Google Earth imagery must comply with the [Google Earth terms of use](https://www.google.com/permissions/geoguidelines/).  
- All images and annotations in MineCan are provided strictly for **academic research purposes only**.  
- **Commercial use is prohibited.**

---

## Dataset Access
> **Note:** This dataset is associated with a paper currently under review at *Scientific Data*.  
> - Access is currently **restricted** via Google Drive (Only reviewers can access)
> - After publication, the dataset will be released as **open access**.

---

## Benchmarks
We evaluated **five segmentation models** and **three detection models** as baselines:

- **Segmentation:** U-Net, UNet++, DeepLabV3+, Segformer, PSPNet  
  - Best result: **UNet++**, F1-Score = 0.9273  
- **Object Detection:** YOLOv5, YOLOv11, YOLOv12  
  - Best result: **YOLOv11**, AP@50 = 0.877  

---

## Acknowledgment
- We thank the **FINEPRINT project** for providing global mining polygons.  
- Google Earth for access to high-resolution imagery.  
