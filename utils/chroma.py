import json
import os
from pathlib import Path
from typing import List

import chromadb
import chromadb.utils.embedding_functions as embedding_functions
from utils.CONFIG import (CHROMA_PERSISTENT_PATH, DATA_PATH,
                          EMBEDDING_MODEL_PATH)


class ChromaDB:
    def __init__(self, json_folder, md_folder, embeddings=None):
        self.json_folder = Path(json_folder)
        self.md_folder = Path(md_folder)

        self.embeddings = embedding_functions.SentenceTransformerEmbeddingFunction(
            EMBEDDING_MODEL_PATH
        )  # "BAAI/bge-base-zh-v1.5")
        self.embeddings._model = self.embeddings._model.to("cuda")

        self.persistent_client = chromadb.PersistentClient(CHROMA_PERSISTENT_PATH)
        self.para_col = self.persistent_client.get_or_create_collection(
            "para", embedding_function=self.embeddings
        )
        self.doc_col = self.persistent_client.get_or_create_collection(
            "doc", embedding_function=self.embeddings
        )

    def build_by_markdown(self):

        doc_ids = []
        docs = []
        doc_metas = []

        para_ids = []
        paras = []
        para_metas = []

        para_id = 0  # 段落的id, 全局自增
        for product_id, md_doc_path in enumerate(
            sorted(self.md_folder.glob("**/*.md"))
        ):
            if not os.path.exists(self.json_folder / f"{md_doc_path.stem}.json"):
                print(md_doc_path)
                continue
            if "团体" in str(md_doc_path.stem):
                continue # 去除团体保险
            if "附加" in str(md_doc_path.stem):
                continue # 去除附加险
            with open(self.json_folder / f"{md_doc_path.stem}.json") as json_file:
                j = json.load(json_file)
                content = f"产品名:{j['product']}, 覆盖：{j['coverage']}, 时长：{j['period']}, 类型: {j['type']}, 介绍: {j['introduction']}"
                j["filename"] = f"{md_doc_path.stem}.pdf"
                doc_ids.append(str(product_id))
                docs.append(content)
                doc_metas.append(j)

            with open(md_doc_path) as md_file:
                text = md_file.read()
                parts = text.split("###")
                for part in parts:
                    if len(part) <= 10:
                        continue  # 跳过过短的分片
                    meta = {
                        "filename": str(md_doc_path.stem),
                        "product": (
                            j["product"]
                            if j["product"] is not None
                            else str(md_doc_path.stem)
                        ),
                        "product_id": product_id,
                        "md_doc_path": str(md_doc_path),
                        "paragraph": part,
                        "header": part.split("\n")[0].strip(),
                    }
                    para_ids.append(str(para_id))
                    paras.append(part)
                    para_metas.append(meta)
                    para_id += 1

        self.para_col.add(para_ids, documents=paras, metadatas=para_metas)
        self.doc_col.add(doc_ids, documents=docs, metadatas=doc_metas)

    def query_doc(self, query_content: str):
        results = self.doc_col.query(query_texts=query_content)
        return results

    def query_para(self, query_content: str, doc_ids: str | List[str]):
        if isinstance(doc_ids, str):
            doc_ids = [doc_ids]
        results = self.para_col.query(
            query_texts=query_content,
            where={"product_id": {"$in": doc_ids}},
            n_results=40,
        )
        return results

    def read_md(self, filename):
        with open(self.md_folder / filename / "auto" / f"{filename}.md", "r") as f:
            return f.read().strip()


if __name__ == "__main__":
    db = ChromaDB(f"{DATA_PATH}/json", f"{DATA_PATH}/markdown")  # chroma
    db.build_by_markdown() # 只需在迁移后运行一次 cd <项目代码仓库根路径> && python -m utils.chroma
    # print(db.query_doc("本合同养老保险金领取方式分为年领和月领两种方式"))
    # print(db.query_para("保险责任",[0,1,2]))
