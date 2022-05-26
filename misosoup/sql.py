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
