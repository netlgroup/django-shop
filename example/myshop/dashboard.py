# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from rest_framework import serializers
from rest_framework.compat import set_many
from rest_framework.exceptions import ValidationError
from rest_framework.utils import model_meta

from shop import app_settings
from shop.dashboard import viewsets
from shop.dashboard import routers
from shop.dashboard.serializers import (ProductDetailSerializer, InlineListSerializer)

from myshop.models import SmartCard, SmartPhoneModel, SmartPhoneVariant


class SmartCardSerializer(ProductDetailSerializer):
    form_name = 'smartcard_form'
    scope_prefix = 'smartcard'

    class Meta:
        model = SmartCard
        fields = '__all__'


class SmartPhoneVariantSerializer(serializers.ModelSerializer):
    class Meta:
        model = SmartPhoneVariant
        list_serializer_class = InlineListSerializer
        fields = '__all__'
        extra_kwargs = {
            'id': {
                'read_only': False,
                'required': False,
                'style': {'hidden': True},
            },
            'product': {
                'required': False,
                'style': {'hidden': True},
            },
            'product_code': {
                'validators': [],
            },
            'unit_price': {
                'coerce_to_string': False,
            }
        }

    def validate_product(self, data):
        if data.pk != self.parent.parent.instance.pk:
            raise ValidationError("Product ID mismatch")
        return data


class SmartPhoneSerializer(serializers.ModelSerializer):
    variants = SmartPhoneVariantSerializer(many=True)

    class Meta:
        model = SmartPhoneModel
        fields = '__all__'
        extra_kwargs = {
            'width': {
                'coerce_to_string': False,
            },
            'height': {
                'coerce_to_string': False,
            },
            'weight': {
                'coerce_to_string': False,
            },
            'screen_size': {
                'coerce_to_string': False,
            },
        }

    def validate(self, data):
        data = super(SmartPhoneSerializer, self).validate(data)
        return data

    def is_valid(self, raise_exception=False):
        return super(SmartPhoneSerializer, self).is_valid(raise_exception)

    def create(self, validated_data):
        smart_phone_variants = validated_data.pop('variants')
        instance = SmartPhoneModel.objects.create(**validated_data)
        for variant in smart_phone_variants:
            SmartPhoneVariant.objects.create(product=instance, **variant)
        return instance

    def update(self, instance, validated_data):
        info = model_meta.get_field_info(instance)
        for attr, value in validated_data.items():
            if isinstance(self.fields[attr], serializers.ListSerializer):
                setattr(instance, attr, self.fields[attr].update(instance, value))
            elif attr in info.relations and info.relations[attr].to_many:
                set_many(instance, attr, value)
            else:
                setattr(instance, attr, value)

        instance.save()
        return instance


class ProductsDashboard(viewsets.DashboardViewSet):
    list_display = ['media', 'product_name', 'caption', 'price']
    list_display_links = ['product_name']
    list_serializer_class = app_settings.PRODUCT_SUMMARY_SERIALIZER
    detail_serializer_classes = {
        'myshop.smartcard': SmartCardSerializer,
        'myshop.smartphonemodel': SmartPhoneSerializer,
    }


router = routers.DashboardRouter()
router.register('products', ProductsDashboard)
