# Create your views here.
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import viewsets

from .models import Product
from .serializers import ProductSerializer


class ProductViewSet(viewsets.ModelViewSet):
    """
    상품 관리 API

    상품의 CRUD 기능을 제공합니다.
    - 상품 목록 조회
    - 상품 상세 조회
    - 상품 생성 (옵션 및 태그 포함)
    - 상품 수정 (옵션 및 태그 포함)
    - 상품 삭제
    """

    serializer_class = ProductSerializer

    def get_queryset(self):
        return Product.objects.prefetch_related("option_set", "tag_set")

    @swagger_auto_schema(
        operation_summary="상품 목록 조회",
        operation_description="전체 상품 목록을 조회합니다. 각 상품에는 연관된 옵션과 태그 정보가 포함됩니다.",
        responses={
            200: openapi.Response(
                description="상품 목록 조회 성공", schema=ProductSerializer(many=True)
            )
        },
        tags=["상품"],
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="상품 생성",
        operation_description="""
        새로운 상품을 생성합니다.

        **태그 처리 규칙:**
        - pk가 있는 태그: 기존 태그와 연결
        - pk가 없는 태그: 새로운 태그 생성 후 연결

        **옵션 처리:**
        - 모든 옵션은 새로 생성됩니다.
        """,
        request_body=ProductSerializer,
        responses={
            201: openapi.Response(
                description="상품 생성 성공", schema=ProductSerializer()
            ),
            400: openapi.Response(
                description="잘못된 요청 데이터",
                examples={
                    "application/json": {
                        "option_set": ["옵션명은 필수입니다."],
                        "tag_set": ["태그 ID 999가 존재하지 않습니다."],
                    }
                },
            ),
        },
        tags=["상품"],
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="상품 상세 조회",
        operation_description="특정 상품의 상세 정보를 조회합니다.",
        responses={
            200: openapi.Response(
                description="상품 조회 성공", schema=ProductSerializer()
            ),
            404: openapi.Response(description="상품을 찾을 수 없음"),
        },
        tags=["상품"],
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="상품 수정",
        operation_description="""
        기존 상품을 수정합니다.

        **옵션 수정 규칙:**
        - pk가 있는 옵션: 기존 옵션 수정
        - pk가 없는 옵션: 새 옵션 생성
        - 요청에 없는 기존 옵션: 삭제

        **태그 수정 규칙:**
        - pk가 있는 태그: 기존 태그와 연결
        - pk가 없는 태그: 새 태그 생성 후 연결
        """,
        request_body=ProductSerializer,
        responses={
            200: openapi.Response(
                description="상품 수정 성공", schema=ProductSerializer()
            ),
            400: openapi.Response(description="잘못된 요청 데이터"),
            404: openapi.Response(description="상품을 찾을 수 없음"),
        },
        tags=["상품"],
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="상품 삭제",
        operation_description="특정 상품을 삭제합니다. 연관된 옵션도 함께 삭제됩니다.",
        responses={
            204: openapi.Response(description="상품 삭제 성공"),
            404: openapi.Response(description="상품을 찾을 수 없음"),
        },
        tags=["상품"],
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)
