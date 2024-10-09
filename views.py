from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

# In-memory session storage
sessions = {}

@csrf_exempt
def ussd(request):
    if request.method == 'POST':
        try:
            # Parse the incoming JSON request body
            data = json.loads(request.body.decode('utf-8'))
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

        # Extract necessary USSD fields from the request
        ussd_id = data.get('USERID', '')
        msisdn = data.get('MSISDN', '')
        user_data = data.get('USERDATA', '')
        msgtype = data.get('MSGTYPE', True)  # True if first request, False if subsequent
        session_id = data.get('SESSIONID', '')

        if not session_id:
            return JsonResponse({'error': 'SESSIONID is missing'}, status=400)

        # Retrieve or initialize the session based on the provided SESSIONID
        session = sessions.setdefault(session_id, {'screen': 1, 'feeling': '', 'reason': ''})

        # Initial request (first screen)
        if msgtype:  # First request
            msg = f"Welcome to {ussd_id} USSD Application.\nHow are you feeling?\n\n1. Feeling fine.\n2. Feeling frisky.\n3. Not well."
            session['screen'] = 1  # Set the screen to 1
            response_data = {
                "USERID": ussd_id,
                "MSISDN": msisdn,
                "USERDATA": user_data,
                "SESSIONID": session_id,
                "MSG": msg,
                "MSGTYPE": True
            }
        else:  # Subsequent requests
            if session['screen'] == 1:
                # Process the user's choice from Screen 1
                if user_data in ['1', '2', '3']:
                    session['feeling'] = ['Feeling fine', 'Feeling frisky', 'Not well'][int(user_data) - 1]
                    msg = f"Why are you {session['feeling']}?\n1. Money\n2. Relationship\n3. A lot"
                    session['screen'] = 2  # Move to Screen 2
                    response_data = {
                        "USERID": ussd_id,
                        "MSISDN": msisdn,
                        "USERDATA": user_data,
                        "SESSIONID": session_id,
                        "MSG": msg,
                        "MSGTYPE": True
                    }
                else:
                    # Invalid input, repeat Screen 1
                    msg = "Invalid choice. How are you feeling?\n1. Feeling fine\n2. Feeling frisky\n3. Not well"
                    response_data = {
                        "USERID": ussd_id,
                        "MSISDN": msisdn,
                        "USERDATA": user_data,
                        "SESSIONID": session_id,
                        "MSG": msg,
                        "MSGTYPE": True
                    }
                    return JsonResponse(response_data)

            elif session['screen'] == 2:
                # Process the user's choice from Screen 2
                if user_data in ['1', '2', '3']:
                    session['reason'] = ['because of money', 'because of relationship', 'because of a lot'][int(user_data) - 1]
                    msg = f"You are {session['feeling']} {session['reason']}."
                    response_data = {
                        "USERID": ussd_id,
                        "MSISDN": msisdn,
                        "USERDATA": user_data,
                        "SESSIONID": session_id,
                        "MSG": msg,
                        "MSGTYPE": False  # Final message, end session
                    }
                    # End the session after Screen 3
                    del sessions[session_id]
                else:
                    # Invalid input, repeat Screen 2
                    msg = f"Invalid choice. Why are you {session['feeling']}?\n1. Money\n2. Relationship\n3. A lot"
                    response_data = {
                        "USERID": ussd_id,
                        "MSISDN": msisdn,
                        "USERDATA": user_data,
                        "SESSIONID": session_id,
                        "MSG": msg,
                        "MSGTYPE": True
                    }
                    return JsonResponse(response_data)

        return JsonResponse(response_data)

    return JsonResponse({'error': 'Method not allowed'}, status=0)
