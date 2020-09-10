from sa2django import SA2DModel


class Parent(SA2DModel):
    class Meta:
        # sa_model = None  # TODO
        managed = False
        db_table = "parent"
