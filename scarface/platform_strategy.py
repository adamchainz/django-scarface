# -*- coding: utf-8 -*-
import json
from abc import ABCMeta

from django.conf import settings

from scarface.settings import DEFAULT_STRATEGIES

__author__ = 'janmeier'

# def get_strategies():
#     strategy_modules = DEFAULT_STRATEGIES
#
#     if hasattr(settings, 'SCARFACE_PLATFORM_STRATEGIES'):
#         strategy_modules.append(settings.SCARFACE_PLATFROM_STRATEGIES)
#
#     for strategy_path in strategy_modules:
#         strategy = _import_strategy(strategy_path)
#     return strategy

def _import_strategy(path):
    components = path.split('.')
    mod = __import__(components[0])
    for comp in components[1:]:
        mod = getattr(mod, comp)
    return mod

class PlatformStrategy(metaclass=ABCMeta):
    def __init__(self, platform_application):
        super().__init__()
        self.platform = platform_application

    def format_payload(self, data):
        return {self.platform.platform: json.dumps(data)}

    def format_push(self, badgeCount, context, context_id, has_new_content, message,
                sound):
        if message:
            message = self.trim_message(message)

        payload = {
            'aps': {
                "content-available": has_new_content,
            },
            "ctx": context,
            "id": context_id
        }

        if message and len(message) > 0:
            payload['aps']['alert'] = message

        if not badgeCount is None:
            payload['aps'].update({
                "badge": badgeCount,
            })

        if not sound is None:
            payload['aps'].update({
                'sound': sound,
            })

        return payload

    def trim_message(self,message):
        import sys

        if sys.getsizeof(message) > 140:
            while sys.getsizeof(message) > 140:
                message = message[:-3]
            message += '...'
        return message


class APNPlatformStrategy(PlatformStrategy):
    def format_payload(self, message):
        """
        :type message: PushMessage
        :param message:
        :return:
        """

        payload = self.format_push(
            message.badge_count,
            message.context,
            message.context_id,
            message.has_new_content,
            message.message, message.sound
        )

        if message.extra_payload:
            payload.update(message.extra_payload)

        return super(
            APNPlatformStrategy,
            self
        ).format_payload(payload)


class GCMPlatformStrategy(PlatformStrategy):
    def format_payload(self, message):
        """
        :type data: PushMessage
        :param data:
        :return:
        """
        data = message.as_dict()
        h = hash(frozenset(data.items()))
        return super(
            GCMPlatformStrategy,
            self
        ).format_payload({"collapse_key": h, "data": data})
