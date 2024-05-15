from app.common.settings import get_settings
import stripe
from stripe import Subscription, Customer, CustomerSession
import logging
from fastapi import FastAPI, Form, Request, HTTPException, APIRouter, Depends
from app.models.user import User
from pydantic import BaseModel

logger = logging.getLogger(__name__)
settings = get_settings()
# This is your test secret API key.
stripe.api_key = settings.STRIPE_SECRET_KEY

class SubscriptionStatus(BaseModel):
    plan: str
    status: bool

async def create_customer(user: User):
    try:
        # Create a new customer in Stripe
        stripe_customer = stripe.Customer.create(
            email=user.email,
            name=user.name,
            description="Customer for {}".format(user.email),
        )
        # Save the stripe customer ID in your database for future use
        # For example: update_user_with_stripe_id(user.email, stripe_customer.id)
        
        return stripe_customer.id
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=str(e))

def checkSubscriptionStatus(subscriptionId): 
    subscription = Subscription.retrieve(id=subscriptionId, expand= ['items.data.price.product'])
    
    if(subscription):
        status = subscription["status"]
        items = subscription["items"]["data"][0]
        plan = items["price"]["lookup_key"]        

        if(status == "active"):
            print("Updating plan", plan)
            return SubscriptionStatus(plan=plan, status=True)
        else:
            return SubscriptionStatus(plan="free", status=False)
    else:
        raise HTTPException(status_code=400, detail="Subscription was not found")

def create_checkout_session(userId, customer_id, price_id):
    try:
        # Attempt to create a checkout session
        session = stripe.checkout.Session.create(
            customer=customer_id,
            payment_method_types=['card'],  # Add or remove as per your requirement
            line_items=[{
                'price': price_id,  # Price ID passed from the frontend
                'quantity': 1,
            }],
            client_reference_id= userId,
            mode='subscription',
            success_url='http://localhost:3000/success?session_id={CHECKOUT_SESSION_ID}',
            cancel_url='http://localhost:3000/cancel',
        )
        # Check if the session is successfully created
        if not session:
            raise HTTPException(status_code=404, detail="Failed to create checkout session")
        return session
    except stripe.error.StripeError as e:
        # Handle Stripe API errors specifically
        print(f"Stripe API error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # Handle other generic exceptions if needed
        print(f"An error occurred: {e}")
        raise HTTPException(status_code=500, detail="An internal error occurred")


def getUserId(customerId):
    user = Customer.retrieve(id=customerId)

            