from flask import Flask, request, jsonify, make_response
import os
import json
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

# from dotenv import load_dotenv

from datetime import datetime

import boto3
from boto3.dynamodb.conditions import Key

### utils 함수
from utils import WorkHoursCalculator

from pytz import timezone

# load_dotenv()

app = Flask(__name__)

client = WebClient(token=os.getenv("SLACK_API_TOKEN"))
dynamodb = boto3.resource('dynamodb', region_name='ap-northeast-2')
in_table = dynamodb.Table('teamlab-commuting')

@app.route("/", methods=["POST"])
def slack_event():
    payload_json = json.loads(request.form.get('payload'))
    
    # 현재 시간/날짜 가져오기
    korea = timezone('Asia/Seoul')
    current_time = datetime.now(korea).strftime("%H:%M")
    current_date = datetime.now(korea).strftime("%Y-%m-%d")
    
    # Verify the event type
    if payload_json['type'] == 'block_actions':
        action = payload_json['actions'][0]
        user_id = payload_json['user']['id']
        trigger_id = payload_json['trigger_id']
        
        # 사용자 이름 가져오기
        try:
            user_info = client.users_info(user=user_id)
            user_name = user_info['user']['real_name']
        except SlackApiError as e:
            print(f"Error getting user info: {e.response['error']}")
            user_name = "Unknown User"
        
        # 출근 메시지 전송
        try:
            in_response = in_table.query(
                KeyConditionExpression=Key('user_id').eq(user_id),
                Limit=1,
                ScanIndexForward=False  # 최신 항목부터 조회
            )
            in_last_event = in_response['Items'][0] if in_response['Items'] else None
            
            # 출근 버튼 눌리면
            if action['action_id'] == 'check_in':
                in_table.put_item(
                    Item={
                        'user_id': user_id,
                        'timestamp':f"{current_date}#{current_time}",
                        'status': 'in'
                    }
                )
                msg_text = f"{user_name}님 {current_time}에 출근하셨습니다."
            
            #퇴근 버튼 눌리면
            elif action['action_id'] == 'check_out':
                if in_last_event and in_last_event['status'] == 'in':
                    ### utils 함수 활용
                    _, in_time = in_last_event['timestamp'].split('#')
                    calculator = WorkHoursCalculator(in_time, current_time)
                    hours, minutes = calculator.calculate_hours()
                    
                    in_table.put_item(
                        Item={
                            'user_id': user_id,
                            'timestamp':f"{current_date}#{current_time}",
                            'status': 'out'
                        }
                    )
                    msg_text = f"{user_name}님 {current_time}에 퇴근하셨습니다. \n근무시간은 {hours}시간 {minutes}분입니다. "
                else:
                    # 출근 안눌리고 퇴근부터 눌리면 모달 에러 메시지
                    client.views_open(
                        trigger_id=trigger_id,
                        view={
                            "type": "modal",
                            "title": {"type": "plain_text", "text": "오류"},
                            "blocks": [
                                {
                                    "type": "section",
                                    "text": {
                                        "type": "mrkdwn",
                                        "text": f"{user_name}님, 출근 버튼을 먼저 눌러주세요."
                                    }
                                }
                            ]
                        }
                    )
                    return make_response("", 200)
                    
            else:
                msg_text = "Unknown action"
            
            client.chat_postMessage(
                channel=payload_json['channel']['id'],
                thread_ts=payload_json['message']['ts'],
                text=msg_text
            )
        except SlackApiError as e:
            print(f"Error sending message: {e.response['error']}")
        

    return make_response("", 200)

if __name__ == '__main__':
    app.run(debug=True)  