import logging
import os
import pathlib

logger = logging.getLogger("api_server")
logger.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

# 记录日志文件
script_home = pathlib.Path(os.path.abspath(__file__)).parent
os.makedirs(script_home / "logs", exist_ok=True)
file_handler = logging.FileHandler(
    script_home / "logs" / "api_server.log", encoding="utf-8"
)
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# 打印到控制台
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.INFO)
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)
