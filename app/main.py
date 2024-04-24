from typing import Annotated

from fastapi import FastAPI, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum

from app.services.line import LineWebhookService

app = FastAPI(
    title="Social network platform",
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)

allow_origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
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
