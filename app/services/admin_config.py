from datetime import datetime, timezone
from fastapi import HTTPException, status
from app.models.user import AdminConfig
from app.common import adminconfig

async def update_admin_config(data, session):
    admin_config = await get_admin_config(session)
    
    update_dict = {k: v for k, v in data.dict().items() if v is not None}
    for key, value in update_dict.items():
        setattr(admin_config, key, value)
    
    if len(update_dict) == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No admin config found in request")
    
    admin_config.updated_at = datetime.now(timezone.utc)
    session.add(admin_config)
    session.commit()
    adminconfig.update_config()

async def get_admin_config(session):
    admin_config = session.query(AdminConfig).first()
    if admin_config is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No admin config found in database")
    return admin_config