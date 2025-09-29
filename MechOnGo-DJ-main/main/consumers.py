from channels.generic.websocket import JsonWebsocketConsumer
from django.contrib.auth.models import User
from .models import MechanicLocation, Job
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

class MechanicLocationConsumer(JsonWebsocketConsumer):
    def connect(self):
        self.mechanic_id = self.scope['url_route']['kwargs']['mechanic_id']
        self.group_name = f'mechanic_location_{self.mechanic_id}'
        
        try:
            self.mechanic = User.objects.get(id=self.mechanic_id)
            self.channel_layer.group_add(self.group_name, self.channel_name)
            self.accept()
            logger.info(f"WebSocket connected for mechanic {self.mechanic.username}")
        except User.DoesNotExist:
            self.close()
            logger.error(f"WebSocket connection failed: Mechanic ID {self.mechanic_id} not found")

    def disconnect(self, close_code):
        self.channel_layer.group_discard(self.group_name, self.channel_name)
        logger.info(f"WebSocket disconnected for mechanic {self.mechanic_id}")

    def receive_json(self, content):
        latitude = content.get('latitude')
        longitude = content.get('longitude')
        job_id = content.get('job_id')

        if not latitude or not longitude or not job_id:
            self.send_json({'error': 'Missing required fields'})
            return

        try:
            job = Job.objects.get(id=job_id, mechanic=self.mechanic, status__in=['en_route', 'in_progress'])
            MechanicLocation.objects.create(
                mechanic=self.mechanic,
                job=job,
                latitude=latitude,
                longitude=longitude
            )
            self.channel_layer.group_send(
                self.group_name,
                {
                    'type': 'location_update',
                    'latitude': latitude,
                    'longitude': longitude,
                    'timestamp': timezone.now().isoformat()
                }
            )
            logger.info(f"Location updated for mechanic {self.mechanic.username} for job {job_id}")
        except Job.DoesNotExist:
            self.send_json({'error': 'Invalid job or not authorized'})
            logger.error(f"Invalid job {job_id} for mechanic {self.mechanic_id}")

    def location_update(self, event):
        self.send_json({
            'latitude': event['latitude'],
            'longitude': event['longitude'],
            'timestamp': event['timestamp']
        })