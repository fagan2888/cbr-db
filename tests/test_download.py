from datetime import date
import os
from unittest.mock import MagicMock

from cbr_db.download import download, get_date


def test_get_last_modified(mocker):
    mock = MagicMock()
    mock.getheader = lambda x: 'Sat 16 Jan 2016 18:47:00'
    mocker.patch('cbr_db.download.urlopen', return_value=mock)
    assert get_date('http://example.com') == date(2016, 1, 16)


def test_download(mocker, tempdir):
    output_dir = os.path.join(tempdir, 'output')
    os.mkdir(output_dir)
    input_file_path = os.path.join(tempdir, 'remote_file.txt')
    with open(input_file_path, 'w') as file:
        file.write('Hello world!\nThis is a test.\n')

    def mock_urlopen(url):
        mock = open(input_file_path, 'rb')
        mock.getheader = lambda x: '2016-01-16'
        return mock

    mocker.patch('cbr_db.download.urlopen', mock_urlopen)
    mocker.patch('cbr_db.download.get_date', lambda x: date(2016, 1, 16))
    download('http://localhost/path/to/file', dir_=output_dir, force=False, verbose=True)
    # Make sure downloaded file is correct
    output_file_path = os.path.join(output_dir, 'file')
    with open(output_file_path, 'r') as file:
        assert file.read() == 'Hello world!\nThis is a test.\n'
    output_file_mtime = os.path.getmtime(output_file_path)
    # Try second time - must not actually download
    mocker.patch('cbr_db.download.urlopen',
                 side_effect=AssertionError('urlopen must not be called'))
    mocker.patch('cbr_db.download.get_date', lambda x: date(2016, 1, 16))
    download('http://localhost/path/to/file', dir_=output_dir, force=False, verbose=True)
    # Make sure file is not changed
    assert os.path.getmtime(output_file_path) == output_file_mtime
