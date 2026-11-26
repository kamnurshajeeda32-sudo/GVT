from alembic import context
from app.db import get_engine, Base
from app import models
with get_engine().connect() as connection:
    context.configure(connection=connection,target_metadata=Base.metadata)
    with context.begin_transaction():
        context.run_migrations()
