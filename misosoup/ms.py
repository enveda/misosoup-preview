__doc__ = """
MisoSoup Data Models for mass spectrometry data.

Classes
-------
Run : a batch of experimental runs
Frame : one MS run, with frame-by-frame overview
MS1Signal : MS1 data points
XIC : extracted ion chromatogram
    Σ(intensity) at specific retention time and MS1 mass range
Peak : local intensity maxima
MSMS : tandem MS fragmentation events
PeakMSMS : all peak–MSMS relationships
MS2Signal : MS2 data points
"""


# ------------------------------------------------------------------------------
# MS Data Containers
# ------------------------------------------------------------------------------


class MisoBase:
    pass


class MSRun(MisoBase):
    """A collection of mass-spec runs.

    Relationships:
    - a run is one of many runs from the same experimental batch;
    - each run has one msrun_id for joining with Benchling metadata;
    - each run has one URI for retrieving data from cloud storage;
    - each run consists of many frames;
    - each run consists of many MSMS fragmentations;
    - each run consists of many MS1 signals;
    - each run consists of many MS2 signals.

    Notes
    -----
    The field extra_info is a dict/JSON-like field of SQL type STRUCT:
    https://docs.aws.amazon.com/athena/latest/ug/rows-and-structs.html
    """

    db_fields = {
        "name": "run name",
        "uri": "data location in cloud storage",
        "sample_type": "type of sample (Sample/QC/Blank)",
        "ionization_mode": "ionization mode of the sample",
        "extra_info": "additional information about the run in STRUCT format",
        "batch_name": "ELN display name of the experiment",
        "batch_eln_id": "ELN database key of the experiment",
        "batch_id": "ELN display id of the experiment",
        "vendor_id": "origin of mass-spec data",
        "id": "MS run ID; partition",
    }


class Frame(MisoBase):
    """A collection of mass spectra.

    Relationships:
    - a frame is one of many mass spectra within a run acquired at the same
      chromatographic retention time (RT, the first separation dimension);
    - each frame represents either ms_level=1 spectra or ms_level=2 spectra
      and reveals aggregate information about the spectra, including:
      - number of spectra
      - number of signals
      - total ion count (TIC)
    - each frame consists of 0-to-many MS1 signals;
    - each frame consists of 0-to-many MS2 signals;
    - each ms1_level=1 frame gives rise to 0-to-many MSMS fragmentation
      events;
    - each ms1_level=2 frame arises from to 0-to-many MSMS fragmentation
      events.
    """

    db_fields = {
        "frame": "a collection of signals with a given retention time",
        "ms_level": "MS level: 1 for MS1, 2 for MS2",
        "rt": "retention time of the frame (sec)",
        "num_spectra": "number of spectra within the frame",
        "num_signals": "number of signals across all Spectra within the frame",
        "accum_time": str(
            "how long (msec) TIMS tunnel collects incoming ions "
            "(scaling factor for intensity)",
        ),
        "tic": "total ion count for the frame",
        "top_intensity": "top intensity within the frame",
        "msrun_id": "MS run ID (msrun.id); PK",
    }


class MS1Signal(MisoBase):
    """MS1 signal data.

    Relationships:
    - an MS1 signal is one of many within an MS1 frame;
    - an MS1 signal takes part in 0 or 1 (MS1) fragmentation event.
    """

    db_fields = {
        "id": "raw index of the signal within a run (not a unique ID)",
        "frame": "frame number of the signal",
        "spectrum": "spectrum (scan) number of the signal",
        "tof": "TOF values of the signal",
        "mz": "mass-to-charge ratio of the signal",
        "mz_group": "ordinal number of a mass cluster within a run",
        "raw_intensity": "raw signal intensity (counts per unit time)",
        "intensity": str(
            "scaled signal intensity "
            "(normalized by frame accumulation time)"
        ),
        "msrun_id": "MS run ID (msrun.id); PK",
    }


class XIC(MisoBase):
    """Extracted Ion Chromatogram (XIC) for MS1 mass groups.

    Relationships:
    - this is an aggregate table where each row represents integrated MS1
      signal at a certain frame, and a certain mz_group;
    - each frame consists of 0-to-many XIC points;
    - each XIC point may or may not be an XIC peak (local intensity maximum).

    Notes
    -----
    The field `mz` is the low-accuracy simple average mz of the signals
    from a given mz_group, in a given frame.  The "center of mass"
    (intensity-weighted average mz) can differ from a simple average by
    as much as 50 mDa.
    """

    db_fields = {
        "ms1_frame_number": "MS1 frame number (X axis for clustering)",
        "frame": "frame number of the signal",
        "rt": "retention time of the frame (sec)",
        "mz_group": "ordinal number of a mass cluster within a run",
        "mz": "average mass within a cluster",
        "mz_min": "minimal mz value in this mz_group, in this frame",
        "mz_max": "maximal mz value in this mz_group, in this frame",
        "n_tof_bins": "count of TOF bins in this mz_group, in this frame",
        "spectrum_min": "first spectrum in this mz_group, in this frame",
        "spectrum_med": "median spectrum in this mz_group, in this frame",
        "spectrum_max": "last spectrum in this mz_group, in this frame",
        "n_spectra": "count of unique spectra",
        "n_signals": "number of signals per mz_group per frame",
        "intensity": "sum of scaled intensity per mz_group per frame",
        "xic_peak": "peak (local maximum) ID within a run",
        "auc": "integrated signal within 5 seconds of the local peak",
        "msrun_id": "MS run ID (msrun.id); PK",
    }


class Peak(MisoBase):
    """Local maxima of MS1 signal.

    Relationships:
    - a peak is an MS1 signal that is a local intensity maximum
      in a neighborhood of a size defined by the peak picking function
    """

    db_fields = {
        "peak_id": "ordinal number of the peak within a run",
        "ms1_id": "raw index of MS1 signal at peak center",
        "mz_group": "ordinal number of a mass cluster within a run",
        "xic_peak": "chromatographic peak ID within a run",
        "frame": "frame number of MS1 signal at peak center",
        "rt": "retention time (sec) of MS1 signal at peak center",
        "spectrum": "spectrum (scan) number of MS1 signal at peak center",
        "tof": "TOF index of MS1 signal at peak center",
        "mz": "intensity-weighted average mz of the peak",
        "feature_id": "ordinal number of the feature within a run",
        "peak_num": "ordinal number of the peak within a feature",
        "delta_mz": "mass difference between current and lightest isotope within a feature",
        "intensity": "sum of intensity of signals in the peak neighborhood",
        "n_signals": "number of signals in the peak neighborhood",
        "msrun_id": "MS run ID (msrun.id); PK",
    }


class MSMS(MisoBase):
    """MSMS or PASEF fragmentation (frag) events within a run.

    Relationships:
    - an MSMS event is one of many frag events within a run;
    - an MSMS event has one parent frame and yields 1-to-many
      child frames;
    - an MSMS event converts 0-to-many parent (usually MS1) signals to
      0-to-many child (usually MS2) signals;
    """

    db_fields = {
        "id": "MS fragmentation event ID (precursor ID)",
        "parent_frame": "parent (MS1) frame",
        "child_frame": "child (MS2) frame",
        "spectrum_min": "first scan of the fragmentation window",
        "spectrum_max": "last scan of the fragmentation window",
        "isolation_mz": "center mass value of the fragmentation window",
        "isolation_width": "mass width of the fragmentation window",
        "collision_energy": "collision energy (eV)",
        "uncorrected_precursor_mz": "instrument-recorded m/z of the source ion",
        "precursor_mz": "m/z of the source ion, with mass correction",
        "precursor_charge": "instrument-recorded charge of the source ion",
        "precursor_intensity": "instrument-recorded intensity of the source ion(s)",
        "msrun_id": "MS run ID (msrun.id); PK",
    }


class PeakMSMS(MisoBase):
    """Peak–MSMS relationships.

    Relationships:
    - a Peak–MSMS event means this peak fell into that MSMS window.
    """

    db_fields = {
        "feature_id": "ordinal number of the feature within a run",
        "peak_num": "ordinal number of the peak within a feature",
        "peak_id": "ordinal number of the peak within a run",
        "xic_peak": "chromatographic peak ID within a run",
        "mz_group": "ordinal number of a mass cluster within a run",
        "ms1_id": "raw index of MS1 signal at peak center",
        "peak_frame": "frame number of MS1 signal at peak center",
        "peak_spectrum": "spectrum (scan) number of MS1 signal at peak center",
        "peak_intensity": "peak intensity",
        "precursor_mz": "intensity-weighted average mz of the peak",
        "msms_id": "MS fragmentation event ID (precursor ID)",
        "mz_min": "lower edge of the mass window",
        "mz_max": "upper edge of the mass window",
        "msms_rt": "retention time of the parent (MS1) MSMS event",
        "msms_frame": "parent (MS1) frame of the MSMS event",
        "spectrum_min": "first scan of the fragmentation window",
        "spectrum_max": "last scan of the fragmentation window",
        "instrument_precursor_mz": "instrument-recorded m/z of the source ion",
        "collision_energy": "collision energy (eV)",
        "msrun_id": "MS run ID (msrun.id); PK",
    }


class MS2Signal(MisoBase):
    """MS2 signal data.

    Relationships:
    - an MS2 signal is one of many within an MS2 frame;
    - an MS2 signal takes part in 0 or 1 MS3 fragmentation event
      or arises from 1 MS1 fragmentation event.
    """

    db_fields = {
        "id": "raw index of the signal within a run (not a unique ID)",
        "frame": "frame number of the signal",
        "spectrum": "spectrum (scan) number of the signal",
        "tof": "TOF values of the signal",
        "mz": "mass-to-charge ratio of the signal",
        "mz_group": "ordinal number of a mass cluster within a run",
        "raw_intensity": "raw signal intensity (counts per unit time)",
        "intensity": str(
            "scaled signal intensity "
            "(normalized by frame accumulation time)"
        ),
        "msms_id": "MSMS fragmentation event that yielded the MS2 signal",
        "msrun_id": "MS run ID (msrun.id); PK",
    }
