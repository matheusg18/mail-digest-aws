import uuid
from datetime import timezone

from factory.base import Factory
from factory.declarations import Sequence, SubFactory
from factory.faker import Faker

from shared.domain.delivery_channel import DeliveryChannel, DeliveryChannelEnum
from shared.domain.telegram.telegram_chat import TelegramChat
from shared.domain.telegram.telegram_message import TelegramMessage
from shared.domain.user import User


class TelegramChatFactory(Factory):
    class Meta:
        model = TelegramChat

    id = Sequence(lambda n: n + 1)
    type = "private"
    username = Faker("user_name")


class TelegramMessageFactory(Factory):
    class Meta:
        model = TelegramMessage

    message_id = Sequence(lambda n: n + 100)
    text = "fake text"
    chat = SubFactory(TelegramChatFactory)


class UserFactory(Factory):
    class Meta:
        model = User

    id = uuid.uuid4()
    full_name = Faker("name")
    avatar_url = Faker("image_url")
    billing_address = None
    payment_method = None
    timezone_code = "UTC"


class DeliveryChannelFactory(Factory):
    class Meta:
        model = DeliveryChannel

    id = uuid.uuid4()
    user_id = uuid.uuid4()
    channel_type = DeliveryChannelEnum.TELEGRAM
    address = Faker("email")
    is_active = True
    created_at = Faker("date_time_this_decade", tzinfo=timezone.utc)
    updated_at = Faker("date_time_this_decade", tzinfo=timezone.utc)
