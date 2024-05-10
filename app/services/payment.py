from app.common.settings import get_settings
import stripe
from stripe import Subscription, Customer, CustomerSession
import logging
from fastapi import FastAPI, Form, Request, HTTPException, APIRouter, Depends
from app.models.user import User

logger = logging.getLogger(__name__)
settings = get_settings()
# This is your test secret API key.
stripe.api_key = settings.STRIPE_SECRET_KEY


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

def checkUserSubscription(subscriptionId): 
    subscription = Subscription.retrieve(id=subscriptionId, expand= ['items.data.price.product'])


    if(subscription):
        status = subscription["status"]
        items = subscription["items"]["data"][0]
        plan = items["price"]["lookup_key"]
        
        print(f'Plan {plan}')
        print(f'Status {status}')

        if(status == "active"):
            return True
        else:
            raise("Subscription is not active")
    else:
        return False

def createCustomerSession(customerId): 
    customer = CustomerSession.create(customer=customerId, components= {"pricing_table": {"enabled": True}})
    
    return customer


def getUserId(customerId):
    user = Customer.retrieve(id=customerId)

            