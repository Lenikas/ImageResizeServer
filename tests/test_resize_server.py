import base64
import json
from os import remove
import pathlib

import pytest
from image_resizer.app import (
    Image,
    change_size_image,
    create_temp_image,
    queue_tasks,
    rd,
    server,
)


@pytest.fixture()
def client():
    with server.test_client() as client:
        yield client


@pytest.fixture()
def square_image_data():
    path = pathlib.Path(__file__).parent / 'square_test_image.gif'

    with open(path, 'rb') as f:
        image_data = base64.encodebytes(f.read())
        yield image_data.decode('ascii')


@pytest.fixture()
def not_square_image_data():
    path = pathlib.Path(__file__).parent / 'not_square_test_image.jpeg'

    with open(path, 'rb') as f:
        image_data = base64.encodebytes(f.read())
        yield image_data.decode('ascii')


@pytest.fixture(autouse=True)
def clean_db():
    yield
    rd.flushall()


@pytest.fixture(autouse=True)
def clean_queue():
    yield
    queue_tasks.empty()


@pytest.fixture(autouse=True)
def clean_temp():
    yield
    try:
        remove('temp')
    except FileNotFoundError:
        pass


def post_data(client, data):
    return client.post(
        '/task', data=json.dumps({'image': data}), content_type='application/json',
    )


def test_create_task_bad_data(client):
    response = post_data(client, '')
    data = json.loads(response.get_data())
    assert data['Warning'] == 'Incorrect data for image'


def test_create_task_bad_request(client):
    response = client.post(
        '/task', data=json.dumps({'bad_request': ''}), content_type='application/json',
    )
    data = json.loads(response.get_data())
    assert data['Error'] == 'Please give image in bytes format'
    assert response.status_code == 400


def test_create_task(client, square_image_data):
    response = post_data(client, square_image_data)
    data = json.loads(response.get_data())
    assert isinstance(data['Information'], dict)
    assert data['Information']['status'] == 'processing'


def test_create_task_not_square(client, not_square_image_data):
    response = post_data(client, not_square_image_data)
    data = json.loads(response.get_data())
    assert data['Error'] == 'Picture size must be quadratic'
    assert response.status_code == 400


def test_create_temp_image(square_image_data):
    image = create_temp_image(square_image_data.encode('ascii'))
    assert image.height == image.width


def test_get_task_state_empty(client):
    response = client.get('task/1')
    data = json.loads(response.get_data())
    assert data['Error'] == 'Invalid job id'


def test_get_task_state(client, square_image_data):
    post_data(client, square_image_data)
    jod_id = queue_tasks.job_ids[0]
    response = client.get('/task/{0}'.format(jod_id))
    data = json.loads(response.get_data())
    assert len(queue_tasks) == 1
    assert isinstance(data['Status'], str)


def test_get_image_empty(client):
    response = client.get('/task/0/32')
    data = json.loads(response.get_data())
    assert data['Error'] == 'Please check id of image and task status'


def test_change_size():
    path = pathlib.Path(__file__).parent / 'square_test_image.gif'
    image = Image.open(path)
    change_size_image(image, 0)
    data_32 = rd.hgetall(0)[bytes('32', 'utf-8')]
    data_64 = rd.hgetall(0)[bytes('64', 'utf-8')]
    assert data_32 is not None and data_64 is not None
