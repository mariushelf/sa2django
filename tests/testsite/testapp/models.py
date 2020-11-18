from sa2django.core import generate_sa2d_models, inject_models
from tests.sa_models import Base

_models = generate_sa2d_models(Base, __name__)
inject_models(_models, globals())
