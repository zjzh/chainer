import threading

import six.moves.cPickle as pickle

from chainer.dataset import dataset_mixin


class PickleDatasetWriter(object):

    """Writer class which makes PickleDataset.

    To make :class:`PickleDataset`, a user need to prepare data using
    :class:`PickleDatasetWriter`.

    Args:
        writer: File like object that supports ``write`` and ``tell`` methods.
        protocol (int): Valid protocol for :mod:`pickle`.

    .. seealso: chainer.datasets.PickleDataset

    """

    def __init__(self, writer, protocol=pickle.HIGHEST_PROTOCOL):
        self.positions = []
        self.writer = writer
        self.protocol = protocol

    def close(self):
        self.writer.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def write(self, x):
        position = self.writer.tell()
        pickle.dump(x, self.writer, protocol=self.protocol)
        self.positions.append(position)

    def flush(self):
        self.writer.flush()


class PickleDataset(dataset_mixin.DatasetMixin):

    """Dataset stored in a storage using pickle.

    :mod:`pickle` is the default serialization library of Python.
    This dataset stores any objects in a storage using :mod:`pickle`.
    Even when a user want to use a large dataset, this dataset can stores all
    data in a large storage like HDD and each data can be randomly accessible.

    >>> with chainer.datasets.open_pickle_dataset_writer('/path/to/data') as w:
    ...     w.write((1, 2.0, 'hello'))
    ...     w.write((2, 3.0, 'good-bye'))
    ...
    >>> with chainer.datasets.open_pickle_dataset('/path/to/data') as dataset:
    ...     print(dataset[1])
    ...
    (2, 3.0, 'good-bye')

    Args:
        reader: File like object. `reader` must support random access.

    """

    def __init__(self, reader):
        if not reader.seekable():
            raise ValueError('reader must support random access')

        self.reader = reader
        self.positions = []
        reader.seek(0)
        while True:
            position = reader.tell()
            try:
                pickle.load(reader)
            except EOFError:
                break
            self.positions.append(position)

        self._lock = threading.RLock()

    def close(self):
        """Closes a file reader.

        After a user calls this method, the dataset is not accessible.
        """
        with self._lock():
            self.reader.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def __len__(self):
        return len(self.positions)

    def get_example(self, index):
        with self._lock:
            self.reader.seek(self.positions[index])
            return pickle.load(self.reader)


def open_pickle_dataset(path):
    """Opens a dataset stored in a given path.

    This is a hepler funciton to open :class:`PickleDataset`. It opens a given
    file in binary mode, and make :class:`PickleDataset` instance.

    This method does not close the opened file. A user needs to call
    :func:`PickleDataset.close`.

    Args:
        path (str): Path to a dataset.

    Returns:
        chainer.datasets.PickleDataset: Opened dataset.

    .. seealso: chainer.datasets.PickleDataset

    """
    reader = open(path, 'br')
    try:
        return PickleDataset(reader)
    except Exception:
        try:
            reader.close()
        except Exception:
            pass
        raise


def open_pickle_dataset_writer(path, protocol=pickle.HIGHEST_PROTOCOL):
    """Opens a writer to make a PickleDataset.

    This is a helper function to open :class:`PickleDatasetWriter`. It opens a
    given file in binary mode and make :clss:`PickleDatasetWriter` instance.

    This method does not close the opened file. A user needs to call
    :func:`PickleDatasetWriter.close`.

    Args:
        path (str): Path to a dataset.
        protocol (int): Valid protocol for :mod:`pickle`.

    Returns:
        chainer.datasets.PickleDatasetWriter: Opened writer.

    .. seealso: chainer.datasets.PickleDataset

    """
    writer = open(path, 'bw')
    try:
        return PickleDatasetWriter(writer, protocol=protocol)
    except Exception:
        try:
            writer.close()
        except Exception:
            pass
        raise
