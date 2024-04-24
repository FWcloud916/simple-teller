# line webhook service
import os
from datetime import datetime

from linebot.v3 import WebhookParser
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (ApiClient, Configuration, FlexContainer,
                                  FlexMessage, MessagingApi,
                                  ReplyMessageRequest, TextMessage)
from notion_client import AsyncClient

from app.utils.json_tools import read_file


class LineWebhookService:
    """LineWebhookService"""

    def __init__(self, db_name: str = "main"):
        database_ids = {
            "main": os.environ.get("MAIN_DB_ID"),
            "wei": os.environ.get("WEI_DB_ID", ''),
        }
        self.notion_secret = os.environ.get("NOTION_SECRET")
        self.database_id = database_ids.get(db_name, database_ids["main"])
        self.client = AsyncClient(auth=self.notion_secret)
        self.configuration = Configuration(access_token=os.environ.get("LINE_CHANNEL_ACCESS_TOKEN"))
        self.parser = WebhookParser(os.environ.get("LINE_CHANNEL_SECRET"))

    async def transfer(self, body, signature):
        rows = []
        texts = []
        row_data = []
        try:
            events = self.parser.parse(body.decode("utf-8"), signature)
            with ApiClient(self.configuration) as api_client:
                line_bot_api = MessagingApi(api_client)
                for event in events:
                    txt = event.message.text
                    data = self.parse_event_text(txt)
                    row = await self.add_notion_row(**data)
                    row_data.append(data)
                    rows.append(row)
                    line_bot_api.reply_message_with_http_info(
                        ReplyMessageRequest(
                            reply_token=event.reply_token,
                            messages=[
                                TextMessage(text="Added to Notion"),
                                FlexMessage(
                                    alt_text="Added to Notion",
                                    contents=self.row_to_flex_message(data),
                                ),
                            ],
                        )
                    )
        except InvalidSignatureError:
            print(
                "Invalid signature. Please check your channel access token/channel secret."
            )
            raise
        return {"status": "ok", "row_data": row_data, "texts": texts, "rows": rows}

    async def add_notion_row(self, **kwargs):
        # Create a new row in the database
        row = await self.client.pages.create(
            parent={"database_id": self.database_id},
            properties={
                "title": {
                    "title": [{"text": {"content": kwargs.get("title", "test title")}}]
                },
                "In/Out": {"select": {"name": kwargs.get("in_out", "Out")}},
                "Category": {"select": {"name": kwargs.get("category", "Food")}},
                "Date": {
                    "date": {
                        "start": kwargs.get("date", datetime.now().strftime("%Y-%m-%d"))
                    }
                },
                "Amount": {"number": int(kwargs.get("amount", 0))},
                "Comment": {
                    "rich_text": [{"text": {"content": kwargs.get("comment", "")}}]
                },
            },
        )

        return row

    @staticmethod
    def fill_missing_data(data, columns):
        for column in columns:
            if column not in data:
                match column:
                    case "date":
                        data[column] = datetime.now().strftime("%Y-%m-%d")
                    case "comment":
                        data[column] = ""
                    case "amount":
                        data[column] = 0
                    case "in_out":
                        data[column] = "Out"
                    case "category":
                        data[column] = "Food"
                    case "title":
                        data[column] = "No title"
        return data

    def format_key_pairs_data(self, split_text: list, columns: list) -> dict:
        data = {}
        data_len = len(split_text)
        for i in range(data_len):
            if ":" in split_text[i]:
                key, value = split_text[i].split(":")
                if key not in columns:
                    continue
                data[key] = value
        if len(data) < len(columns):
            data = self.fill_missing_data(data, columns)
        return data

    def parse_event_text(self, text: str) -> dict:
        columns = ["title", "in_out", "category", "amount", "date", "comment"]
        with_key = ":" in text
        txt = text.split("\n")
        data_lens = len(txt)
        if with_key:
            data = self.format_key_pairs_data(txt, columns)
        else:
            data = {
                "title": txt[0],
                "amount": txt[1],
                "category": txt[4] if data_lens > 2 else "Food",
                "date": (
                    txt[2] if data_lens > 3 else datetime.now().strftime("%Y-%m-%d")
                ),
                "in_out": txt[3] if data_lens > 4 else "Out",
                "comment": txt[5] if data_lens > 5 else "",
            }

        data["amount"] = int(data["amount"])
        data["date"] = datetime.strptime(data["date"], "%Y-%m-%d").strftime("%Y-%m-%d")

        return data

    @staticmethod
    def row_to_flex_message(data: dict):
        template_string = read_file("app/templates/notion_row.json")
        template_string = template_string.replace(
            "#TITLE", data.get("title", "No title")
        )
        template_string = template_string.replace("#AMOUNT", str(data.get("amount", 0)))
        template_string = template_string.replace(
            "#DATE", data.get("date", datetime.now().strftime("%Y-%m-%d"))
        )
        template_string = template_string.replace("#IN_OUT", data.get("in_out", "Out"))
        template_string = template_string.replace(
            "#CATEGORY", data.get("category", "Food")
        )
        return FlexContainer.from_json(template_string)
