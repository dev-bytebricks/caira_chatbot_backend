from fastapi import Request, HTTPException, APIRouter, Depends
from fastapi.responses import JSONResponse
import stripe.webhook
from app.common.settings import get_settings
import stripe
from sqlalchemy.orm import Session
from app.common.database import get_session
from app.services.user import update_user_payment

settings = get_settings()
# This is your test secret API key.
stripe.api_key = settings.STRIPE_SECRET_KEY
webhook_secret = settings.STRIPE_WEBHOOK_SECRET

stripe_router = APIRouter(
    prefix="/stripe",
    tags=["Stripe"],
    responses={404: {"description": "Not found, something wrong with auth"}},
    dependencies=[]
)

@stripe_router.post("/webhook")
async def webhook_received(request: Request, session: Session = Depends(get_session)):
    try:
        # Correctly retrieve the raw body for signature verification
        signature = request.headers.get('stripe-signature')
        request_body_bytes = await request.body()  # This reads the body as bytes
        event = stripe.Webhook.construct_event(
            payload=request_body_bytes,  # Pass the raw bytes of the request body
            sig_header=signature,
            secret=webhook_secret)
        data = event['data']
    except Exception as e:
        print(e, "error in stripe ")
        raise HTTPException(status_code=400, detail="Webhook signature verification failed.")
    
    event_type = event['type']
    data_object = data['object']
    
    # Handle the event accordingly

    if event_type == 'customer.subscription.updated':
        if data_object["customer"]:
            subscription_id = data_object["id"]
            customer_id = data_object["customer"]

            await update_user_payment(customer_id, subscription_id, session)

    if event_type == 'customer.subscription.deleted':
        if data_object["status"] == "canceled":
            customer_id = data_object["customer"]
            subscription_id = data_object["id"]

            await update_user_payment(customer_id, subscription_id, session)
         
    # Handle other events...

    return JSONResponse({'status': 'success'})

