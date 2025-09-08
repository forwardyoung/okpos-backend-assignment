from django.urls import path
from .views import ProductViewSet

urlpatterns = [
    path(
        "products/",
        ProductViewSet.as_view(
            {
                "get": "list",
                "post": "create",
            }
        ),
        name="products",
    ),
    path(
            "products/<int:pk>/",
        ProductViewSet.as_view(
            {
                "get": "retrieve",
                "patch": "partial_update",
                "delete": "destroy",
            }
        ),
        name="products-detail",
    ),
]