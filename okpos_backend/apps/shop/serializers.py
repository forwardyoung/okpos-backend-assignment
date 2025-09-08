from rest_framework import serializers
from drf_writable_nested import WritableNestedModelSerializer
from .models import Tag, ProductOption, Product


class TagSerializer(WritableNestedModelSerializer):
    class Meta:
        model = Tag
        fields = ['pk', 'name']
        read_only_fields = ['pk']


class ProductOptionSerializer(WritableNestedModelSerializer):
    class Meta:
        model = ProductOption
        fields = ['pk', 'name', 'price']
        read_only_fields = ['pk']

    def validate_name(self, value):
        """옵션명 유효성 검사"""
        if not value or not value.strip():
            raise serializers.ValidationError("옵션명은 필수입니다.")
        return value.strip()


class ProductSerializer(WritableNestedModelSerializer):
    option_set = ProductOptionSerializer(many=True, required=False)
    tag_set = TagSerializer(many=True, required=False)

    class Meta:
        model = Product
        fields = ['pk', 'name', 'option_set', 'tag_set']
        read_only_fields = ['pk']

    def create(self, validated_data):
        """상품 생성 - 태그 완전 수동 처리"""
        # 태그 데이터를 미리 제거 (WritableNestedModelSerializer가 처리하지 않도록)
        tags_data = validated_data.pop('tag_set', [])

        # 상품과 옵션만 자동 처리
        product = super().create(validated_data)

        # 태그 수동 처리
        self._process_tags(product, tags_data)

        return product

    def update(self, instance, validated_data):
        """상품 수정 - 태그 완전 수동 처리"""
        # 태그 데이터를 미리 제거
        tags_data = validated_data.pop('tag_set', None)

        # 상품과 옵션만 자동 처리
        product = super().update(instance, validated_data)

        # 태그 수동 처리 (None이 아닌 경우에만)
        if tags_data is not None:
            self._process_tags(product, tags_data)

        return product

    def _process_tags(self, product, tags_data):
        """태그 처리 헬퍼 메서드"""
        tag_instances = []
        processed_tag_names = set()

        for tag_data in tags_data:
            # 빈 데이터 체크
            if not tag_data or 'name' not in tag_data:
                continue

            tag_name = tag_data['name']

            # 중복 방지
            if tag_name in processed_tag_names:
                continue

            if 'pk' in tag_data and tag_data['pk']:
                # 기존 태그 연결
                try:
                    tag = Tag.objects.get(pk=tag_data['pk'])
                    tag_instances.append(tag)
                    processed_tag_names.add(tag_name)
                except Tag.DoesNotExist:
                    raise serializers.ValidationError(
                        {"tag_set": f"태그 ID {tag_data['pk']}가 존재하지 않습니다."}
                    )
            else:
                # 새 태그 생성 또는 기존 태그 재사용
                tag, created = Tag.objects.get_or_create(name=tag_name)
                tag_instances.append(tag)
                processed_tag_names.add(tag_name)

        # 태그 연결
        product.tag_set.set(tag_instances)