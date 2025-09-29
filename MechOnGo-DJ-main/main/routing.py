from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/mechanic/location/(?P<mechanic_id>\d+)/$', consumers.MechanicLocationConsumer.as_asgi()),
]