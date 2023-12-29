from flask import Flask, request, jsonify, make_response
import os
import json
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from dotenv import load_dotenv

from datetime import datetime


load_dotenv()

app = Flask(__name__)

client = WebClient(token=os.getenv("SLACK_API_TOKEN"))


user_status = {} # 사용자 출퇴근 상태 딕셔너리
user_last_check_in = {} # 사용자 마지막 출근 일자 딕셔너리



@app.route("/", methods=["POST"])
def slack_event():
    payload_json = json.loads(request.form.get('payload'))
    
    # 현재 시간/날짜 가져오기
    current_time = datetime.now().strftime("%H:%M")
    current_date = datetime.now().strftime("%Y-%m-%d")
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
            if action['action_id'] == 'check_in':
                if user_last_check_in.get(user_id) != current_date:
                    user_status[user_id] = 'in'
                    user_last_check_in[user_id] = current_date
                    msg_text = f"{user_name}님 {current_time}에 출근하셨습니다."
                else:
                    # 오늘 출근 버튼을 한번 눌렸으면 에러 모달
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
                                        "text": f"{user_name}님, 오늘 이미 출근하셨습니다."
                                    }
                                }
                            ]
                        }
                    )
                    return make_response("", 200)
            elif action['action_id'] == 'check_out':
                if user_status.get(user_id) == 'in':
                    user_status[user_id] = 'out'
                    msg_text = f"{user_name}님 {current_time}에 퇴근하셨습니다."
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
    app.run(debug=True, port=5002)