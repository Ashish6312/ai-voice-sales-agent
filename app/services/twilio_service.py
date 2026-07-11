"""
Twilio Service

This service handles outbound dialing using the Twilio Voice REST API. 
It initializes the Twilio REST Client using credentials defined in the settings (.env).

Core Responsibilities:
---------------------
1. Client Verification: Checks that Account SID, Auth Token, and Twilio Phone Number are present on startup.
2. Outbound Call Placement (make_call): Calls a lead's phone number and binds it to the configured webhook endpoints.

Call Flow & Callback Bindings:
-----------------------------
- Voice Webhook (url): When the customer answers, Twilio requests this endpoint (POST /twilio/voice) 
  to retrieve the initial greeting TwiML (<Gather> and <Say>).
- Status Callback (status_callback): Twilio sends asynchronous status updates (initiated, ringing, answered, completed) 
  to this endpoint (POST /twilio/status), allowing the CRM to record exact call durations and status updates in real-time.
"""

from twilio.rest import Client

from app.core.config import settings


class TwilioService:
    """
    Outbound calling client wrapper using the Twilio REST SDK.
    """

    def __init__(self):

        if not settings.twilio_account_sid:
            raise ValueError("TWILIO_ACCOUNT_SID is missing.")

        if not settings.twilio_auth_token:
            raise ValueError("TWILIO_AUTH_TOKEN is missing.")

        if not settings.twilio_phone_number:
            raise ValueError("TWILIO_PHONE_NUMBER is missing.")

        self.client = Client(
            settings.twilio_account_sid,
            settings.twilio_auth_token,
        )

    def make_call(
        self,
        phone_number: str,
    ) -> str:
        """
        Place an outbound call.
        """

        print("\n" + "=" * 60)
        print("CREATING TWILIO CALL")
        print("=" * 60)

        print(f"FROM : {settings.twilio_phone_number}")
        print(f"TO   : {phone_number}")

        print(
            f"VOICE WEBHOOK : {settings.public_base_url}/twilio/voice"
        )

        print(
            f"STATUS WEBHOOK: {settings.public_base_url}/twilio/status"
        )

        call = self.client.calls.create(
            to=phone_number,
            from_=settings.twilio_phone_number,
            url=f"{settings.public_base_url}/twilio/voice",
            method="POST",
            status_callback=f"{settings.public_base_url}/twilio/status",
            status_callback_method="POST",
            status_callback_event=[
                "initiated",
                "ringing",
                "answered",
                "completed",
            ],
        )

        print("\nCall Created Successfully")
        print(f"Call SID : {call.sid}")
        print(f"Status   : {call.status}")

        return call.sid