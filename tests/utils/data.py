"""
A collection of test utilities for retrieving unittest data
"""
import csv
import os


class dotdict(dict):  # pylint: disable=invalid-name
    """dot.notation access to dictionary attributes"""
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__


def get_test_data_filename(shortname):
    """
    Returns the fully qualified filepath of the requested test data file.
    """
    vmbasepath = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../../")
    )
    filename = f"{vmbasepath}/tests/data/{shortname}"

    if not os.path.exists(filename):
        raise FileNotFoundError(f"no such test file: {shortname}")

    return filename


def get_test_data(name):
    """
    Given a short filename from tests/data/[FILENAME], will open the file
    and return all of its contents.
    """
    with open(get_test_data_filename(name), 'r', encoding='utf-8') as f:
        data = f.read().strip()

    return data


def get_test_data_tsv(name, abspath=None):
    """
    Opens and parses a tsv file, yielding individual lines as arrays of
    python maps, mapping the column name to the value.

    The given tsv file MUST have a header row.
    """
    filename = abspath or get_test_data_filename(name)
    with open(filename, encoding='utf-8') as fd:
        tsv_reader = csv.reader(fd, delimiter="\t")
        headers = None
        for line in tsv_reader:
            if headers is None:
                headers = line
                continue

            row = {}
            for idx, header in enumerate(headers):
                row[header] = line[idx]

            yield row

def get_test_rows_tsv(name, abspath=None):
    """
    Opens and parses a tsv file, yielding individual lines as a list.

    Needed for mocking the PrestoReader results as it parses an array, not a
    dictionary.
    """
    filename = abspath or get_test_data_filename(name)
    with open(filename, encoding='utf-8') as fd:
        tsv_reader = csv.reader(fd, delimiter="\t")
        headers = None
        for line in tsv_reader:
            if headers is None:
                headers = line
                continue

            yield line

def get_test_data_csv(name):
    """
    Opens and parses a csv file, yielding individual lines as arrays of
    python maps, mapping the column name to the value.

    The given csv file MUST have a header row.
    """
    with open(get_test_data_filename(name), encoding='utf-8') as fd:
        csv_reader = csv.reader(fd)
        headers = None
        for line in csv_reader:
            if headers is None:
                headers = line
                continue

            row = {}
            for idx, header in enumerate(headers):
                row[header] = line[idx]

            yield row
