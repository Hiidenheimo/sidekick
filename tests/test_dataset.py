import functools
import os
import zipfile

import numpy as np
import pandas as pd
import pytest
from PIL import Image

import sidekick


@pytest.fixture
def dataset_index(tmpdir):
    n_rows = 32

    # Create image stored in temporary file
    image_file_path = str(tmpdir.join('test_image.jpg'))
    Image.new(mode='RGB', size=(640, 320)).save(image_file_path)

    # Create columns for dataset
    integer_column = np.random.randint(0, 10, size=n_rows)
    float_column = np.random.rand(n_rows)
    string_column = ['foo'] * n_rows
    numpy_column = list(np.random.rand(n_rows, 3))
    image_column = [
        Image.new(mode='RGB', size=(64, 32)) for _ in range(n_rows)
    ]
    image_file_column = [image_file_path for _ in range(n_rows)]

    # Build dataset index
    return pd.DataFrame({
        'integer_column': integer_column,
        'float_column': float_column,
        'string_column': string_column,
        'numpy_column': numpy_column,
        'image_column': image_column,
        'image_file_column': image_file_column,
        'image_file_process_column': image_file_column
    })


def test_create_dataset_sequential(dataset_index, tmpdir):
    # Create dataset
    dataset_path = str(tmpdir.join('dataset.zip'))
    resize_image = functools.partial(sidekick.process_image, crop_size=(32, 8))
    set_image_format = functools.partial(sidekick.process_image, format='png')

    sidekick.create_dataset(
        dataset_path,
        dataset_index,
        path_columns=['image_file_column', 'image_file_process_column'],
        preprocess={
            'image_file_process_column': resize_image,
            'image_column': set_image_format
        },
        progress=True,
        parallel_processing=0
    )
    assert os.path.exists(dataset_path) and os.path.getsize(dataset_path) > 100


def test_create_dataset_parallel(dataset_index, tmpdir):
    # Create dataset
    dataset_path = str(tmpdir.join('dataset.zip'))
    resize_image = functools.partial(sidekick.process_image, crop_size=(32, 8))
    set_image_format = functools.partial(sidekick.process_image, format='png')

    sidekick.create_dataset(
        dataset_path,
        dataset_index,
        path_columns=['image_file_column', 'image_file_process_column'],
        preprocess={
            'image_file_process_column': resize_image,
            'image_column': set_image_format
        },
        progress=False,
        parallel_processing=10
    )
    assert os.path.exists(dataset_path) and os.path.getsize(dataset_path) > 100


def test_dataset_metadata(dataset_index, tmpdir):
    # Create dataset
    dataset_path = str(tmpdir.join('dataset.zip'))
    set_image_format = functools.partial(sidekick.process_image, format='png')
    sidekick.create_dataset(
        dataset_path,
        dataset_index,
        preprocess={'image_column': set_image_format}
    )

    # Assert the .sidekick metadata was added
    with zipfile.ZipFile(dataset_path, 'r') as zf:
        assert '.sidekick' in zf.namelist()


def test_import_multiple_formats(tmpdir):
    size = (64, 32)
    images = [
        Image.new(mode='RGBA', size=size),
        Image.new(mode='LA', size=size),
        Image.new(mode='RGB', size=size),
        Image.new(mode='L', size=size)
    ]

    df = pd.DataFrame({
        'image_column': images
    })
    dataset_path = str(tmpdir.join('dataset.zip'))
    set_image_format = functools.partial(sidekick.process_image, format='png')

    sidekick.create_dataset(
        dataset_path,
        df,
        preprocess={
            'image_column': set_image_format
        },
        progress=True,
        parallel_processing=0
    )
    assert os.path.exists(dataset_path) and os.path.getsize(dataset_path) > 100
