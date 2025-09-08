# apps/shop/tests.py
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from .models import Tag, Product, ProductOption


class BaseProductAPITestCase(APITestCase):
    """상품 API 테스트의 공통 기능"""

    def setUp(self):
        """공통 테스트 데이터 설정"""
        # 기본 태그들 생성
        self.existing_tag = Tag.objects.create(name="ExistTag")
        self.another_tag = Tag.objects.create(name="AnotherExistTag")

        # URL 설정
        self.list_url = reverse("products")

    def get_detail_url(self, pk):
        """상세 URL 헬퍼 메서드"""
        return reverse("products-detail", kwargs={"pk": pk})

    def create_product_with_relations(
        self, name="TestProduct", options_data=None, tags=None
    ):
        """관계가 포함된 상품 생성 헬퍼"""
        product = Product.objects.create(name=name)

        if tags:
            product.tag_set.set(tags)

        if options_data:
            for option_data in options_data:
                ProductOption.objects.create(product=product, **option_data)

        return product

    def assert_response_format(self, response_data, is_list=False):
        """응답 형식 검증 헬퍼"""
        if is_list:
            self.assertIsInstance(response_data, list)
            products = response_data
        else:
            products = [response_data]

        for product in products:
            # 필수 필드 검증
            self.assertIn("pk", product)
            self.assertIn("name", product)
            self.assertIn("option_set", product)
            self.assertIn("tag_set", product)

            # 옵션 형식 검증
            for option in product["option_set"]:
                self.assertIn("pk", option)
                self.assertIn("name", option)
                self.assertIn("price", option)
                self.assertIsInstance(option["pk"], int)
                self.assertIsInstance(option["name"], str)
                self.assertIsInstance(option["price"], int)

            # 태그 형식 검증
            for tag in product["tag_set"]:
                self.assertIn("pk", tag)
                self.assertIn("name", tag)
                self.assertIsInstance(tag["pk"], int)
                self.assertIsInstance(tag["name"], str)


class ProductCreateAPITestCase(BaseProductAPITestCase):
    """상품 생성 API 테스트"""

    def test_create_product_with_new_options_and_mixed_tags(self):
        """새로운 옵션들과 기존/신규 태그가 혼합된 상품 생성 테스트"""
        request_data = {
            "name": "TestProduct",
            "option_set": [
                {"name": "TestOption1", "price": 1000},
                {"name": "TestOption2", "price": 500},
                {"name": "TestOption3", "price": 0},
            ],
            "tag_set": [
                {"pk": self.existing_tag.pk, "name": "ExistTag"},
                {"name": "NewTag"},
            ],
        }

        response = self.client.post(self.list_url, request_data, format="json")

        # 기본 검증
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response_data = response.json()

        # 응답 형식 검증
        self.assert_response_format(response_data)

        # 데이터 내용 검증
        self.assertEqual(response_data["name"], "TestProduct")
        self.assertEqual(len(response_data["option_set"]), 3)
        self.assertEqual(len(response_data["tag_set"]), 2)

        # 옵션명 검증
        option_names = {opt["name"] for opt in response_data["option_set"]}
        expected_options = {"TestOption1", "TestOption2", "TestOption3"}
        self.assertEqual(option_names, expected_options)

        # 태그명 검증
        tag_names = {tag["name"] for tag in response_data["tag_set"]}
        expected_tags = {"ExistTag", "NewTag"}
        self.assertEqual(tag_names, expected_tags)

        # DB 검증
        created_product = Product.objects.get(pk=response_data["pk"])
        self.assertEqual(created_product.name, "TestProduct")
        self.assertEqual(created_product.option_set.count(), 3)
        self.assertEqual(created_product.tag_set.count(), 2)
        self.assertTrue(Tag.objects.filter(name="NewTag").exists())
        self.assertEqual(Tag.objects.count(), 3)  # existing_tag + another_tag + NewTag

    def test_create_product_with_only_existing_tags(self):
        """기존 태그만 사용하는 상품 생성 테스트"""
        initial_tag_count = Tag.objects.count()

        request_data = {
            "name": "ProductWithExistingTags",
            "option_set": [{"name": "Option1", "price": 2000}],
            "tag_set": [
                {"pk": self.existing_tag.pk, "name": "ExistTag"},
                {"pk": self.another_tag.pk, "name": "AnotherExistTag"},
            ],
        }

        response = self.client.post(self.list_url, request_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # 새로운 태그가 생성되지 않았는지 확인
        self.assertEqual(Tag.objects.count(), initial_tag_count)

    def test_create_product_with_only_new_tags(self):
        """새로운 태그만 사용하는 상품 생성 테스트"""
        initial_tag_count = Tag.objects.count()

        request_data = {
            "name": "ProductWithNewTags",
            "option_set": [{"name": "Option1", "price": 1500}],
            "tag_set": [{"name": "NewTag1"}, {"name": "NewTag2"}],
        }

        response = self.client.post(self.list_url, request_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Tag.objects.count(), initial_tag_count + 2)
        self.assertTrue(Tag.objects.filter(name="NewTag1").exists())
        self.assertTrue(Tag.objects.filter(name="NewTag2").exists())

    def test_create_product_without_options(self):
        """옵션 없이 상품 생성 테스트"""
        request_data = {
            "name": "ProductWithoutOptions",
            "option_set": [],
            "tag_set": [{"name": "TagOnly"}],
        }

        response = self.client.post(self.list_url, request_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        created_product = Product.objects.get(pk=response.json()["pk"])
        self.assertEqual(created_product.option_set.count(), 0)
        self.assertEqual(created_product.tag_set.count(), 1)

    def test_create_product_without_tags(self):
        """태그 없이 상품 생성 테스트"""
        request_data = {
            "name": "ProductWithoutTags",
            "option_set": [{"name": "OnlyOption", "price": 3000}],
            "tag_set": [],
        }

        response = self.client.post(self.list_url, request_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        created_product = Product.objects.get(pk=response.json()["pk"])
        self.assertEqual(created_product.option_set.count(), 1)
        self.assertEqual(created_product.tag_set.count(), 0)

    def test_create_product_with_invalid_existing_tag_pk(self):
        """존재하지 않는 태그 pk로 요청 시 오류 처리 테스트"""
        request_data = {
            "name": "InvalidTagProduct",
            "option_set": [{"name": "Option1", "price": 1000}],
            "tag_set": [{"pk": 99999, "name": "NonExistentTag"}],
        }

        response = self.client.post(self.list_url, request_data, format="json")

        self.assertIn(
            response.status_code,
            [status.HTTP_400_BAD_REQUEST, status.HTTP_404_NOT_FOUND],
        )

    def test_create_product_with_empty_option_name(self):
        """빈 옵션명으로 요청 시 오류 처리 테스트"""
        request_data = {
            "name": "InvalidOptionProduct",
            "option_set": [{"name": "", "price": 1000}],
            "tag_set": [],
        }

        response = self.client.post(self.list_url, request_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_product_with_negative_price(self):
        """음수 가격으로 요청 시 처리 테스트"""
        request_data = {
            "name": "NegativePriceProduct",
            "option_set": [{"name": "NegativeOption", "price": -1000}],
            "tag_set": [],
        }

        response = self.client.post(self.list_url, request_data, format="json")

        # 비즈니스 로직에 따라 허용 여부가 결정됨
        self.assertIn(
            response.status_code, [status.HTTP_201_CREATED, status.HTTP_400_BAD_REQUEST]
        )

    def test_create_product_response_format(self):
        """응답 데이터 형식 검증"""
        request_data = {
            "name": "FormatTestProduct",
            "option_set": [{"name": "FormatOption", "price": 1000}],
            "tag_set": [{"name": "FormatTag"}],
        }

        response = self.client.post(self.list_url, request_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assert_response_format(response.json())


class ProductUpdateAPITestCase(BaseProductAPITestCase):
    """상품 수정 API 테스트"""

    def setUp(self):
        """테스트 데이터 설정"""
        super().setUp()

        # 테스트용 상품과 관계 데이터 생성
        self.new_tag = Tag.objects.create(name="NewTag")
        self.product = self.create_product_with_relations(
            name="TestProduct",
            options_data=[
                {"name": "TestOption1", "price": 1000},
                {"name": "TestOption2", "price": 500},
                {"name": "TestOption3", "price": 0},
            ],
            tags=[self.existing_tag, self.new_tag],
        )

        # 개별 옵션 참조 저장 (테스트에서 사용)
        self.options = list(self.product.option_set.all())
        self.option1, self.option2, self.option3 = self.options

    def test_update_product_with_complex_changes(self):
        """복잡한 중첩 수정 테스트"""
        url = self.get_detail_url(self.product.pk)
        request_data = {
            "name": "TestProduct",
            "option_set": [
                {"pk": self.option1.pk, "name": "TestOption1", "price": 1000},
                {"pk": self.option2.pk, "name": "Edit TestOption2", "price": 1500},
                {"name": "Edit New Option", "price": 300},
            ],
            "tag_set": [
                {"pk": self.existing_tag.pk, "name": "ExistTag"},
                {"pk": self.new_tag.pk, "name": "NewTag"},
                {"name": "Edit New Tag"},
            ],
        }

        response = self.client.patch(url, request_data, format="json")

        # 기본 검증
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()

        # 응답 형식 검증
        self.assert_response_format(response_data)

        # 데이터 변경 검증
        self.assertEqual(len(response_data["option_set"]), 3)
        self.assertEqual(len(response_data["tag_set"]), 3)

        # 옵션 변경 확인
        option_names = {opt["name"] for opt in response_data["option_set"]}
        expected_options = {"TestOption1", "Edit TestOption2", "Edit New Option"}
        self.assertEqual(option_names, expected_options)

        # 가격 변경 확인
        edited_option = next(
            opt
            for opt in response_data["option_set"]
            if opt["name"] == "Edit TestOption2"
        )
        self.assertEqual(edited_option["price"], 1500)

        # 태그 변경 확인
        tag_names = {tag["name"] for tag in response_data["tag_set"]}
        expected_tags = {"ExistTag", "NewTag", "Edit New Tag"}
        self.assertEqual(tag_names, expected_tags)

        # DB 검증
        updated_product = Product.objects.get(pk=self.product.pk)
        self.assertEqual(updated_product.option_set.count(), 3)
        self.assertEqual(updated_product.tag_set.count(), 3)
        self.assertFalse(ProductOption.objects.filter(pk=self.option3.pk).exists())
        self.assertTrue(Tag.objects.filter(name="Edit New Tag").exists())

    def test_update_product_remove_all_options(self):
        """모든 옵션 제거 테스트"""
        url = self.get_detail_url(self.product.pk)
        request_data = {
            "name": "TestProduct",
            "option_set": [],
            "tag_set": [{"pk": self.existing_tag.pk, "name": "ExistTag"}],
        }

        response = self.client.patch(url, request_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        updated_product = Product.objects.get(pk=self.product.pk)
        self.assertEqual(updated_product.option_set.count(), 0)

    def test_update_product_remove_all_tags(self):
        """모든 태그 제거 테스트"""
        url = self.get_detail_url(self.product.pk)
        request_data = {
            "name": "TestProduct",
            "option_set": [
                {"pk": self.option1.pk, "name": "TestOption1", "price": 1000}
            ],
            "tag_set": [],
        }

        response = self.client.patch(url, request_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        updated_product = Product.objects.get(pk=self.product.pk)
        self.assertEqual(updated_product.tag_set.count(), 0)

    def test_update_nonexistent_product(self):
        """존재하지 않는 상품 수정 시도"""
        url = self.get_detail_url(99999)
        request_data = {"name": "Updated Name"}

        response = self.client.patch(url, request_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_partial_update_name_only(self):
        """상품명만 수정"""
        url = self.get_detail_url(self.product.pk)
        request_data = {"name": "Updated Product Name"}

        response = self.client.patch(url, request_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
        self.assertEqual(response_data["name"], "Updated Product Name")
        self.assertEqual(len(response_data["option_set"]), 3)
        self.assertEqual(len(response_data["tag_set"]), 2)


class ProductListAPITestCase(BaseProductAPITestCase):
    """상품 목록 조회 API 테스트"""

    def setUp(self):
        """테스트 데이터 설정"""
        super().setUp()

        # 다양한 상품들 생성
        self.test_tag = Tag.objects.create(name="TestTag")

        self.product1 = self.create_product_with_relations(
            name="TestProduct",
            options_data=[
                {"name": "TestOption1", "price": 1000},
                {"name": "TestOption2", "price": 500},
                {"name": "TestOption3", "price": 0},
            ],
            tags=[self.existing_tag, self.another_tag],
        )

        self.product2 = self.create_product_with_relations(name="TestProduct2")

        self.product3 = self.create_product_with_relations(
            name="TestProduct3",
            options_data=[{"name": "Option3-1", "price": 2000}],
            tags=[self.test_tag],
        )

    def test_list_all_products(self):
        """전체 상품 목록 조회 테스트"""
        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()

        # 기본 검증
        self.assert_response_format(response_data, is_list=True)
        self.assertEqual(len(response_data), 3)

        # 각 상품별 세부 검증
        products_by_name = {p["name"]: p for p in response_data}

        # 첫 번째 상품 검증
        product1_data = products_by_name["TestProduct"]
        self.assertEqual(product1_data["pk"], self.product1.pk)
        self.assertEqual(len(product1_data["option_set"]), 3)
        self.assertEqual(len(product1_data["tag_set"]), 2)

        # 두 번째 상품 검증 (빈 옵션/태그)
        product2_data = products_by_name["TestProduct2"]
        self.assertEqual(len(product2_data["option_set"]), 0)
        self.assertEqual(len(product2_data["tag_set"]), 0)

    def test_list_empty_products(self):
        """상품이 없을 때 목록 조회 테스트"""
        Product.objects.all().delete()

        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
        self.assertEqual(len(response_data), 0)


class ProductRetrieveAPITestCase(BaseProductAPITestCase):
    """상품 상세 조회 API 테스트"""

    def setUp(self):
        """테스트 데이터 설정"""
        super().setUp()

        self.new_tag = Tag.objects.create(name="NewTag")
        self.product = self.create_product_with_relations(
            name="TestProduct",
            options_data=[
                {"name": "TestOption1", "price": 1000},
                {"name": "TestOption2", "price": 500},
                {"name": "TestOption3", "price": 0},
            ],
            tags=[self.existing_tag, self.new_tag],
        )

    def test_retrieve_existing_product(self):
        """존재하는 상품 상세 조회 테스트"""
        url = self.get_detail_url(self.product.pk)
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()

        # 응답 형식 검증
        self.assert_response_format(response_data)

        # 데이터 내용 검증
        self.assertEqual(response_data["pk"], self.product.pk)
        self.assertEqual(response_data["name"], "TestProduct")
        self.assertEqual(len(response_data["option_set"]), 3)
        self.assertEqual(len(response_data["tag_set"]), 2)

        # 특정 데이터 확인
        option_names = {opt["name"] for opt in response_data["option_set"]}
        expected_options = {"TestOption1", "TestOption2", "TestOption3"}
        self.assertEqual(option_names, expected_options)

        tag_names = {tag["name"] for tag in response_data["tag_set"]}
        expected_tags = {"ExistTag", "NewTag"}
        self.assertEqual(tag_names, expected_tags)

    def test_retrieve_nonexistent_product(self):
        """존재하지 않는 상품 조회 테스트"""
        url = self.get_detail_url(99999)
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_retrieve_product_without_options_and_tags(self):
        """옵션과 태그가 없는 상품 조회 테스트"""
        empty_product = Product.objects.create(name="EmptyProduct")
        url = self.get_detail_url(empty_product.pk)

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
        self.assertEqual(response_data["name"], "EmptyProduct")
        self.assertEqual(len(response_data["option_set"]), 0)
        self.assertEqual(len(response_data["tag_set"]), 0)

    def test_retrieve_with_query_optimization(self):
        """N+1 쿼리 최적화 확인"""
        url = self.get_detail_url(self.product.pk)

        with self.assertNumQueries(3):  # Product + Options + Tags
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
