FROM python:3.6

WORKDIR /app

COPY dynamic /app
COPY support /app
COPY .gitignore /app
COPY Dockerfile /app
COPY gui.py /app
COPY LICENSE /app
COPY README.md /app
COPY requirements.txt /app

RUN pip install -r requirements.txt

CMD ["python", "./gui.py"]