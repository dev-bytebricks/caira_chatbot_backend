from fastapi import HTTPException, status
from app.models.user import AdminConfig

async def update_admin_config(data, session):
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="This feature is under development")

async def get_admin_config(session):
    admin_config = session.query(AdminConfig).first()
    if admin_config is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No admin config found in database")
    return admin_config