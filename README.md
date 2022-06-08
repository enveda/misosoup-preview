# MisoSoup Preview

![misosoup logo](MisoSoup.png)

MisoSoup is a data processing pipeline for mass-spec metabolomics.  The name is a portmanteau of the terms "mass-spectrometry", "isotope", and "soup" (of biomolecules).

**WHY**  
The creation of MisoSoup was motivated by the lack of scalable open-source solutions where the processing of mass-spectrometry data is decoupled from data analysis.  We sought to create reproducible, tunable, automatable processes for denoising and identifying features from the raw data, and depositing pre-processed mass-spectrometry data to relational databases.

Once the significant hurdles of organizing large volumes of raw data are cleared, the researcher is equipped to ask higher-level questions.  What species are responsible for the observed phenotype?  Are they novel, or has someone seen them before?  These questions are often accompanied by smaller tasks common in metabolomics workflows:
- find the abundance of a species with m/z of 369.1234 ± 0.01 across all runs;
- find retention time offsets across all runs (perform alignment);
- collect the MS2 spectra of the above species and compute similarity metrics.

MisoSoup helps you organize mass-spec data, so you can focus on the questions that prompted the metabolomics inquiry in the first place.

**HOW**  
MisoSoup processes experimental runs with up to >10<sup>8</sup> signals in seconds to minutes and organizes data in a relational model composed of eight core tables.

**WHAT**  
Here we demonstrate the data model and some of the MisoSoup features using a NIST SRM 1950 PASEF lipidomics run [[MSV000084402 in UCSD MassIVE](https://doi.org/doi:10.25345/C54T01)].  It was a study of lipids from NIST Standard Reference Material 1950 (pooled human plasma).  NIST SRM 1950 is a well-annotated material, with consensus measurements of absolute concentrations of many lipids available.  It is therefore a good "ground truth" sample for method development.

## Features
- processed data is stored in Parquet files for easy querying within and across mass-spec runs using:
    - [DuckDB](https://duckdb.org/) (shown here)
    - AWS Athena (not shown here)
- mass calibration using common background ions
- novel SQL-based algorithm for identifying peaks (local intensity maxima)
- linking peaks and MS2 spectra
- "backwards compatibility" with regular LCMS data (mzML processing coming soon)
- [interactive visualizations](https://misosoup.s3.amazonaws.com/MisoSoup-Preview.html) with [Altair/Vega](https://altair-viz.github.io/)

## Installation
```bash
git clone https://github.com/enveda/misosoup-preview.git # clone repo
cd misosoup-preview # change to directory
conda env create -f environment.yml # create environment
conda activate misosoup-preview # activate environment
jupyter notebook # start jupyter
```

Navigate to the `notebooks` directory and click on `Misosoup-Preview.ipynb`

## Usage
[HTML notebook with live, interactive plots](https://misosoup.s3.amazonaws.com/MisoSoup-Preview.html )

This repo contains one lipidomics run processed with MisoSoup, `msrun_id 'LIPID6950'`.  Upon importing misosoup, the Parquet files are registered as a DuckDB database, and are instantly available for querying via `MisoQuery`.

```python
import misosoup  # must be on sys.path
from misosoup.sql import MisoQuery as MSQ
MSQ("PRAGMA show_tables").run()
MSQ("SELECT * FROM peak WHERE msrun_id = 'LIPID6950'").run()
```

## Join Interest List
[google doc link](https://tinyurl.com/waut5dmp)

## Citation
This preview was presented as abstract #310348 at the 2022 Annual Conference of the American Society for Mass Spectrometry.
