# DrivAerML sedan geometry

Source: N. Ashton and the DrivAerML contributors, *DrivAerML*,
[arXiv:2408.11969](https://arxiv.org/abs/2408.11969).

Dataset: [neashton/drivaerml](https://huggingface.co/datasets/neashton/drivaerml).
The sedan source is `run_1/drivaer_1.stl`, verified at dataset revision
`5d448b209bf654503c64ce7261c34fa125f46392` with SHA-256
`411e6651284a26fc94924106b833fd79febc6deba63922c929dd8acfc99720d2`.

The dataset and derived sedan geometry are provided under
[CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).
The source license text is included in `drivaerml-CC-BY-SA-4.0.txt`.

Zephyr changes include bounded geometry deformation, display mesh reduction and
display coordinate conversion. The candidate export retains upstream solver
coordinates in metres. Each run's evidence identifies the actual deformation,
input/output hashes and inference checkpoint.

Displayed pressure, sensitivity and airflow fields are Zephyr's recorded NVIDIA
DoMINO predictions, not the original dataset's CFD fields. They do not establish
physical validation or imply endorsement by the dataset contributors or NVIDIA.
The software license is separate from these dataset and geometry notices.
