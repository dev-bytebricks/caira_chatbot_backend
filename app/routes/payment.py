import json
import os
from fastapi import FastAPI, Form, Request, HTTPException, APIRouter, Depends
from fastapi.responses import RedirectResponse, JSONResponse, FileResponse
from app.common.security import oauth2_scheme, validate_access_token
from app.common.settings import get_settings
from fastapi.staticfiles import StaticFiles
import stripe
from sqlalchemy.orm import Session
from app.common.database import get_session
from app.services.user import update_user_payment, cancel_user_subscription
from app.services import payment
from app.common.security import get_current_user
from app.models.user import User

settings = get_settings()
# This is your test secret API key.
stripe.api_key = settings.STRIPE_SECRET_KEY

YOUR_DOMAIN = 'https://dev0106.unwildered.co.uk/'

payments_router_protected = APIRouter(
    prefix="/payment",
    tags=["Payment"],
    responses={404: {"description": "Not found, something wrong with auth"}},
    dependencies=[Depends(oauth2_scheme), Depends(validate_access_token),]
)

@payments_router_protected.post("/create-portal-session")
async def customer_portal(session_id: str = Form(...)):
    try:
        checkout_session = stripe.checkout.Session.retrieve(session_id)

        return_url = YOUR_DOMAIN

        portalSession = stripe.billing_portal.Session.create(
            customer=checkout_session.customer,
            return_url=return_url,
        )
        return RedirectResponse(url=portalSession.url, status_code=303)
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Server error")

@payments_router_protected.post("/create-payment-session")
async def create_payment_session(user: User = Depends(get_current_user)):
    print('Stripe ID', user.stripeId)
    try:
        if not user.stripeId:
            raise HTTPException(status_code=400, detail="Stripe ID not found")
        client_secret = payment.createCustomerSession(user.stripeId)
        return client_secret
    except HTTPException as http_exc:
        # This will handle our custom raised HTTPExceptions
        raise http_exc    
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Server error")

