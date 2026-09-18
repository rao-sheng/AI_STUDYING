from pathlib import Path
import hashlib
def read_document(file_path:Path) ->str:
    return file_path.read_text(encoding="utf-8")

def split_document(text:str,source:str,chunk_size:int=500) ->list[dict]:
    chunks=[]
    current_heading=""
    for paragraph in text.split("\n\n"):
        paragraph=paragraph.strip()
        if not paragraph:
            continue
        if "\n" not in paragraph and paragraph.startswith("# "):
            current_heading=paragraph
            continue
        if "\n" not in paragraph and paragraph.startswith("## "):
            current_heading=paragraph
            continue
        heading_prefix=(
            current_heading+"\n"
            if current_heading
            else ""
        )
        body_size=chunk_size-len(heading_prefix)

        if body_size<=0:
            raise ValueError("标题过长，请增大chunk_size")
        pieces=split_by_sentence(
            paragraph,
            chunk_size=body_size
        )
        for piece in pieces:
            chunks.append({
                "id": f"{source}_{len(chunks) + 1:03d}",
                "source": source,
                "text": heading_prefix + piece
            })
    return chunks 

def calculate_text_hash(text:str) ->str:
    text_bytes=text.encode("utf-8")
    return hashlib.sha256(text_bytes).hexdigest()

def split_long_text(text:str,chunk_size:int=500,overlap:int=100) ->list[str]:
    if chunk_size<=0:
        raise ValueError("chunk_size必须要大于0")
    if not 0<=overlap<chunk_size:
        raise ValueError("overlap必须满足条件：0<overlap<chunk_size")
    pieces=[]
    start=0
    while start<len(text):
        end=start+chunk_size
        pieces.append(text[start:end])
        if end >len(text):
            break 
        start=end-overlap

    return pieces

def split_by_sentence(text:str,chunk_size:int=50) ->list[str]:
    if chunk_size<=0:
        raise ValueError("chunk_size必须要大于0")
    pieces =[] #已经保存好的片段列表
    current=""#正在组装，还没有保存的一个片段
    for part in text.split("。"):
        sentence=part.strip()
        if not sentence:
            continue
        sentence+="。"
        #单句本身太长，退回字符切分
        if len(sentence)>chunk_size:
            if current:
                pieces.append(current)
                current=""
            pieces.extend(
                split_long_text(
                    sentence,chunk_size=chunk_size,overlap=0
                )
            )
            continue
        #当前片段装不下这句话，先保存，再开始新片段
        if len(current)+len(sentence)>chunk_size:
            pieces.append(current)
            current=sentence
        else:
            current+=sentence
    #循环结束后，保存最后尚未放入列表的片段
    if current:
        pieces.append(current)
    return pieces

if __name__=="__main__":
    test_text = (
    "## 账户与工作区\n\n"
    "每个账户最多创建三个工作区。\n\n"
    "不同工作区的数据相互独立。"
)

    test_chunks = split_document(test_text, source="demo.md")

    for chunk in test_chunks:
        print(chunk["text"])
        print()
    

    



