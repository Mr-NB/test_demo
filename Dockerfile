FROM python:3.8.2-alpine
WORKDIR /app
RUN apk add --no-cache --update gcc musl-dev libxslt-dev libressl-dev libffi-dev jpeg-dev zlib-dev freetype-dev lcms2-dev openjpeg-dev tiff-dev tk-dev tcl-dev libxml2-dev  libgcc openssl-dev curl
COPY requirements.txt ./
RUN export CRYPTOGRAPHY_DONT_BUILD_RUST=1 && python -m pip install --upgrade pip && pip install --no-cache-dir -i https://mirrors.aliyun.com/pypi/simple/ -r requirements.txt --upgrade --ignore-installed six
COPY . .

EXPOSE 8084

#CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8084"]
CMD ["python","main.py"]