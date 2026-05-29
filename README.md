# MineCan: A Canada-Wide Benchmark Dataset for Mining Detection from Satellite Imagery

**MineCan** is the first Canada-wide benchmark dataset for **mining detection and segmentation** using high-resolution Google Earth imagery. It provides both **object detection bounding boxes** and **pixel-level segmentation masks**, enabling reproducible deep learning benchmarks across diverse geographies.

---

## Dataset Overview

- **Total images:** 1,519 RGB images, each 750 x 750 pixels.
- **Annotations:** Provided in three formats:
  - **LabelMe JSONs** for polygon annotations.
  - **YOLO text files** for object detection bounding boxes.
  - **Segmentation masks** for pixel-level ground truth in PNG format.
- **Geographic coverage:** Across all Canadian provinces and territories, including coastal, inland, and northern regions.
- **Acquisition dates:** 14 Jan. 2025 to 7 Feb. 2025, recorded for reproducibility in Google Earth.
- **Annotation tool:** [LabelMe](https://github.com/wkentaro/labelme) was used for manual polygon annotation, guided by polygons from the [FINEPRINT visualizer](https://www.fineprint.global/visualisations/viewer/).

---

## Dataset Structure

```text
MineCan
|-- images                 # RGB images
|   |-- train (1063)
|   `-- val (456)
|
|-- labelme_jsons          # Polygon annotations in LabelMe format
|   |-- train (1063)
|   `-- val (456)
|
|-- labels_yolo            # Object detection labels in YOLO format
|   |-- train (1063)
|   `-- val (456)
|
`-- segmentation_masks     # Pixel-level ground truth masks
    |-- train (1063)
    `-- val (456)
```

---

## Single Patch Capture

This repository also includes a small script for capturing a single Google Maps satellite patch centered on a coordinate. The default output size is **750 x 750 pixels**, matching the MineCan image size.

Run:

```bash
python download_single_patch.py --lat {latitude} --lon {longitude} --zoom {zoom}
```

Example:

```bash
python download_single_patch.py --lat 47.535714 --lon -52.752814 --zoom 18
```

The script saves the cropped patch as:

```text
output/Lat_{latitude}_Lon_{longitude}.png
```

---

## Dataset Access

> **Note:** This dataset is associated with a paper currently under review at *Scientific Data*.
>
> - Access is currently **restricted** via Google Drive. Only reviewers can access it.
> - After publication, the dataset will be released as **open access**.

---

## Benchmarks

We evaluated **five segmentation models** and **three detection models** as baselines:

- **Segmentation:** U-Net, UNet++, DeepLabV3+, SegFormer, PSPNet.
  - Best result: **UNet++**, F1-score = 0.9273.
- **Object Detection:** YOLOv5, YOLOv11, YOLOv12.
  - Best result: **YOLOv11**, AP@50 = 0.877.

---

## Acknowledgment

- We thank the **FINEPRINT project** for providing global mining polygons.
- We thank Google Earth for access to high-resolution imagery.
