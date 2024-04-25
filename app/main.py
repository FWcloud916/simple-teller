from typing import Annotated

import uvicorn
from fastapi import FastAPI, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum

from app.services.line import LineWebhookService

app = FastAPI(
    title="Simple Teller",
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/api/line/webhooks")
async def line_webhooks(
        x_line_signature: Annotated[str | None, Header()], request: Request
):
    # get X-Line-Signature header value
    signature = x_line_signature

    # get request body as text
    body = await request.body()

    line_service = LineWebhookService("main")
    return await line_service.transfer(body, signature)


handler = Mangum(app)


if __name__ == "__main__":
    uvicorn.run(app, port=8000)
