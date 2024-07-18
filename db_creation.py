import chromadb
from tqdm import tqdm
import pickle
import os


if __name__ == "__main__":
    files = os.listdir('jurisdictions')

    texts, metas, ids = [], [], []
    for f in tqdm(files):
        file_path = f'jurisdictions/{f}'
        filename = file_path.split('/')[1]
        with open(f"texts/{filename.replace('.pdf', '')}", "rb") as fp:
            text = pickle.load(fp)
        with open(f"metadata/{filename.replace('.pdf', '')}", "rb") as fp:
            meta = pickle.load(fp)
        with open(f"ids/{filename.replace('.pdf', '')}", "rb") as fp:
            idp = pickle.load(fp)

        texts.append(text)
        metas.append(meta)
        ids.append(idp)
    
    full_text, full_meta, full_id = [], [], []

    for text, meta, idp in zip(texts, metas, ids):
        for t, m, i in zip(text, meta, idp):
            full_text.append(m['country']+': '+t)
            full_meta.append(m)
            full_id.append(i)
    

    db = chromadb.PersistentClient()
    collection_name = "genai"

    if collection_name in [c.name for c in db.list_collections()]:
        db.delete_collection(collection_name)
        print("--- deleted ---")

    collection = db.get_or_create_collection(name=collection_name, 
               embedding_function=chromadb.utils.embedding_functions.DefaultEmbeddingFunction())

    batch_size = 300
    for i in tqdm(range(0, len(full_text), batch_size)):
        collection.add(documents=full_text[i:i+batch_size], ids=full_id[i:i+batch_size], metadatas=full_meta[i:i+batch_size], 
                images=None, embeddings=None)
        print(f"finished batch {i}-{i+batch_size}")
    collection.peek(1)