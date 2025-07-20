from fastapi import FastAPI
from sqladmin import Admin
from starlette.middleware.sessions import SessionMiddleware

import siksha_admin.config as admin_config
from siksha_admin.auth import authentication_backend
from siksha_admin.db import async_session_maker, engine
from siksha_admin.views import (
    AdminUserAdmin,
    BoardAdmin,
    CommentAdmin,
    CommentLikeAdmin,
    CommentReportAdmin,
    ImageAdmin,
    MenuAdmin,
    MenuLikeAdmin,
    MenuOwnerAdmin,
    PostAdmin,
    PostLikeAdmin,
    PostReportAdmin,
    RestaurantAdmin,
    RestaurantOwnerAdmin,
    RestaurantRequestAdmin,
    UserAdmin,
    VersionAdmin,
)

app = FastAPI()

app.add_middleware(SessionMiddleware, secret_key=admin_config.ADMIN_SECRET)

admin = Admin(
    app, engine, session_maker=async_session_maker, authentication_backend=authentication_backend
)

# Add all views to admin
admin.add_view(VersionAdmin)
admin.add_view(UserAdmin)
admin.add_view(RestaurantAdmin)
admin.add_view(MenuAdmin)
admin.add_view(AdminUserAdmin)
admin.add_view(RestaurantRequestAdmin)
admin.add_view(BoardAdmin)
admin.add_view(PostAdmin)
admin.add_view(CommentAdmin)
admin.add_view(PostReportAdmin)
admin.add_view(CommentReportAdmin)
admin.add_view(MenuLikeAdmin)
admin.add_view(PostLikeAdmin)
admin.add_view(CommentLikeAdmin)
admin.add_view(ImageAdmin)

# Owner Views
admin.add_view(RestaurantOwnerAdmin)
admin.add_view(MenuOwnerAdmin)
