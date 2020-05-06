# Image Resizer
    A server that allows you to change the size of a square image 
    to 64x64 or 128x128. Work with image in base64 format.
    
    При POST-запросе на адрес “/task” в теле запроса передается картинка, 
    закодированная в base64. В ответ приходит id задачи, статус выполнения задачи 
    и id картинки, используя который можно будет получить измененную картинку. 
    HTTP-код ответа должен равняться 201.

    Далее пользователь может проверять статус выполнения задачи с помощью GET-запроса 
    на адрес “/task/<id задачи>”. В ответ приходит id задачи, статус выполнения задачи 
    и id картинки. HTTP-код ответа — 200.

    Когда задача окажется выполненной, пользователь может получить картинку в нужном размере 
    с помощью GET-запроса на адрес “/image/<id картинки>?size=<64, 32 или original>”

### Description:
    Автор:Сагалов Леонид

### Create venv:
    make venv

### Run tests:
    make test

### Run linters:
    make lint

### Run formatters:
    make format

### Build service:
	make build
