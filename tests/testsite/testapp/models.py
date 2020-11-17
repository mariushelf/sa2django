from sa2django import SA2DModel, register_table
from tests.sa_models import SACar, SACarParentAssoc, SAChild, SAParent

register_table("child", "DMChild")
register_table("car", "DMCar")
register_table("cartoparent", "DMCarParentAssoc")


class DMParent(SA2DModel):
    class Meta:
        sa_model = SAParent


class DMChild(SA2DModel):
    class Meta:
        sa_model = SAChild


class DMCar(SA2DModel):
    class Meta:
        sa_model = SACar


class DMCarParentAssoc(SA2DModel):
    class Meta:
        sa_model = SACarParentAssoc
