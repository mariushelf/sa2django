from sa2django import SA2DModel
from tests.sa_models import SAChild, SAParent


class DMParent(SA2DModel):
    class Meta:
        sa_model = SAParent


class DMChild(SA2DModel):
    class Meta:
        sa_model = SAChild
