# Dockerfile

# 使用 Python 官方镜像作为基础镜像
FROM python:3.13-alpine as base
FROM base as builder
COPY requirements.txt /requirements.txt
RUN pip install --user -r /requirements.txt

FROM base
# copy only the dependencies installation from the 1st stage image
COPY --from=builder /root/.local /root/.local
COPY main.py /app/main.py
# COPY common /app/common
# COPY bot.py /app/bot.py
WORKDIR /app

# update PATH environment variable
ENV PATH=/home/app/.local/bin:$PATH

# 暴露端口（与FastAPI运行端口一致）
EXPOSE 8000

# 启动命令（使用uvicorn运行应用，支持多线程和自动重载）
CMD ["python", "main.py"]
