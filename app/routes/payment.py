import json
import os
from fastapi import FastAPI, Form, Request, HTTPException, APIRouter, Depends
from fastapi.responses import RedirectResponse, JSONResponse, FileResponse
from app.common.security import oauth2_scheme, validate_access_token
from app.common.settings import get_settings
from fastapi.staticfiles import StaticFiles
from stripe import StripeError, stripe
from sqlalchemy.orm import Session
from app.common.database import get_session
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
async def customer_portal(user: User = Depends(get_current_user)):
    try:
        return_url = "https://dev0106.unwildered.co.uk"

        portalSession = stripe.billing_portal.Session.create(
            customer=user.stripeId,
            return_url=return_url,
        )
        return portalSession.url
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Server error")

@payments_router_protected.get("/prices")
async def get_prices():
    try:
        prices = stripe.Price.list(active=True, expand=['data.product'])
        return {"prices": prices.data}
    except StripeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    

@payments_router_protected.get("/create-payment-session")
async def create_payment_session(priceId: str, user: User = Depends(get_current_user)):
    print('Stripe ID', user.stripeId)
    try:
        if not user.stripeId:
            raise HTTPException(status_code=400, detail="Stripe ID not found")
        client_secret = payment.create_checkout_session(user.id, user.stripeId, priceId)
        return client_secret
    except HTTPException as http_exc:
        # This will handle our custom raised HTTPExceptions
        raise http_exc    
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Server error")

