# misosoup/mol.py

__doc__ = """
MisoSoup Molecules module contains methods for calcuting mass
and other molecular properties.

Methods
-------
hrms : HRMS with fine isotopic distribution
lrms : LRMS with coarse isotopic distribution
mw_range : calculates monoisotopic mass with a given tolerance (in ppm)
"""

import logging
import molmass
import numpy as np
import pandas as pd

from IsoSpecPy import IsoThresholdGenerator

log = logging.getLogger(__name__)


# ------------------------------------------------------------------------------
# Globals & Constants
# ------------------------------------------------------------------------------


class M:
    """Molecular weights of common fragments."""

    E = 0.00054858


# ------------------------------------------------------------------------------
# Mass Calculations
# ------------------------------------------------------------------------------


def hrms(formula, charge=1, precision=6, th=1e-3) -> pd.DataFrame:
    """Simulates a high-resolution MS with fine isotopic distribution.

    Parameters
    ----------
    formula : str
        Molecular formula as a string.
    charge : int (default: +1)
        Charge of the molecule
    precision : int, default 6
        Rounds m/z values to this number of significant digits
    th : float, default 1e-3
        A parameter for IsoSpecPy that signifies a threshold
        of probability (i.e. rel. isotope abundance) that remains unassigned
        to a particular mass.  By default, when .999 of probability is covered,
        no additional isotopes are considered

    Returns
    -------
    Pandas dataframe with standard autoincrementing index and columns:
    - tmz: theoretical m/z; mass of gained/lost electrons is accounted for
    - tri: theoretical relative intensity, normalized to 1 million

    Notes
    -----
    The formula is passed through the molmass interpretor, but IsoSpecPy
    won't handle inputs with specified isotope labels that are permitted
    in molmass (e.g. [13C]O2).  Method ``lrms`` uses molmass only, and can
    handle compounds with unnatural isotopic composition.   If fine
    isotopic patterns are needed, check IsoSpecPy documentation:
    https://github.com/MatteoLacki/IsoSpec/blob/master/Examples/Python
    """

    try:
        ef = molmass.Formula(formula)
        _spectrum = IsoThresholdGenerator(formula=ef.formula, threshold=th)
    except molmass.FormulaError as e:
        log.error(f"unable to interpret {formula}: {e}")
        return None
    except ValueError as e:
        log.error(f"unable to interpret {ef}: {e}")
        return None

    df = pd.DataFrame(columns=["tmz", "tri"], data=[i for i in _spectrum])
    df.sort_values(["tmz"], inplace=True)

    if charge != 0:
        df["tmz"] -= M.E * charge
        df["tmz"] /= abs(charge)

    df["tmz"] = np.round(df["tmz"], precision)
    df["tri"] = np.int32(df["tri"] * 1e6)
    return df


def lrms(formula, charge=1, precision=5) -> pd.DataFrame:
    """Simulates a low-resolution mass spectrum.

    Parameters
    ----------
    formula : str
        Molecular formula as a string.  Examples of valid formulas:
        [2H]2O, Et3N, CuSO4.5H2O, (COOH)2,
        AgCuRu4(H)2[CO]12{PPh3}2, CGCGAATTCGCG, MDRGEQGLLK
        (exercise caution with one-letter peptides and nucleotides)
    charge : int (default: +1)
        Charge of the molecule
    precision : int, default 5
        Rounds m/z values to this number of significant digits

    Returns
    -------
    Pandas dataframe where index is the mass number, and columns:
    - tmz: theoretical m/z; mass of gained/lost electrons is accounted for
    - tri: theoretical relative intensity, normalized to 1 million

    Notes
    -----
    Let's discuss the distinction from ``hrms`` on the example of
    trimethylglycine monocation:
        lrms('C5H12NO2', 1, 6).loc[119, 'tmz'] returns 119.089303, which is
    the average mass of [13C], [2H], [15N], and [17O] isotopologues, weighted
    by their relative abundance.  The exact masses and abundances
    can be obtained with hrms('C5H12NO2'):
        '15N': (119.083291, 0.003466)
        '13C': (119.089611, 0.050740)
        '17O': (119.090473, 0.000715)
        '2H' : (119.092533, 0.001295)
    The 15N peak is separated from other M+1 peaks by 6 mDa. Depending on the
    instrument resolution and centroiding, the 15N may or may not be averaged
    together with other M+1 peaks, which can alter its average mass.

    For each mass number, the abundance-weighted average mass is returned,
    simulating a low-res instrument.  To get the exact mass and abundance
    of the main isotopologues for each mass number, try:
        ms = misosoup.ingred.hrms('(CH3SiOCH3)8 NH4')
        ms.loc[ms.groupby(np.floor(ms.tmz)).tri.idxmax()]
    """

    try:
        ef = molmass.Formula(formula)
        _spectrum = ef.spectrum(minfract=1e-4)
    except molmass.FormulaError as e:
        log.error(f"unable to interpret {formula}: {e}")
        return None

    for _, v in _spectrum.items():
        if charge != 0:
            v[0] -= M.E * charge
            v[0] /= abs(charge)

    df = pd.DataFrame(_spectrum).T
    df.columns = ["tmz", "tri"]
    df["tmz"] = np.round(df["tmz"], precision)
    df["tri"] = np.int32(df["tri"] * 1e6)
    return df


def mw_range(mf, charge=1, tol_ppm=10) -> np.ndarray:
    """Provides a range of mz values for a particular molecular formula.

    Returns
    -------
    An array with lower and upper mz bounds, within a certain tolerance
    around the mass of the lightest neutromer.

    Examples
    --------
    >>> misosoup.mol.mw_range('C28H30N2O3 + H', tol_ppm=20)
    """

    mw = hrms(mf, charge=charge).iloc[0, 0]
    return np.round((mw * (1 - tol_ppm * 1e-6), mw * (1 + tol_ppm * 1e-6)), 6)
