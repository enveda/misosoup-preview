# MisoSoup Preview

![misosoup logo](MisoSoup.png)

MisoSoup is a data processing pipeline for tandem mass-spectrometry data.
- processed data is stored in Parquet files for easy querying within and across mass-spec runs using:
    - DuckDB (shown here)
    - AWS Athena (not shown here)
- mass calibration using common background ions
- novel SQL-based algorithm for identifying peaks (local intensity maxima)
- links peaks and MS2 spectra
- interactive visualizations

## Installation
`conda env create -f environment.yml`

## Usage
```python
import misosoup
msq = misosoup.sql.get_chromatograms(['LIPID6950'])
msq.run()
```

## Join Interest List
[google doc link]

## Citation
This preview was presented as an abstract at ASMS [abstract ID].