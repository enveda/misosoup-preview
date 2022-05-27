# misosoup-preview/misosoup/sql.py

__doc__ = """
APIs for misosoup SQL tables.

SQL query templates are stored in the .sql files, organized in folders
according to the DB engine used.  For all functions defined here, default
arguments are provided for building the query from a .sql template.
"""

import logging

log = logging.getLogger(__name__)

import duckdb
import numpy as np
import os
import pandas as pd
import pkgutil

from pyarrow.dataset import dataset as pyarrow_dataset

# ------------------------------------------------------------------------------
# Globals & Constants
# ------------------------------------------------------------------------------

DATA_ROOT = os.path.abspath("../data/")
os.chdir(DATA_ROOT)  # we start in the data folder by default


# ------------------------------------------------------------------------------
# Register Parquet Files as DuckDB database
# ------------------------------------------------------------------------------


def register_parquet_data(folder=DATA_ROOT):
    duckdb_connection = duckdb.connect()
    for table in os.listdir(folder):
        path = os.path.join(DATA_ROOT, table)
        dataset = pyarrow_dataset(path, format="parquet", partitioning="hive")
        duckdb_connection.register(table, dataset)
    return duckdb_connection


DUCKDB_CONN = register_parquet_data()

# ------------------------------------------------------------------------------
# MisoQuery
# ------------------------------------------------------------------------------


class MisoQuery(str):
    """Utility class for doing useful things with query strings.

    Attributes
    ----------
    count : str
        Wraps original query into CTE and returns its row counts.

    Examples
    --------
    # all query templates listed here return a MisoQuery object:
    >>> msq = misosoup.sql.get_chromatograms('LIPID6950')
    >>> msq.count.run()
    >>> msq.run()
    """

    def __init__(self, query: str):
        self.lines = query.split("\n")

    def run(self, db_engine="duckdb", footer=""):
        """Executes query using db_engine (only DuckDB at this time).

        Parameters
        ----------
        db_engine : str, default and only implemented="athena"
            type of database reader engine
        footer : str, default=''
            line(s) to append to query (e.g. LIMIT 420)
        """

        if footer:
            self = MisoQuery(self + f"\n{footer}")

        if db_engine == "duckdb":
            con = DUCKDB_CONN
            try:
                df = con.execute(self).df()
                n_rows = len(df)
                log.debug(f"query returned {n_rows} rows")
                # con.close()
                return df

            except Exception as e:
                log.error(e)
                # con.close()
                return None

        elif db_engine == "athena":
            raise NotImplementedError

        else:
            raise NotImplementedError

    @property
    def count(self):
        """Query for getting count of rows the parent query would return.

        Wraps original query into `result` CTE and returns
        `SELECT COUNT(*) FROM result`.
        """

        return MisoQuery(
            "\n".join(
                [
                    "WITH result AS (",
                    "\n".join(["\t" + line for line in self.lines]),
                    ") SELECT COUNT(1) AS row_count FROM result",
                ]
            )
        )


# ------------------------------------------------------------------------------
# Query Functions
# ------------------------------------------------------------------------------


def get_chromatograms(
    msrun_ids, *, ms_level=1, template="duckdb/get_chromatograms.sql",
):
    """Get chromatogram (frame-by-frame overview) by msrun_ids.

    Parameters
    ----------
    msrun_ids : Iterable[str]
        list of msrun_ids
    ms_level : int, default=1
        MS level for which to retrieve frame data
    template : str, default "duckdb/get_chromatograms.sql"
        SQL query template.
    """

    _msrun_ids = sanitize_list(msrun_ids)
    query = fetch_template(template).format(
        msrun_ids=_msrun_ids, ms_level=ms_level,
    )
    return MisoQuery(query)


def get_ms1_features(
    msrun_ids,
    *,
    feature_id=None,
    mz_range=None,
    rt_range=None,
    min_ms1_intensity=10,
    rt_window=10.0,
    spectrum_window=5,
    tof_window=3,
    template="duckdb/get_ms1_features.sql",
):
    """Get MS1 features and their neighborhood signals.

    Parameters
    ----------
    msrun_ids : Iterable[str]
        A collection of msrun_ids (list, tuple, set, numpy, pandas)
        or a single msrun_id (str).
    feature_id : int
        filter by feature ID
    mz_range : Iterable[float, float]
        filter by feature m/z range
    rt_range : Iterable[float, float]
        filter by feature retention time range
    min_ms1_intensity : int
        filter MS1 signal by its corrected intensity
    rt_window : float, default=10.0
        diameter of retention time window around the peak
    tof_window : int, default=3
        radius of TOF window around the peak
    spectrum_window : int, default=5
        diameter of spectrum(scan) window around the peak
    template : str, default "duckdb/get_ms1_features.sql"
        SQL query template.

    Examples
    --------
    >>> features = misosoup.sql.get_ms1_features('LIPID6950').run()
    >>> # 1033418 rows in 16.8 s
    """

    _filter_clauses = ""

    if feature_id is not None:
        clause = f"AND feature_id = {feature_id}"
        _filter_clauses += "\n\t" + clause

    if validate_range(mz_range):
        clause = f"AND mz BETWEEN {mz_range[0]} AND {mz_range[1]}"
        _filter_clauses += "\n\t" + clause

    if validate_range(rt_range):
        clause = f"AND rt BETWEEN {rt_range[0]} AND {rt_range[1]}"
        _filter_clauses += "\n\t" + clause

    _msrun_ids = sanitize_list(msrun_ids)

    query = fetch_template(template).format(
        msrun_ids=_msrun_ids,
        filter_clauses=_filter_clauses,
        min_ms1_intensity=min_ms1_intensity,
        rt_window=rt_window,
        tof_window=tof_window,
        spectrum_window=spectrum_window,
    )
    return MisoQuery(query)


# ------------------------------------------------------------------------------
# Utility Functions
# ------------------------------------------------------------------------------


def fetch_template(template: str):
    """Loads a sql template.  If not a .sql file, the string is the template.

    Parameters
    ----------
    template : str
        SQL query template (path a ".sql" file or a custom template string).
    """

    if template.endswith(".sql"):
        try:
            _template = pkgutil.get_data(__name__, template).decode()
        except FileNotFoundError as e:
            print(e)
    else:
        _template = template
    return _template


def sanitize_list(list_like_arg):
    """SQL input sanitizaton for passing list-like args into IN operator."""

    if isinstance(list_like_arg, str):
        _ids = f"('{list_like_arg}')"
    elif isinstance(list_like_arg, (list, tuple, set, np.ndarray, pd.Series)):
        if len(list_like_arg) == 1:
            _ids = f"('{list_like_arg[0]}')"
        else:
            _ids = tuple(list_like_arg)
    else:
        raise TypeError(
            "IDs must be one of: "
            "(str, list, tuple, set, np.ndarray, pd.Series)"
        )
    return _ids


def validate_range(field_range) -> bool:
    """Check if field_range is provided and ensure correct format."""

    if field_range is None:
        return False
    if (
        isinstance(field_range, (list, tuple, np.ndarray))
        and len(field_range) == 2
        and field_range[0] <= field_range[1]
    ):
        return True
    else:
        raise ValueError(f"invalid range: {field_range}")
