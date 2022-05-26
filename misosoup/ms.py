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
