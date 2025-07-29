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

@app.post("/test")
def test():
    return {"hello": "world"}

class GetLiCaiPromptRequest(BaseModel):
    id: str

@app.post("/get_licai_prompt/", tags=["licai"])
async def get_licai_prompt(query: GetLiCaiPromptRequest):
    id = query.id
    # 如果id为空，则返回错误
    if not id:
        raise HTTPException(status_code=400, detail="id is required")
    # 根据id查询name，如果name为空，则返回错误
    TABLE_NAME = "hxb_licai_kv"
    response = supabase.table(TABLE_NAME).select("value").eq("item", id).eq("key", "name").execute()
    if not response.data or len(response.data) == 0:
        raise HTTPException(status_code=400, detail="name not found for the given id")
    name = response.data[0].get("value", "")
    # 开始收集相关数据，包括risk_level（风险等级）， type（产品类型），investment_period（投资期限）、7_days_annualized_yield（七日年化）、
    # agency(发行单位)、minimum_purchase_amount（起购点）、main_investment_direction（主要投资方向）、fee(费率）
    # liquidity（流动性）、advantage（产品特点优势）、other_info(其他信息)
    # 1. 开始收集risk_level
    response = supabase.table(TABLE_NAME).select("value").eq("item", id).eq("key", "risk_level").execute()
    if not response.data or len(response.data) == 0:
        raise HTTPException(status_code=400, detail="risk_level not found for the given id")
    risk_level = response.data[0].get("value", "")
    # 2. 开始收集type
    response = supabase.table(TABLE_NAME).select("value").eq("item", id).eq("key", "type").execute()
    if not response.data or len(response.data) == 0:
        raise HTTPException(status_code=400, detail="type not found for the given id")
    prod_type = response.data[0].get("value", "")
    # 3. 开始收集investment_period

    response = supabase.table(TABLE_NAME).select("value").eq("item", id).eq("key", "investment_period").execute()
    if not response.data or len(response.data) == 0:
        raise HTTPException(status_code=400, detail="investment_period not found for given id")
    investment_period = response.data[0].get("value", "")
    # 4. 开始收集7_days_annualized_yield
    response = supabase.table(TABLE_NAME).select("value").eq("item", id).eq("key", "7_days_annualized_yield").execute()
    if not response.data or len(response.data) == 0:
        raise HTTPException(status_code=400, detail="7_days_annualized_yield not found for given id")
    seven_days_annualized_yield = response.data[0].get("value", "")
    # 5. 开始收集agency
    response = supabase.table(TABLE_NAME).select("value").eq("item", id).eq("key", "agency").execute()
    if not response.data or len(response.data) == 0:
        raise HTTPException(status_code=400, detail="agency not found for given id")
    agency = response.data[0].get("value", "")
    # 6. 开始收集minimum_purchase_amount
    response = supabase.table(TABLE_NAME).select("value").eq("item", id).eq("key", "minimum_purchase_amount").execute()
    if not response.data or len(response.data) == 0:
        raise HTTPException(status_code=400, detail="minimum_purchase_amount not found for given id")
    minimum_purchase_amount = response.data[0].get("value", "")
    # 7. 开始收集main_investment_direction
    response = supabase.table(TABLE_NAME).select("value").eq("item", id).eq("key", "main_investment_direction").execute()
    if not response.data or len(response.data) == 0:
        raise HTTPException(status_code=400, detail="main_investment_direction not found for given id")
    main_investment_direction = response.data[0].get("value", "")
    # 8. 开始收集fee
    response = supabase.table(TABLE_NAME).select("value").eq("item", id).eq("key", "fee").execute()
    if not response.data or len(response.data) == 0:
        raise HTTPException(status_code=400, detail="fee not found for given id")
    fee = response.data[0].get("value", "")
    # 9. 开始收集liquidity
    response = supabase.table(TABLE_NAME).select("value").eq("item", id).eq("key", "liquidity").execute()
    if not response.data or len(response.data) == 0:
        raise HTTPException(status_code=400, detail="liquidity not found for given id")
    liquidity = response.data[0].get("value","")
    # 10. 开始收集advantage
    response = supabase.table(TABLE_NAME).select("value").eq("item", id).eq("key", "advantage").execute()
    if not response.data or len(response.data) == 0:
        raise HTTPException(status_code=400, detail="advantage not found for given id")
    advantage = response.data[0].get("value", "")
    # 11. 开始收集other_info
    # response = supabase.table(TABLE_NAME).select("value").eq("item", id).eq("key", "other_info").execute()
    # if not response.data or len(response.data) == 0:
    #     raise HTTPException(status_code=400, detail="other_info not found for given id")
    # other_info = response.data[0].get("value", "")
    data = {
        "risk_level": risk_level,
        "type": prod_type,
        "investment_period": investment_period,
        "seven_days_annualized_yield": seven_days_annualized_yield,
        "agency": agency,
        "minimum_purchase_amount": minimum_purchase_amount,
        "main_investment_direction": main_investment_direction,
        "fee": fee,
        "liquidity": liquidity,
        "advantage": advantage,
        "name": name,
    }

    # 开始构造prompt
    prompt_base = """你是一名资深银行理财顾问，请基于以下产品说明书数据，用通俗易懂的语言为用户解读该理财产品。要求：
核心原则：
1. 表情化标题：在四个模块标题前添加对应emoji（📍💰⚠️👥）
2. 生活化表达：用“您”代替“投资者”等人称，增强亲和力
3. 视觉分层：关键数据保留数字形式（如“可能亏损10%”）
4. 风险强化：⚠️标题必须使用警示性emoji
"""
    prompt_body = f"""{prompt_base}
输入数据:
产品名称： {name}
产品类型: {prod_type}
七日年化收益: {seven_days_annualized_yield}
风险等级: {risk_level}
投资方向: {main_investment_direction}
投资期限: {investment_period}
费用结构: {fee}
流动性: {liquidity}
产品特点/优势: {advantage}
起购金额: {minimum_purchase_amount}
发行机构: {agency}
    """
    prompt = f"""{prompt_body}
    输出规范：
```markdown
📍【产品定位】
这是一款适合[风险等级]投资者的[产品类型]理财产品

💰【收益特征】
主要投资于[简述资产组合]，目标收益区间参考X%-Y%（历史收益≠未来保证）

⚠️【风险提示】
最大可能亏损**[比例]本金**！关键风险点：[突出说明如股市波动/利率变化等]

👥【适合人群】
建议持有[时长]以上，适合能承受[比例]本金波动的[场景]资金  
"""
    return {"prompt": prompt}
    
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
    