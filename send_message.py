import os
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from dotenv import load_dotenv

from datetime import datetime
import boto3

# DynamoDB 설정
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('SlackMessages')

load_dotenv()
# 환경변수로부터 Bot User OAuth Token 불러오기
slack_token = os.getenv("SLACK_API_TOKEN")
client = WebClient(token=slack_token)

current_date = datetime.now().strftime("%b %d, %Y")
msg_text = (
    f"드디어 {current_date}!\n"
    "오늘도 :unicorn_face: 행복한 :sparkling_heart: 아침입니다! :sunny:\n"
    "출근 시간과 퇴근시간을 기록해주세요!"
)

try:
    # 메시지 전송
    response = client.chat_postMessage(
        channel="#bot-slack-message-test",
        text=msg_text,  
        blocks=[
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": msg_text}
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "출근"},
                        "action_id": "check_in"
                    },
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "퇴근"},
                        "action_id": "check_out"
                    }
                ]
            }
        ]
    )
    
    # 메시지의 timestamp 저장
    message_timestamp = response['ts']
    table.put_item(
        Item={
            'channel': '#bot-slack-message-test',
            'timestamp': message_timestamp
        }
    )
except SlackApiError as e:
    print(f"Error sending message: {e.response['error']}")
