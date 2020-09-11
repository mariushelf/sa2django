from sa2django import SA2DModel, register_table
from tests.sa_models import SAChild, SAParent

register_table("child", "DMChild")


class DMParent(SA2DModel):
    class Meta:
        sa_model = SAParent


class DMChild(SA2DModel):
    class Meta:
        sa_model = SAChild
