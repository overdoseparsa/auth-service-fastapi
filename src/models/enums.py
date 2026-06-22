import enum


class UserRoleEnum(str, enum.Enum):
    ADMIN = "admin"
    USER = "user"


class OrderStatusEnum(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    SENT = "sent"
    DELIVERED = "delivered"
    CANCELED = "canceled"


class PaymentStatusEnum(str, enum.Enum):
    UNPAID = "unpaid"
    PAID = "paid"
    REFUNDED = "refunded"


class OrderLogAction(str, enum.Enum):
    ORDER_CREATED = "order_created"
    STATUS_CHANGED = "status_changed"
    PAYMENT_UPDATED = "payment_updated"
    ORDER_CANCELED = "order_canceled"
    ORDER_REFUNDED = "order_refunded"
