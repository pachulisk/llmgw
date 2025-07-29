from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from litellm import completion
from dotenv import load_dotenv
load_dotenv()
from supa import supabase

import os

app = FastAPI(title="DeepSeek 流式对话接口", version="1.0")

# 定义请求模型 - 使用Deepseek官方确认的有效模型名称
class StreamChatRequest(BaseModel):
    message: str
    system_prompt: str = "你是一个有用的助手，会用简洁明了的语言回答问题。"
    model: str = "deepseek-chat"  # 正确的模型名称

# 健康检查接口
@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "deepseek-streaming-chat-api"}

# 流式输出的单轮对话接口
@app.post("/stream-chat")
async def stream_chat(request: StreamChatRequest):
    try:
        # 检查API密钥
        if not os.getenv("DEEPSEEK_API_KEY"):
            raise HTTPException(status_code=500, detail="请设置DEEPSEEK_API_KEY环境变量")
        
        # 定义生成器函数，用于流式返回数据
        def generate():
            # 调用模型，开启流式响应
            response = completion(
                model=request.model,
                messages=[
                    {"role": "system", "content": request.system_prompt},
                    {"role": "user", "content": request.message}
                ],
                api_base="https://api.deepseek.com/v1",  # 官方API地址
                stream=True  # 开启流式输出
            )
            
            # 逐块返回数据
            for chunk in response:
                if chunk.choices and chunk.choices[0].delta.content:
                    # 返回SSE格式的数据
                    yield f"data: {chunk.choices[0].delta.content}\n\n"
            
            # 发送结束标志
            yield "data: [DONE]\n\n"
        
        # 返回流式响应，指定媒体类型为text/event-stream
        return StreamingResponse(
            generate(),
            media_type="text/event-stream"
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"调用模型时发生错误: {str(e)}")

# 非流式对话接口
class ChatRequest(BaseModel):
    message: str
    system_prompt: str = "你是一个有用的助手，会用简洁明了的语言回答问题。"
    model: str = "deepseek-chat"  # 正确的模型名称

class ChatResponse(BaseModel):
    response: str
    model_used: str

@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    try:
        if not os.getenv("DEEPSEEK_API_KEY"):
            raise HTTPException(status_code=500, detail="请设置DEEPSEEK_API_KEY环境变量")
        
        response = completion(
            model=request.model,
            messages=[
                {"role": "system", "content": request.system_prompt},
                {"role": "user", "content": request.message}
            ],
            api_base="https://api.deepseek.com/v1"
        )
        
        return {
            "response": response.choices[0].message.content,
            "model_used": request.model
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"调用模型时发生错误: {str(e)}")

class GetLiCaiItemRequest(BaseModel):
    item: str

@app.post("/get_licai_item", tags=["licai"])
async def get_licai_item(query: GetLiCaiItemRequest):
    item = query.item
    # 如果item为空，返回空列表
    if not item:
        return { "data": [] }
    TABLE_NAME = "hxb_licai_kv"
    response = supabase.table(TABLE_NAME).select("*").eq("item", item).execute()
    return { "data": response.data }

class UpdateLiCaiItemRequest(BaseModel):
    item: str
    key: str
    value: str

@app.post("/update_licai_item", tags=["licai"])
async def update_licai_item(query: UpdateLiCaiItemRequest):
    item = query.item
    key = query.key
    value = query.value
    # 如果item为空，返回错误
    if not item:
        raise HTTPException(status_code=400, detail="item is required")
    # 如果key为空，返回错误
    if not key:
        raise HTTPException(status_code=400, detail="key is required")
    # 如果value是空，则不更新，直接返回成功
    if value is None:
        return {"status": "success", "message": "value is None, no update performed"}
    # 通过supabase的upsert功能，更新或者插入数据
    data = {
        "item": item,
        "key": key,
        "value": value
    }
    TABLE_NAME = "hxb_licai_kv"
    response = supabase.table(TABLE_NAME).upsert(data).execute()
    return response

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
    