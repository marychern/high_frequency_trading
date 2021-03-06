from channels import Group, Channel
from channels.generic.websockets import JsonWebsocketConsumer
from .decorators import timer
from .dispatcher import LEEPSDispatcher
from .models import Player
import logging

log = logging.getLogger(__name__)

class SubjectConsumer(JsonWebsocketConsumer):

    def raw_connect(self, message, subsession_id, group_id, player_id):
        player = Player.objects.get(id=player_id)
        Group(player.market_id).add(message.reply_channel)
        self.connect(message, subsession_id, group_id, player_id)

    def connect(self, message, subsession_id, group_id, player_id):
        player = Player.objects.get(id=player_id)
        log.info('Player %s is connected to Group %s with in-group id %s.' % (
            player_id, group_id, player.id_in_group))
        player.channel = message.reply_channel
        player.save()

    @timer
    def raw_receive(self, message, subsession_id, group_id, player_id):
        try:
            LEEPSDispatcher.dispatch('websocket', message, subsession_id=subsession_id,
                market_id=group_id, player_id=player_id)
        except Exception as e:
            log.exception('player %s: error processing message, ignoring. %s:%s', 
                player_id, message.content, e)

    def raw_disconnect(self, message, subsession_id, group_id, player_id):
        player = Player.objects.get(id=player_id)
        Group(player.market_id).add(message.reply_channel)      

class InvestorConsumer(JsonWebsocketConsumer):

    @timer
    def raw_receive(self, message, subsession_id):
        try:
            LEEPSDispatcher.dispatch('websocket', message, subsession_id=subsession_id)
        except Exception as e:
            log.exception('error processing investor arrival, ignoring. %s:%s', message.content, e)

class JumpConsumer(JsonWebsocketConsumer):

    def raw_receive(self, message, subsession_id):
        try:
            LEEPSDispatcher.dispatch('websocket', message, subsession_id=subsession_id)
        except Exception as e:
            log.exception('error processing fundamental value change, ignoring. %s:%s', message.content, e)
