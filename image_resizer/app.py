import base64
from io import BytesIO
from typing import Any

import redis
from flask import Flask, jsonify, request
from PIL import Image, UnidentifiedImageError
from rq import Queue

server = Flask(__name__)
rd = redis.Redis()
rd.flushdb()
queue_tasks = Queue(connection=rd)


@server.route('/task', methods=['POST'])
def create_task() -> Any:
    if not request.json or 'image' not in request.json:
        return jsonify({'Error': 'Please give image in bytes format'})

    byte_image: bytes = bytes(request.json.get('image'), 'ascii')
    try:
        temp_image = create_temp_image(byte_image)
    except UnidentifiedImageError:
        return jsonify({'Warning': 'Incorrect data for image'})

    if not check_quadratic(temp_image):
        return jsonify({'Error': 'Picture size must be quadratic'})
    image_id = len(queue_tasks)
    rd.hmset(str(image_id), {'original': byte_image})
    job_id = put_task(temp_image, image_id)

    return (
        jsonify(
            {
                'Information': {
                    'job_id': '{0}'.format(job_id),
                    'status': 'processing',
                    'image_id': '{0}'.format(image_id),
                }
            }
        ),
        201,
    )


def check_quadratic(temp_image: Image) -> bool:
    return temp_image.height == temp_image.width


def create_temp_image(byte_image: bytes) -> Image:
    decode_image = base64.decodebytes(byte_image)
    with open('temp', 'wb') as f:
        f.write(decode_image)
        image = Image.open('temp')
    return image


def change_size_image(temp_image: Image, image_id: int) -> None:
    resize_image_32 = temp_image.resize((32, 32))
    resize_image_64 = temp_image.resize((64, 64))

    img_32_bytes = BytesIO()
    resize_image_32.save(img_32_bytes, 'gif')

    img_64_bytes = BytesIO()
    resize_image_64.save(img_64_bytes, 'gif')

    rd.hmset(str(image_id), {'32': base64.encodebytes(img_32_bytes.getvalue())})
    rd.hmset(str(image_id), {'64': base64.encodebytes(img_64_bytes.getvalue())})


def put_task(temp_image: Image, image_id: int) -> str:
    job = queue_tasks.enqueue(change_size_image, temp_image, image_id)
    return job.id


@server.route('/task/<job_id>', methods=['GET'])
def get_task_state(job_id: str) -> Any:
    status = queue_tasks.fetch_job(job_id)
    if status is None:
        return jsonify({'Error': 'Invalid job id'})
    return (
        jsonify({'Status': '{0}'.format(status.get_status()), 'job_id': job_id}),
        200,
    )


@server.route('/task/<image_id>/<size>', methods=['GET'])
def get_image(image_id: str, size: str) -> Any:
    try:
        image = rd.hgetall(image_id)[bytes(size, 'utf-8')]
    except KeyError:
        return jsonify({'Error': 'Please check id of image and task status'})
    return jsonify({'Image': '{0}'.format(image)}), 200
